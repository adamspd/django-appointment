from copy import deepcopy
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from appointment.models import Service
from appointment.tests.base.base_test import BaseTest


class ServiceCreationAndBasicAttributesTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_service_creation(self):
        self.assertIsNotNone(self.service)

    def test_basic_attributes_verification(self):
        self.assertEqual(self.service.name, "Stargate Activation")
        self.assertEqual(self.service.description, "Activate the Stargate")
        self.assertEqual(self.service.duration, timedelta(hours=1))

    def test_timestamps_on_creation(self):
        """Newly created services should have created_at and updated_at values."""
        self.assertIsNotNone(self.service.created_at)
        self.assertIsNotNone(self.service.updated_at)


class ServicePriceTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_service_price_verification(self):
        self.assertEqual(self.service.price, 100000)
        self.assertEqual(self.service.get_price(), 100000)

    def test_paid_service_verification(self):
        self.assertTrue(self.service.is_a_paid_service())

    def check_price(self, price, expected_string):
        service = deepcopy(self.service)
        service.price = price
        self.assertEqual(service.get_price_text(), expected_string)

    def test_dynamic_price_representation(self):
        """Test that the get_price method returns the correct string for a service with a price of 100, 1000, etc."""
        test_cases = [
            (100, '100$'),
            (100.50, '100.5$'),
            (49.99, '49.99$'),
            (0, 'Free')
        ]
        for price, expected in test_cases:
            self.check_price(price, expected)


class ServiceDurationTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_service_duration_verification(self):
        """Test the duration of the service."""
        self.assertEqual(self.service.duration, self.service1.duration)

    def check_duration(self, duration, expected_string):
        service = deepcopy(self.service)
        service.duration = duration
        self.assertEqual(service.get_duration(), expected_string)

    def test_dynamic_duration_representation(self):
        """Test that the get_duration method returns the correct string for a service with a duration of 30 seconds,
        30 minutes, etc."""
        test_cases = [
            (timedelta(seconds=30), '30 seconds'),
            (timedelta(minutes=30), '30 minutes'),
            (timedelta(hours=1), '1 hour'),
            (timedelta(hours=2, minutes=30), '2 hours 30 minutes'),
            (timedelta(days=1), '1 day'),
        ]
        for duration, expected in test_cases:
            self.check_duration(duration, expected)


class ServiceDownPaymentTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_down_payment_value(self):
        """By default, down payment value is 0"""
        self.assertEqual(self.service.down_payment, 0)
        self.assertEqual(self.service.get_down_payment(), 0)

        self.assertEqual(self.service.get_down_payment_text(), "Free")

        # Change the down payment value to 69.99
        s = deepcopy(self.service)
        s.down_payment = 69.99
        self.assertEqual(s.get_down_payment(), 69.99)

        self.assertEqual(s.get_down_payment_text(), "69.99$")

    def test_accepts_down_payment(self):
        """By default, down payment is not accepted."""
        self.assertFalse(self.service.accepts_down_payment())

        # Change the accepts_down_payment value to True
        s = deepcopy(self.service)
        s.down_payment = 69.99
        self.assertTrue(s.accepts_down_payment())

    def test_equal_price_and_down_payment_scenario(self):
        """A service can be created with a price and down payment of the same value.
        This is useful when the service requires full payment upfront.
        """
        service = Service.objects.create(
            name="Naquadah Generator Maintenance", duration=timedelta(hours=1), price=100, down_payment=100)
        self.assertEqual(service.price, service.down_payment)


class ServiceRepresentationAndMiscTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_string_representation_of_service(self):
        """Test the string representation of the Service model."""
        service_name = "Test Service"
        service = Service.objects.create(name=service_name, duration=timedelta(hours=1), price=100)
        self.assertEqual(str(service), service_name)

    def test_image_url_with_attached_image(self):
        """Service should return the correct URL for the image if provided."""
        # Create an image and attach it to the service
        image_path = settings.BASE_DIR / 'appointment/static/img/texture.webp'  # Adjust the path as necessary
        image = SimpleUploadedFile(name='test_image.png', content=open(image_path, 'rb').read(),
                                   content_type='image/png')
        service = Service.objects.create(name="Service with Image", duration=timedelta(hours=1), price=50, image=image)

        # Assuming you have MEDIA_URL set in your settings for development like '/media/'
        expected_url = f"{settings.MEDIA_URL}{service.image}"
        self.assertTrue(service.get_image_url().endswith(expected_url))

    def test_image_url_without_attached_image(self):
        """Service should handle cases where no image is provided gracefully."""
        service = Service.objects.create(name="Gate Travel Coordination", duration=timedelta(hours=1), price=50)
        self.assertEqual(service.get_image_url(), "")

    def test_auto_generation_of_background_color(self):
        """Service should auto-generate a background color if none is provided."""
        service = Service.objects.create(name="Wormhole Stability Analysis", duration=timedelta(hours=1), price=50)
        self.assertIsNotNone(service.background_color)
        self.assertNotEqual(service.background_color, "")

    def test_service_to_dict_representation(self):
        """Test the to_dict method returns the correct dictionary representation of the Service instance."""
        service = Service.objects.create(name="Off-world Tactical Training", duration=timedelta(hours=1), price=150,
                                         description="Train for off-world missions")
        expected_dict = {
            "id": service.id,
            "name": "Off-world Tactical Training",
            "description": "Train for off-world missions",
            "price": "150"
        }
        self.assertEqual(service.to_dict(), expected_dict)

    def test_reschedule_features(self):
        """Service should correctly handle reschedule limits and rescheduling allowance."""
        service = Service.objects.create(name="Goa'uld Artifact Decryption", duration=timedelta(hours=1), price=50,
                                         reschedule_limit=3, allow_rescheduling=True)
        self.assertEqual(service.reschedule_limit, 3)
        self.assertTrue(service.allow_rescheduling)

    def test_default_currency_setting(self):
        """The Default currency is USD."""
        self.assertEqual(self.service.currency, 'USD')

        # Change the currency to EUR
        s = deepcopy(self.service)
        s.currency = 'EUR'
        self.assertEqual(s.currency, 'EUR')


class ServiceModelNegativeTestCase(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_exceeding_service_name_length(self):
        """Test that the max_length of the name field is 100 characters."""
        s = deepcopy(self.service)
        s.name = ("Gate Diagnostics and Calibration for Intergalactic Travel through the Quantum Bridge Device "
                  "Portal - Series SG-1")  # Exceeding the max_length (112 characters)
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_negative_price_and_down_payment_values(self):
        """Test that the price and down_payment fields cannot be negative."""
        s = deepcopy(self.service)
        s.price = -100
        with self.assertRaises(ValidationError):
            s.full_clean()

        s = deepcopy(self.service)
        s.down_payment = -100
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_invalid_currency_code_length(self):
        """A service cannot be created with a currency of less or more than three characters."""
        s = deepcopy(self.service)
        s.currency = "US"

        with self.assertRaises(ValidationError):
            s.full_clean()

        s.currency = "DOLLAR"
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_zero_or_negative_duration_handling(self):
        """A service cannot be created with a duration being zero or negative."""
        service = Service(name="Zat'nik'tel Tune-Up", duration=timedelta(0), price=100, description="Tune-up the Zat")
        self.assertRaises(ValidationError, service.full_clean)
        service = Service(name="Ancient's Archive Retrieval ", duration=timedelta(seconds=-1), price=50,
                          description="Retrieve the Ancient's Archive")
        self.assertRaises(ValidationError, service.full_clean)

    def test_creation_without_service_name(self):
        """A service cannot be created with no name."""
        with self.assertRaises(ValidationError):
            Service.objects.create(name="", duration=timedelta(hours=1), price=100).full_clean()
