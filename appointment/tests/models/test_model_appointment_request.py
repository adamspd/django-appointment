from datetime import timedelta, time, date

from django.core.exceptions import ValidationError
from django.test import TestCase

from appointment.models import Service, AppointmentRequest


class AppointmentRequestModelTestCase(TestCase):
    def setUp(self):
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100)
        self.ar = AppointmentRequest.objects.create(date=date.today(), start_time=time(9, 0), end_time=time(10, 0),
                                                    service=self.service)

    def test_appointment_request_creation(self):
        self.assertIsNotNone(self.ar)
        self.assertEqual(self.ar.start_time, time(9, 0))
        self.assertEqual(self.ar.end_time, time(10, 0))

    def test_service_name_retrieval(self):
        self.assertEqual(self.ar.get_service_name(), "Test Service")

    def test_service_duration_retrieval(self):
        self.assertEqual(self.ar.get_service_duration(), "1 hour")

    def test_service_price_retrieval(self):
        self.assertEqual(self.ar.get_service_price(), 100)

    def test_invalid_start_time(self):
        self.ar.start_time = time(11, 0)
        self.ar.end_time = time(9, 0)
        with self.assertRaises(ValueError):
            self.ar.full_clean()

    def test_invalid_payment_type(self):
        self.ar.payment_type = "invalid"
        with self.assertRaises(ValidationError):
            self.ar.full_clean()

    def test_get_date(self):
        self.assertEqual(self.ar.get_date(), date.today())

    def test_get_start_time(self):
        self.assertEqual(self.ar.get_start_time(), time(9, 0))

    def test_get_end_time(self):
        self.assertEqual(self.ar.get_end_time(), time(10, 0))

    def test_get_service_down_payment(self):
        self.assertEqual(self.ar.get_service_down_payment(), 0)

    def test_get_service_image(self):
        # self.assertIsNone(self.ar.get_service_image())
        pass

    def test_get_service_image_url(self):
        self.assertRaises(ValueError, self.ar.get_service_image_url)

    def test_get_service_description(self):
        self.assertIsNone(self.ar.get_service_description())

    def test_get_id_request(self):
        self.assertIsNotNone(self.ar.get_id_request())
        self.assertIsInstance(self.ar.get_id_request(), str)

    def test_is_a_paid_service(self):
        self.assertTrue(self.ar.is_a_paid_service())

    def test_accepts_down_payment_false(self):
        self.assertFalse(self.ar.accepts_down_payment())

    def test_get_payment_type(self):
        self.assertEqual(self.ar.get_payment_type(), 'full')

    def test_get_created_at(self):
        self.assertIsNotNone(self.ar.get_created_at())

    def test_get_updated_at(self):
        self.assertIsNotNone(self.ar.get_updated_at())
