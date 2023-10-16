from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from appointment.models import Service


class ServiceModelTestCase(TestCase):
    def setUp(self):
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=1, minutes=30), price=100)

    def test_service_creation(self):
        """Test if a service can be created."""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.duration, timedelta(hours=1, minutes=30))
        self.assertEqual(self.service.price, 100)

    def test_is_a_paid_service(self):
        """Test if a service is a paid service."""
        self.assertTrue(self.service.is_a_paid_service())

    def test_service_name(self):
        """Test if a service can be created with a name."""
        self.assertEqual(self.service.name, "Test Service")

    def test_get_service_description(self):
        """Test if a service can be created with a description."""
        self.assertEqual(self.service.description, None)
        self.service.description = "Test Service - 1 hour - 100.0"
        self.assertEqual(self.service.description, "Test Service - 1 hour - 100.0")

    def test_get_service_duration_day(self):
        """Test that the get_duration method returns the correct string for a service with a duration of 1 day."""
        self.service.duration = timedelta(days=1)
        self.assertEqual(self.service.get_duration(), '1 day')

    def test_get_service_duration_hour(self):
        """Test that the get_duration method returns the correct string for a service with a duration of 1 hour."""
        self.service.duration = timedelta(hours=1)
        self.assertEqual(self.service.get_duration(), '1 hour')

    def test_get_service_duration_minute(self):
        """Test that the get_duration method returns the correct string for a service with a duration of 30 minutes."""
        self.service.duration = timedelta(minutes=30)
        self.assertEqual(self.service.get_duration(), '30 minutes')

    def test_get_service_duration_second(self):
        """Test that the get_duration method returns the correct string for a service with a duration of 30 seconds."""
        self.service.duration = timedelta(seconds=30)
        self.assertEqual(self.service.get_duration(), '30 seconds')

    def test_get_service_duration_hour_minute(self):
        """Test that the get_duration method returns the correct string for a service with
           a duration of 1 hour 30 minutes."""
        self.service.duration = timedelta(hours=2, minutes=20)
        self.assertEqual(self.service.get_duration(), '2 hours 20 minutes')

    def test_get_service_price(self):
        """Test that the get_price method returns the correct price for a service."""
        self.assertEqual(self.service.get_price(), 100)

    def test_get_service_price_display(self):
        """Test that the get_price_text method returns the correct string price including the currency symbol."""
        self.assertEqual(self.service.get_price_text(), "100$")

    def test_get_service_price_display_cent(self):
        """Test that the method returns the correct string price including the currency symbol for a service with a
           price of 100.50."""
        self.service.price = 100.50
        self.assertEqual(self.service.get_price_text(), "100.5$")

    def test_get_service_price_display_free(self):
        """Test that if the price is 0, the method returns the string 'Free'."""
        self.service.price = 0
        self.assertEqual(self.service.get_price_text(), "Free")

    def test_get_service_down_payment_none(self):
        """Test that the get_down_payment method returns 0 if the service has no down payment."""
        self.assertEqual(self.service.get_down_payment(), 0)

    def test_get_service_down_payment(self):
        """Test that the get_down_payment method returns the correct down payment for a service."""
        self.service.down_payment = 50
        self.assertEqual(self.service.get_down_payment(), 50)

    def test_service_currency(self):
        """Test if a service can be created with a currency."""
        self.assertEqual(self.service.currency, "USD")

    def test_get_service_image(self):
        """test_get_service_image's implementation not finished yet."""
        pass
        # self.assertIsNone(self.service.get_image())
        # Add a sample image file and test the method
        # self.service.image = 'path/to/sample/image.jpg'
        # self.assertEqual(self.service.get_image(), 'path/to/sample/image.jpg')

    def test_get_service_image_url(self):
        """test_get_service_image_url's implementation not finished yet."""
        pass
        # self.assertIsNone(self.service.get_image_url())
        # Add a sample image file and test the method
        # self.service.image = 'path/to/sample/image.jpg'
        # self.service.save()
        # self.assertEqual(self.service.get_image_url(), '/media/path/to/sample/image.jpg')

    def test_service_created_at(self):
        """Test if a service can be created with a created at date."""
        self.assertIsNotNone(self.service.created_at)

    def test_get_service_updated_at(self):
        """Test if a service can be created with an updated at date."""
        self.assertIsNotNone(self.service.updated_at)

    def test_accepts_down_payment_false(self):
        """Test that the accepts_down_payment method returns False if the service has no down payment."""
        self.assertFalse(self.service.accepts_down_payment())

    def test_accepts_down_payment_true(self):
        """Test that the accepts_down_payment method returns True if the service has a down payment."""
        self.service.down_payment = 50
        self.assertTrue(self.service.accepts_down_payment())

    # Negative test cases
    def test_invalid_service_name(self):
        """Test that the max_length of the name field is 100 characters."""
        self.service.name = "A" * 101  # Exceeding the max_length
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_invalid_service_price_negative(self):
        """A service cannot be created with a negative price."""
        self.service.price = -100
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_invalid_service_down_payment_negative(self):
        """A service cannot be created with a negative down payment."""
        self.service.down_payment = -50
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_invalid_service_currency_length(self):
        """A service cannot be created with a currency of less or more than three characters."""
        self.service.currency = "US"  # Less than 3 characters
        with self.assertRaises(ValidationError):
            self.service.full_clean()
        self.service.currency = "USDD"  # More than 3 characters
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_service_duration_zero(self):
        """A service cannot be created with a duration of zero."""
        with self.assertRaises(ValidationError):
            Service.objects.create(name="Test Service", duration=timedelta(), price=100)

    def test_price_and_down_payment_same(self):
        """A service can be created with a price and down payment of the same value."""
        service = Service.objects.create(name="Service Name", duration=timedelta(hours=1), price=100, down_payment=100)
        self.assertEqual(service.price, service.down_payment)

    def test_service_with_no_name(self):
        """A service cannot be created with no name."""
        with self.assertRaises(ValidationError):
            Service.objects.create(name="", duration=timedelta(hours=1), price=100)
