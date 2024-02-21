from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
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

    def test_service_with_invalid_duration(self):
        """Service should not be created with a negative or zero duration."""
        with self.assertRaises(ValidationError):
            Service.objects.create(name="Invalid Duration Service", duration=timedelta(seconds=-1), price=50)
        with self.assertRaises(ValidationError):
            Service.objects.create(name="Zero Duration Service", duration=timedelta(seconds=0), price=50)

    def test_service_with_empty_name(self):
        """Service should not be created with an empty name."""
        with self.assertRaises(ValidationError):
            Service.objects.create(name="", duration=timedelta(hours=1), price=50)

    def test_service_with_negative_price(self):
        """Service should not be created with a negative price."""
        with self.assertRaises(ValidationError):
            Service.objects.create(name="Negative Price Service", duration=timedelta(hours=1), price=-1)

    def test_service_with_negative_down_payment(self):
        """Service should not have a negative down payment."""
        with self.assertRaises(ValidationError):
            Service.objects.create(name="Service with Negative Down Payment", duration=timedelta(hours=1), price=50,
                                   down_payment=-1)

    def test_service_auto_generate_background_color(self):
        """Service should auto-generate a background color if none is provided."""
        service = Service.objects.create(name="Service with Auto Background", duration=timedelta(hours=1), price=50)
        self.assertIsNotNone(service.background_color)
        self.assertNotEqual(service.background_color, "")

    def test_reschedule_limit_and_allowance(self):
        """Service should correctly handle reschedule limits and rescheduling allowance."""
        service = Service.objects.create(name="Reschedulable Service", duration=timedelta(hours=1), price=50,
                                         reschedule_limit=3, allow_rescheduling=True)
        self.assertEqual(service.reschedule_limit, 3)
        self.assertTrue(service.allow_rescheduling)

    def test_get_service_image_url_no_image(self):
        """Service should handle cases where no image is provided gracefully."""
        service = Service.objects.create(name="Service without Image", duration=timedelta(hours=1), price=50)
        self.assertEqual(service.get_image_url(), "")

    def test_to_dict_method(self):
        """Test the to_dict method returns the correct dictionary representation of the Service instance."""
        service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=150,
                                         description="A test service")
        expected_dict = {
            "id": service.id,
            "name": "Test Service",
            "description": "A test service",
            "price": "150"
        }
        self.assertEqual(service.to_dict(), expected_dict)

    def test_get_down_payment_as_integer(self):
        """Test the get_down_payment method returns an integer if the down payment has no decimal part."""
        service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100, down_payment=50)
        self.assertEqual(service.get_down_payment(), 50)

    def test_get_down_payment_as_decimal(self):
        """Test the get_down_payment method returns the original decimal value if it has a decimal part."""
        service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100,
                                         down_payment=50.50)
        self.assertEqual(service.get_down_payment(), 50.50)

    def test_get_down_payment_text_free(self):
        """Test the get_down_payment_text method returns 'Free' if the down payment is 0."""
        service = Service.objects.create(name="Free Service", duration=timedelta(hours=1), price=100, down_payment=0)
        self.assertEqual(service.get_down_payment_text(), "Free")

    def test_get_down_payment_text_with_value(self):
        """Test the get_down_payment_text method returns the down payment amount followed by the currency icon."""
        service = Service.objects.create(name="Paid Service", duration=timedelta(hours=1), price=100, down_payment=25)
        # Assuming get_currency_icon method returns "$" for USD
        expected_text = "25$"
        self.assertEqual(service.get_down_payment_text(), expected_text)

    def test_get_down_payment_text_with_decimal(self):
        """Test the get_down_payment_text method for a service with a decimal down payment."""
        service = Service.objects.create(name="Service with Decimal Down Payment", duration=timedelta(hours=1),
                                         price=100, down_payment=25.75)
        # Assuming get_currency_icon method returns "$" for USD
        expected_text = "25.75$"
        self.assertEqual(service.get_down_payment_text(), expected_text)

    def test_str_method(self):
        """Test the string representation of the Service model."""
        service_name = "Test Service"
        service = Service.objects.create(name=service_name, duration=timedelta(hours=1), price=100)
        self.assertEqual(str(service), service_name)

    def test_get_service_image_url_with_image(self):
        """Service should return the correct URL for the image if provided."""
        # Create an image and attach it to the service
        image_path = settings.BASE_DIR / 'appointment/static/img/texture.webp'  # Adjust the path as necessary
        image = SimpleUploadedFile(name='test_image.png', content=open(image_path, 'rb').read(),
                                   content_type='image/png')
        service = Service.objects.create(name="Service with Image", duration=timedelta(hours=1), price=50, image=image)

        # Assuming you have MEDIA_URL set in your settings for development like '/media/'
        expected_url = f"{settings.MEDIA_URL}{service.image}"
        self.assertTrue(service.get_image_url().endswith(expected_url))
