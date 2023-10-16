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
        """Test if a configuration can be created."""
        self.assertIsNotNone(self.config)
        self.assertEqual(self.config.slot_duration, 30)
        self.assertEqual(self.config.lead_time, time(9, 0))
        self.assertEqual(self.config.finish_time, time(17, 0))
        self.assertEqual(self.config.appointment_buffer_time, 2.0)
        self.assertEqual(self.config.website_name, "My Website")

    def test_config_str_method(self):
        """Test that the string representation of a configuration is correct."""
        expected_str = f"Config {self.config.pk}: slot_duration=30, lead_time=09:00:00, finish_time=17:00:00"
        self.assertEqual(str(self.config), expected_str)

    def test_invalid_slot_duration(self):
        """Test that a configuration cannot be created with a negative slot duration."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=-10, lead_time=time(9, 0), finish_time=time(17, 0))

    def test_multiple_config_creation(self):
        """Test that only one configuration can be created."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=20, lead_time=time(8, 0), finish_time=time(18, 0))

    def test_lead_time_greater_than_finish_time(self):
        """Test that lead time cannot be greater than finish time."""
        self.config.lead_time = time(18, 0)
        self.config.finish_time = time(9, 0)
        with self.assertRaises(ValidationError):
            self.config.full_clean()

    def test_editing_existing_config(self):
        """Test that an existing configuration can be edited."""
        self.config.slot_duration = 40
        self.config.save()

    def test_slot_duration_of_zero(self):
        """Test that a configuration cannot be created with a slot duration of zero."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=0, lead_time=time(9, 0), finish_time=time(17, 0))

    def test_same_lead_and_finish_time(self):
        """Test that a configuration cannot be created with the same lead time and finish time."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=30, lead_time=time(9, 0), finish_time=time(9, 0))

    def test_lead_time_one_minute_before_finish_time(self):
        """Test that a configuration cannot be created with a lead time one minute before the finish time."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=30, lead_time=time(8, 59), finish_time=time(9, 0))

    def test_negative_appointment_buffer_time(self):
        """Test that a configuration cannot be created with a negative appointment buffer time."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=30, lead_time=time(9, 0), finish_time=time(17, 0),
                                  appointment_buffer_time=-2.0)

    def test_update_website_name(self):
        """Simulate changing the website name in the configuration."""
        new_name = "Updated Website Name"
        self.config.website_name = new_name
        self.config.save()

        updated_config = Config.objects.get(pk=self.config.pk)
        self.assertEqual(updated_config.website_name, new_name)
