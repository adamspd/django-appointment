from datetime import date, timedelta, time, datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from appointment.models import Service, Appointment, AppointmentRequest
from appointment.utils import Utility


class AppointmentModelTestCase(TestCase):
    def setUp(self):
        self.user_model = Utility.get_user_model()
        self.user = self.user_model.objects.create_user(first_name="Tester",
                                                        email="testemail@gmail.com",
                                                        username="test_user", password="Kfdqi3!?n")
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100)
        self.ar = AppointmentRequest.objects.create(date=date.today(), start_time=time(9, 0), end_time=time(10, 0),
                                                    service=self.service)
        self.appointment = Appointment.objects.create(client=self.user, appointment_request=self.ar,
                                                      phone="1234567890", address="Some City, Some State")

    # Test appointment creation
    def test_appointment_creation(self):
        appointment = Appointment.objects.get(appointment_request=self.ar)
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.client, self.user)
        self.assertEqual(appointment.phone, "1234567890")
        self.assertEqual(appointment.address, "Some City, Some State")

    # Test str representation
    def test_str_representation(self):
        expected_str = f"{self.user} - {self.ar.start_time.strftime('%Y-%m-%d %H:%M')} to " \
                       f"{self.ar.end_time.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.appointment), expected_str)

    # Test start time
    def test_get_start_time(self):
        expected_start_time = datetime.combine(self.ar.get_date(),
                                               self.ar.get_start_time())
        self.assertEqual(self.appointment.get_start_time(), expected_start_time)

    # Test end time
    def test_get_end_time(self):
        expected_end_time = datetime.combine(self.ar.get_date(),
                                             self.ar.get_end_time())
        self.assertEqual(self.appointment.get_end_time(), expected_end_time)

    # Test service name retrieval
    def test_get_service_name(self):
        self.assertEqual(self.appointment.get_service_name(), "Test Service")

    # Test service price retrieval
    def test_get_service_price(self):
        self.assertEqual(self.appointment.get_service_price(), 100)

    # Test phone retrieval
    def test_get_phone(self):
        self.assertEqual(self.appointment.get_phone(), "1234567890")

    # Test address retrieval
    def test_get_address(self):
        self.assertEqual(self.appointment.get_address(), "Some City, Some State")

    # Test reminder retrieval
    def test_get_want_reminder(self):
        self.assertFalse(self.appointment.get_want_reminder())

    # Test additional info retrieval
    def test_get_additional_info(self):
        self.assertIsNone(self.appointment.get_additional_info())

    # Test paid status retrieval
    def test_is_paid(self):
        self.assertFalse(self.appointment.is_paid())

    # Test appointment amount to pay
    def test_get_appointment_amount_to_pay(self):
        self.assertEqual(self.appointment.get_appointment_amount_to_pay(), 100)

    # Test appointment currency retrieval
    def test_get_appointment_currency(self):
        self.assertEqual(self.appointment.get_appointment_currency(), "USD")

    # Test appointment ID request retrieval
    def test_get_appointment_id_request(self):
        self.assertIsNotNone(self.appointment.get_appointment_id_request())

    # Test created at retrieval
    def test_get_created_at(self):
        self.assertIsNotNone(self.appointment.get_created_at())

    # Test updated at retrieval
    def test_get_updated_at(self):
        self.assertIsNotNone(self.appointment.get_updated_at())

    # Test paid status setting
    def test_set_appointment_paid_status(self):
        self.appointment.set_appointment_paid_status(True)
        self.assertTrue(self.appointment.is_paid())
        self.appointment.set_appointment_paid_status(False)
        self.assertFalse(self.appointment.is_paid())

    # Test invalid phone number
    def test_invalid_phone(self):
        self.appointment.phone = "1234"  # Invalid phone number
        with self.assertRaises(ValidationError):
            self.appointment.full_clean()

    # Test service down payment retrieval
    def test_get_service_down_payment(self):
        self.assertEqual(self.appointment.get_service_down_payment(), self.service.get_down_payment())

    # Test service description retrieval
    def test_get_service_description(self):
        self.assertEqual(self.appointment.get_service_description(), self.service.get_description())

    # Test appointment date retrieval
    def test_get_appointment_date(self):
        self.assertEqual(self.appointment.get_appointment_date(), self.ar.get_date())

    # Test save function with down payment type
    def test_save_with_down_payment(self):
        self.ar.payment_type = 'down'
        self.ar.save()
        self.appointment.save()
        self.assertEqual(self.appointment.get_service_down_payment(), self.service.get_down_payment())
