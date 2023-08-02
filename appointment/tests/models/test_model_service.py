from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from appointment.models import Service


class ServiceModelTestCase(TestCase):
    def setUp(self):
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=1, minutes=30), price=100)

    def test_service_creation(self):
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.duration, timedelta(hours=1, minutes=30))
        self.assertEqual(self.service.price, 100)

    def test_is_a_paid_service(self):
        self.assertTrue(self.service.is_a_paid_service())

    def test_get_service_name(self):
        self.assertEqual(self.service.get_name(), "Test Service")

    def test_get_service_description(self):
        self.assertEqual(self.service.get_description(), None)
        self.service.description = "Test Service - 1 hour - 100.0"
        self.assertEqual(self.service.get_description(), "Test Service - 1 hour - 100.0")

    def test_get_service_duration_day(self):
        self.service.duration = timedelta(days=1)
        self.assertEqual(self.service.get_duration(), '1 day')

    def test_get_service_duration_hour(self):
        self.service.duration = timedelta(hours=1)
        self.assertEqual(self.service.get_duration(), '1 hour')

    def test_get_service_duration_minute(self):
        self.service.duration = timedelta(minutes=30)
        self.assertEqual(self.service.get_duration(), '30 minutes')

    def test_get_service_duration_second(self):
        self.service.duration = timedelta(seconds=30)
        self.assertEqual(self.service.get_duration(), '30 seconds')

    def test_get_service_duration_hour_minute(self):
        self.service.duration = timedelta(hours=2, minutes=20)
        print(self.service.get_duration())
        self.assertEqual(self.service.get_duration(), '2 hours 20 minutes')

    def test_get_service_price(self):
        self.assertEqual(self.service.get_price(), 100)

    def test_get_service_price_display(self):
        self.assertEqual(self.service.get_price_text(), "100 USD")

    def test_get_service_price_display_cent(self):
        self.service.price = 100.50
        self.assertEqual(self.service.get_price_text(), "100.5 USD")

    def test_get_service_price_display_free(self):
        self.service.price = 0
        self.assertEqual(self.service.get_price_text(), "Free")

    def test_get_service_down_payment_none(self):
        self.assertEqual(self.service.get_down_payment(), 0)

    def test_get_service_down_payment(self):
        self.service.down_payment = 50
        self.assertEqual(self.service.get_down_payment(), 50)

    def test_get_service_currency(self):
        self.assertEqual(self.service.get_currency(), "USD")

    def test_get_service_image(self):
        pass
        # self.assertIsNone(self.service.get_image())
        # Add a sample image file and test the method
        # self.service.image = 'path/to/sample/image.jpg'
        # self.assertEqual(self.service.get_image(), 'path/to/sample/image.jpg')

    def test_get_service_image_url(self):
        pass
        # self.assertIsNone(self.service.get_image_url())
        # Add a sample image file and test the method
        # self.service.image = 'path/to/sample/image.jpg'
        # self.service.save()
        # self.assertEqual(self.service.get_image_url(), '/media/path/to/sample/image.jpg')

    def test_get_service_created_at(self):
        self.assertIsNotNone(self.service.get_created_at())

    def test_get_service_updated_at(self):
        self.assertIsNotNone(self.service.get_updated_at())

    def test_accepts_down_payment_false(self):
        self.assertFalse(self.service.accepts_down_payment())

    def test_accepts_down_payment_true(self):
        self.service.down_payment = 50
        self.assertTrue(self.service.accepts_down_payment())

    # Negative test cases
    def test_invalid_service_name(self):
        self.service.name = "A" * 101  # Exceeding the max_length
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_invalid_service_price_negative(self):
        self.service.price = -100
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_invalid_service_down_payment_negative(self):
        self.service.down_payment = -50
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_invalid_service_currency_length(self):
        self.service.currency = "US"  # Less than 3 characters
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_invalid_service_currency_length_exceed(self):
        self.service.currency = "USDD"  # More than 3 characters
        with self.assertRaises(ValidationError):
            self.service.full_clean()
