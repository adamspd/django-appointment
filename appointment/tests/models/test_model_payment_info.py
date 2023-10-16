from appointment.models import PaymentInfo
from appointment.tests.base.base_test import BaseTest


class PaymentInfoModelTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.ar = self.create_appt_request_for_sm1()
        self.appointment = self.create_appointment_for_user1(appointment_request=self.ar)
        self.payment_info = PaymentInfo.objects.create(appointment=self.appointment)

    def test_payment_info_creation(self):
        """Test if a payment info can be created."""
        payment_info = PaymentInfo.objects.get(appointment=self.appointment)
        self.assertIsNotNone(payment_info)
        self.assertEqual(payment_info.appointment, self.appointment)

    def test_str_representation(self):
        """Test if a payment info's string representation is correct."""
        self.assertEqual(str(self.payment_info), f"{self.service1.name} - {self.service1.price}")

    def test_get_id_request(self):
        """Test if a payment info's id request is correct."""
        self.assertEqual(self.payment_info.get_id_request(), self.appointment.get_appointment_id_request())

    def test_get_amount_to_pay(self):
        """Test if a payment info's amount to pay is correct."""
        self.assertEqual(self.payment_info.get_amount_to_pay(), self.appointment.get_appointment_amount_to_pay())

    def test_get_currency(self):
        """Test if a payment info's currency is correct."""
        self.assertEqual(self.payment_info.get_currency(), self.appointment.get_appointment_currency())

    def test_get_name(self):
        """Test if payment info's name is correct."""
        self.assertEqual(self.payment_info.get_name(), self.appointment.get_service_name())

    def test_get_img_url(self):
        """test_get_img_url's implementation not finished yet."""
        pass
        # self.assertEqual(self.payment_info.get_img_url(), self.appointment.get_service_img_url())

    def test_set_paid_status(self):
        """Test if a payment info's paid status can be set correctly."""
        self.payment_info.set_paid_status(True)
        self.assertTrue(self.appointment.is_paid())
        self.payment_info.set_paid_status(False)
        self.assertFalse(self.appointment.is_paid())

    def test_get_user_name(self):
        """Test if payment info's username is correct."""
        self.assertEqual(self.payment_info.get_user_name(), self.client1.first_name)

    def test_get_user_email(self):
        """Test if payment info's user email is correct."""
        self.assertEqual(self.payment_info.get_user_email(), self.client1.email)

    def test_created_at(self):
        """Test if payment info's created at date is correctly set upon creation."""
        self.assertIsNotNone(self.payment_info.created_at)

    def test_updated_at(self):
        """Test if payment info's updated at date is correctly set upon creation."""
        self.assertIsNotNone(self.payment_info.updated_at)
