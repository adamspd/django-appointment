from datetime import timedelta, date, time

from django.test import TestCase

from appointment.models import PaymentInfo, Appointment, Service, AppointmentRequest
from appointment.utils import Utility


class PaymentInfoModelTestCase(TestCase):
    def setUp(self):
        self.user_model = Utility.get_user_model()
        self.user = self.user_model.objects.create_user(first_name="Tester",
                                                        email="testemail@gmail.com",
                                                        username="test_user", password="Kfdqi3!?n")
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100)
        self.ar = AppointmentRequest.objects.create(date=date.today(), start_time=time(9, 0), end_time=time(10, 0),
                                                    service=self.service)
        self.appointment = Appointment.objects.create(client=self.user, appointment_request=self.ar)
        self.payment_info = PaymentInfo.objects.create(appointment=self.appointment)

    def test_payment_info_creation(self):
        payment_info = PaymentInfo.objects.get(appointment=self.appointment)
        self.assertIsNotNone(payment_info)
        self.assertEqual(payment_info.appointment, self.appointment)

    def test_str_representation(self):
        self.assertEqual(str(self.payment_info), f"{self.service.name} - {self.service.price}")

    def test_get_id_request(self):
        self.assertEqual(self.payment_info.get_id_request(), self.appointment.get_appointment_id_request())

    def test_get_amount_to_pay(self):
        self.assertEqual(self.payment_info.get_amount_to_pay(), self.appointment.get_appointment_amount_to_pay())

    def test_get_currency(self):
        self.assertEqual(self.payment_info.get_currency(), self.appointment.get_appointment_currency())

    def test_get_name(self):
        self.assertEqual(self.payment_info.get_name(), self.appointment.get_service_name())

    def test_get_img_url(self):
        pass
        # self.assertEqual(self.payment_info.get_img_url(), self.appointment.get_service_img_url())

    def test_set_paid_status(self):
        self.payment_info.set_paid_status(True)
        self.assertTrue(self.appointment.is_paid())
        self.payment_info.set_paid_status(False)
        self.assertFalse(self.appointment.is_paid())

    def test_get_user_name(self):
        self.assertEqual(self.payment_info.get_user_name(), self.user.first_name)

    def test_get_user_email(self):
        self.assertEqual(self.payment_info.get_user_email(), self.user.email)

    def test_created_at(self):
        self.assertIsNotNone(self.payment_info.created_at)

    def test_updated_at(self):
        self.assertIsNotNone(self.payment_info.updated_at)
