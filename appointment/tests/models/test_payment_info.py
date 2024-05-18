from appointment.models import PaymentInfo
from appointment.tests.base.base_test import BaseTest


class PaymentInfoBasicTestCase(BaseTest):
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self):
        self.ar = self.create_appt_request_for_sm1()
        self.appointment = self.create_appt_for_sm1(appointment_request=self.ar)
        self.payment_info = PaymentInfo.objects.create(appointment=self.appointment)
        return super().setUp()

    def tearDown(self):
        self.ar.delete()
        self.appointment.delete()
        self.payment_info.delete()
        return super().tearDown()

    def test_str_representation(self):
        """Test if payment info's string representation is correct."""
        self.assertEqual(str(self.payment_info), f"{self.service1.name} - {self.service1.price}")

    def test_default_attributes_on_creation(self):
        """Test if payment info can be created."""
        payment_info = PaymentInfo.objects.get(appointment=self.appointment)
        self.assertIsNotNone(payment_info)
        self.assertEqual(payment_info.appointment, self.appointment)
        self.assertEqual(self.payment_info.get_id_request(), self.appointment.get_appointment_id_request())
        self.assertEqual(self.payment_info.get_amount_to_pay(), self.appointment.get_appointment_amount_to_pay())
        self.assertEqual(self.payment_info.get_currency(), self.appointment.get_appointment_currency())
        self.assertEqual(self.payment_info.get_name(), self.appointment.get_service_name())
        self.assertIsNotNone(self.payment_info.created_at)
        self.assertIsNotNone(self.payment_info.updated_at)

    def test_get_user_info(self):
        """Test if payment info's username is correct."""
        self.assertEqual(self.payment_info.get_user_name(), self.users['client1'].first_name)
        self.assertEqual(self.payment_info.get_user_email(), self.users['client1'].email)


class PaymentInfoStatusTestCase(BaseTest):
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self):
        self.ar = self.create_appt_request_for_sm1()
        self.appointment = self.create_appt_for_sm1(appointment_request=self.ar)
        self.payment_info = PaymentInfo.objects.create(appointment=self.appointment)
        return super().setUp()

    def tearDown(self):
        self.ar.delete()
        self.appointment.delete()
        self.payment_info.delete()
        return super().tearDown()

    def test_set_paid_status(self):
        """Test if payment info's paid status can be set correctly."""
        self.payment_info.set_paid_status(True)
        self.assertTrue(self.appointment.is_paid())
        self.payment_info.set_paid_status(False)
        self.assertFalse(self.appointment.is_paid())
