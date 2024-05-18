from datetime import time

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from appointment.models import Config


class ConfigCreationTestCase(TestCase):
    def setUp(self):
        self.config = Config.objects.create(slot_duration=30, lead_time=time(9, 0),
                                            finish_time=time(17, 0), appointment_buffer_time=2.0,
                                            website_name="Stargate Command")

    @override_settings(DEBUG=True)
    def tearDown(self):
        Config.objects.all().delete()
        cache.clear()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_default_attributes_on_creation(self):
        self.assertIsNotNone(self.config)
        self.assertEqual(self.config.slot_duration, 30)
        self.assertEqual(self.config.lead_time, time(9, 0))
        self.assertEqual(self.config.finish_time, time(17, 0))
        self.assertEqual(self.config.appointment_buffer_time, 2.0)
        self.assertEqual(self.config.website_name, "Stargate Command")
        self.assertIsNotNone(Config.get_instance())

    def test_multiple_config_creation(self):
        """Test that only one configuration can be created."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=20, lead_time=time(8, 0), finish_time=time(18, 0))

    def test_config_str_method(self):
        """Test that the string representation of a configuration is correct."""
        expected_str = f"Config {self.config.pk}: slot_duration=30, lead_time=09:00:00, finish_time=17:00:00"
        self.assertEqual(str(self.config), expected_str)


class ConfigUpdateTestCase(TestCase):
    def setUp(self):
        self.config = Config.objects.create(slot_duration=30, lead_time=time(9, 0),
                                            finish_time=time(17, 0), appointment_buffer_time=2.0,
                                            website_name="Stargate Command")

    @override_settings(DEBUG=True)
    def tearDown(self):
        Config.objects.all().delete()
        cache.clear()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_editing_existing_config(self):
        """Test that an existing configuration can be edited."""
        self.config.slot_duration = 41
        self.config.website_name = "Cheyeene Mountain Complex"
        self.config.save()

        updated_config = Config.objects.get(pk=self.config.pk)
        self.assertEqual(updated_config.website_name, "Cheyeene Mountain Complex")
        self.assertEqual(updated_config.slot_duration, 41)


class ConfigDeletionTestCase(TestCase):
    def setUp(self):
        self.config = Config.objects.create(slot_duration=30, lead_time=time(9, 0),
                                            finish_time=time(17, 0), appointment_buffer_time=2.0,
                                            website_name="Stargate Command")

    @override_settings(DEBUG=True)
    def tearDown(self):
        Config.objects.all().delete()
        cache.clear()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_cant_delete_config(self):
        """Test that a configuration cannot be deleted."""
        self.config.delete()
        self.assertIsNotNone(Config.objects.first())


class ConfigDurationValidationTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_invalid_slot_duration(self):
        """Test that a configuration cannot be created with a negative slot duration."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=-10, lead_time=time(9, 0), finish_time=time(17, 0))
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=0, lead_time=time(9, 0), finish_time=time(17, 0))


class ConfigTimeValidationTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_lead_time_greater_than_finish_time(self):
        # TODO: Think about business with night shifts, start time will be greater than finish time,
        #  but again, not sure client will use this app for night shifts
        """Test that lead time cannot be greater than finish time."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=30, lead_time=time(18, 0), finish_time=time(9, 0))

    def test_same_lead_and_finish_time(self):
        """Test that a configuration cannot be created with the same lead time and finish time."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=30, lead_time=time(9, 0), finish_time=time(9, 0))

    def test_negative_appointment_buffer_time(self):
        """Test that a configuration cannot be created with a negative appointment buffer time."""
        with self.assertRaises(ValidationError):
            Config.objects.create(slot_duration=30, lead_time=time(9, 0), finish_time=time(17, 0),
                                  appointment_buffer_time=-2.0)
