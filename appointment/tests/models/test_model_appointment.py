from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from appointment.models import Appointment
from appointment.tests.base.base_test import BaseTest


class AppointmentModelTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.ar = self.create_appt_request_for_sm1()
        self.appointment = self.create_appointment_for_user1(appointment_request=self.ar)

    # Test appointment creation
    def test_appointment_creation(self):
        """Test if an appointment can be created."""
        appointment = Appointment.objects.get(appointment_request=self.ar)
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.client, self.client1)
        self.assertEqual(appointment.phone, "1234567890")
        self.assertEqual(appointment.address, "Some City, Some State")

    # Test str representation
    def test_str_representation(self):
        """Test if an appointment's string representation is correct."""
        expected_str = f"{self.client1} - {self.ar.start_time.strftime('%Y-%m-%d %H:%M')} to " \
                       f"{self.ar.end_time.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.appointment), expected_str)

    # Test start time
    def test_get_start_time(self):
        """Test if an appointment's start time is correct."""
        expected_start_time = datetime.combine(self.ar.date,
                                               self.ar.start_time)
        self.assertEqual(self.appointment.get_start_time(), expected_start_time)

    # Test end time
    def test_get_end_time(self):
        """Test if an appointment's end time is correct."""
        expected_end_time = datetime.combine(self.ar.date,
                                             self.ar.end_time)
        self.assertEqual(self.appointment.get_end_time(), expected_end_time)

    # Test service name retrieval
    def test_get_service_name(self):
        """Test if an appointment's service name is correct."""
        self.assertEqual(self.appointment.get_service_name(), "Test Service")

    # Test service price retrieval
    def test_get_service_price(self):
        """Test if an appointment's service price is correct."""
        self.assertEqual(self.appointment.get_service_price(), 100)

    # Test phone retrieval
    def test_get_phone(self):
        """Test if an appointment's phone number is correct."""
        self.assertEqual(self.appointment.phone, "1234567890")

    # Test address retrieval
    def test_get_address(self):
        """Test if an appointment's address is correct."""
        self.assertEqual(self.appointment.address, "Some City, Some State")

    # Test reminder retrieval
    def test_get_want_reminder(self):
        """Test if an appointment's reminder status is correct."""
        self.assertFalse(self.appointment.want_reminder)

    # Test additional info retrieval
    def test_get_additional_info(self):
        """Test if an appointment's additional info is correct."""
        self.assertIsNone(self.appointment.additional_info)

    # Test paid status retrieval
    def test_is_paid(self):
        """Test if an appointment's paid status is correct."""
        self.assertFalse(self.appointment.is_paid())

    def test_is_paid_text(self):
        """Test if an appointment's paid status is correct."""
        self.assertEqual(self.appointment.is_paid_text(), "No")

    # Test appointment amount to pay
    def test_get_appointment_amount_to_pay(self):
        """Test if an appointment's amount to pay is correct."""
        self.assertEqual(self.appointment.get_appointment_amount_to_pay(), 100)

    # Test appointment currency retrieval
    def test_get_appointment_currency(self):
        """Test if an appointment's currency is correct."""
        self.assertEqual(self.appointment.get_appointment_currency(), "USD")

    # Test appointment ID request retrieval
    def test_get_appointment_id_request(self):
        """Test if an appointment's ID request is correct."""
        self.assertIsNotNone(self.appointment.get_appointment_id_request())

    # Test created at retrieval
    def test_created_at(self):
        """Test if an appointment's created at date is correct."""
        self.assertIsNotNone(self.appointment.created_at)

    # Test updated at retrieval
    def test_updated_at(self):
        """Test if an appointment's updated at date is correct."""
        self.assertIsNotNone(self.appointment.updated_at)

    # Test paid status setting
    def test_set_appointment_paid_status(self):
        """Test if an appointment's paid status can be set."""
        self.appointment.set_appointment_paid_status(True)
        self.assertTrue(self.appointment.is_paid())
        self.appointment.set_appointment_paid_status(False)
        self.assertFalse(self.appointment.is_paid())

    # Test invalid phone number
    def test_invalid_phone(self):
        """Test that an appointment cannot be created with an invalid phone number."""
        self.appointment.phone = "1234"  # Invalid phone number
        with self.assertRaises(ValidationError):
            self.appointment.full_clean()

    # Test service down payment retrieval
    def test_get_service_down_payment(self):
        """Test if an appointment's service down payment is correct."""
        self.assertEqual(self.appointment.get_service_down_payment(), self.service1.get_down_payment())

    # Test service description retrieval
    def test_service_description(self):
        """Test if an appointment's service description is correct."""
        self.assertEqual(self.appointment.get_service_description(), self.service1.description)

    # Test appointment date retrieval
    def test_get_appointment_date(self):
        """Test if an appointment's date is correct."""
        self.assertEqual(self.appointment.get_appointment_date(), self.ar.date)

    # Test save function with down payment type
    def test_save_with_down_payment(self):
        """Test if an appointment can be saved with a down payment."""
        self.ar.payment_type = 'down'
        self.ar.save()
        self.appointment.save()
        self.assertEqual(self.appointment.get_service_down_payment(), self.service1.get_down_payment())

    def test_appointment_without_appointment_request(self):
        """Test that an appointment cannot be created without an appointment request."""
        with self.assertRaises(ValidationError):  # Assuming model validation prevents this
            Appointment.objects.create(client=self.client1)

    def test_appointment_without_client(self):
        """Test that an appointment cannot be created without a client."""
        with self.assertRaises(IntegrityError):  # Assuming model validation prevents this
            Appointment.objects.create(appointment_request=self.ar)

    def test_appointment_amount_to_pay_calculation(self):
        """
        Test if an appointment's amount_to_pay field is correctly calculated based on the associated AppointmentRequest.
        """
        self.assertEqual(self.appointment.get_appointment_amount_to_pay(), self.ar.get_service_price())

    def test_update_appointment_paid_status(self):
        """Simulate appointment's paid status being updated."""
        self.appointment.set_appointment_paid_status(True)
        self.assertTrue(self.appointment.is_paid())
        self.appointment.set_appointment_paid_status(False)
        self.assertFalse(self.appointment.is_paid())

    def test_appointment_rescheduling(self):
        """Simulate appointment rescheduling by changing the appointment date and times."""
        new_date = self.ar.date + timedelta(days=1)
        new_start_time = time(10, 0)
        new_end_time = time(11, 0)
        self.ar.date = new_date
        self.ar.start_time = new_start_time
        self.ar.end_time = new_end_time
        self.ar.save()

        self.assertEqual(self.appointment.get_date(), new_date)
        self.assertEqual(self.appointment.get_start_time().time(), new_start_time)
        self.assertEqual(self.appointment.get_end_time().time(), new_end_time)

    def test_create_appointment_without_required_fields(self):
        """Test that an appointment cannot be created without the required fields."""
        with self.assertRaises(ValidationError):
            Appointment.objects.create()

    def test_get_service_duration(self):
        """Test if an appointment's service duration is correct."""
        self.assertEqual(self.appointment.get_service_duration(), "1 hour")

    def test_appt_to_dict(self):
        response = {
            'id': 1,
            'client_name': 'Client1',
            'client_email': 'client1@gmail.com',
            'start_time': '1900-01-01 09:00',
            'end_time': '1900-01-01 10:00',
            'service_name': 'Test Service',
            'address': 'Some City, Some State',
            'want_reminder': False,
            'additional_info': None,
            'paid': False,
            'amount_to_pay': 100,
        }
        actual_response = self.appointment.to_dict()
        actual_response.pop('id_request', None)
        self.assertEqual(actual_response, response)

    def test_get_staff_member_name_with_staff_member(self):
        """Test if you get_staff_member_name method returns the correct name when a staff member is associated."""
        expected_name = self.staff_member1.get_staff_member_name()
        actual_name = self.appointment.get_staff_member_name()
        self.assertEqual(actual_name, expected_name)

    def test_get_staff_member_name_without_staff_member(self):
        """Test if you get_staff_member_name method returns an empty string when no staff member is associated."""
        self.appointment.appointment_request.staff_member = None
        self.appointment.appointment_request.save()
        self.assertEqual(self.appointment.get_staff_member_name(), "")
