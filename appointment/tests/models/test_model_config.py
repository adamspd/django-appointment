from datetime import time

from django.core.exceptions import ValidationError
from django.test import TestCase

from appointment.models import Config


class ConfigModelTestCase(TestCase):
    def setUp(self):
        self.config = Config.objects.create(slot_duration=30, lead_time=time(9, 0),
                                            finish_time=time(17, 0), appointment_buffer_time=2.0,
                                            website_name="My Website")

    def test_config_creation(self):
        self.assertIsNotNone(self.config)
        self.assertEqual(self.config.slot_duration, 30)
        self.assertEqual(self.config.lead_time, time(9, 0))
        self.assertEqual(self.config.finish_time, time(17, 0))
        self.assertEqual(self.config.appointment_buffer_time, 2.0)
        self.assertEqual(self.config.website_name, "My Website")

    def test_config_str_method(self):
        expected_str = f"Config {self.config.pk}: slot_duration=30, lead_time=09:00:00, finish_time=17:00:00"
        self.assertEqual(str(self.config), expected_str)

    def test_invalid_slot_duration(self):
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=-10, lead_time=time(9, 0), finish_time=time(17, 0))

    def test_multiple_config_creation(self):
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=20, lead_time=time(8, 0), finish_time=time(18, 0))

    def test_lead_time_greater_than_finish_time(self):
        self.config.lead_time = time(18, 0)
        self.config.finish_time = time(9, 0)
        with self.assertRaises(ValidationError):
            self.config.full_clean()

    def test_editing_existing_config(self):
        # Editing existing config should not raise an error
        self.config.slot_duration = 40
        self.config.save()  # This should not raise an error
