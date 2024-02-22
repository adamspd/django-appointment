import datetime
from datetime import date, time, timedelta

from django.core.exceptions import ValidationError

from appointment.tests.base.base_test import BaseTest


class AppointmentRequestModelTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.ar = self.create_appointment_request_(self.service1, self.staff_member1)
        self.today = date.today()

    def test_appointment_request_creation(self):
        """Test if an appointment request can be created."""
        self.assertIsNotNone(self.ar)
        self.assertEqual(self.ar.start_time, time(9, 0))
        self.assertEqual(self.ar.end_time, time(10, 0))

    def test_service_name_retrieval(self):
        """Test if an appointment request's service name is correct."""
        self.assertEqual(self.ar.get_service_name(), "Test Service")

    def test_service_price_retrieval(self):
        self.assertEqual(self.ar.get_service_price(), 100)

    def test_invalid_start_time(self):
        """Start time must be before end time"""
        self.ar.start_time = time(11, 0)
        self.ar.end_time = time(9, 0)
        with self.assertRaises(ValueError):
            self.ar.full_clean()

    def test_invalid_payment_type(self):
        """Payment type must be either 'full' or 'down'"""
        self.ar.payment_type = "invalid"
        with self.assertRaises(ValidationError):
            self.ar.full_clean()

    def test_get_date(self):
        """Test if an appointment request's date is correct."""
        self.assertEqual(self.ar.date, date.today())

    def test_get_start_time(self):
        """Test if an appointment request's start time is correct."""
        self.assertEqual(self.ar.start_time, time(9, 0))

    def test_get_end_time(self):
        """Test if an appointment request's end time is correct."""
        self.assertEqual(self.ar.end_time, time(10, 0))

    def test_get_service_down_payment(self):
        """Test if an appointment request's service down payment is correct."""
        self.assertEqual(self.ar.get_service_down_payment(), 0)

    def test_get_service_image(self):
        """ test_get_service_image not implemented yet."""
        # self.assertIsNone(self.ar.get_service_image())
        pass

    def test_get_service_image_url(self):
        """test_get_service_image_url's implementation not finished yet."""
        pass

    def test_get_service_description(self):
        """Test if an appointment request's service description is correct."""
        self.assertIsNone(self.ar.get_service_description())

    def test_get_id_request(self):
        """Test if an appointment request's ID request is correct."""
        self.assertIsNotNone(self.ar.get_id_request())
        self.assertIsInstance(self.ar.get_id_request(), str)

    def test_is_a_paid_service(self):
        """Test if an appointment request's service is a paid service."""
        self.assertTrue(self.ar.is_a_paid_service())

    def test_accepts_down_payment_false(self):
        """Test if an appointment request's service accepts down payment."""
        self.assertFalse(self.ar.accepts_down_payment())

    def test_get_payment_type(self):
        """Test if an appointment request's payment type is correct."""
        self.assertEqual(self.ar.payment_type, 'full')

    def test_created_at(self):
        """Test if an appointment request's created at date is correctly set upon creation."""
        self.assertIsNotNone(self.ar.created_at)

    def test_updated_at(self):
        """Test if an appointment request's updated at date is correctly set upon creation."""
        self.assertIsNotNone(self.ar.updated_at)

    def test_appointment_with_same_start_and_end_time(self):
        """
        Test the situation where an appointment's start time is equal to the end time.
        The model will prevent this.
        """
        with self.assertRaises(ValidationError):
            self.create_appointment_request_(self.service1, self.staff_member1, start_time=time(9, 0),
                                             end_time=time(9, 0))

    def test_appointment_in_past(self):
        """Test that an appointment cannot be created in the past."""
        past_date = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.create_appointment_request_(self.service1, self.staff_member1, date_=past_date)

    def test_appointment_duration_exceeds_service_time(self):
        """Test that an appointment cannot be created with a duration greater than the service duration."""
        long_duration = timedelta(hours=3)
        self.service1.duration = long_duration
        self.service1.save()

        # Assuming the appointment request uses the service duration
        with self.assertRaises(ValidationError):
            self.create_appointment_request_(self.service1, self.staff_member1, start_time=time(9, 0),
                                             end_time=time(13, 0))

    def test_reschedule_attempts_limit(self):
        """Test appointment request's ability to be rescheduled based on service's limit."""
        self.service1.reschedule_limit = 2
        self.service1.save()

        # Simulate rescheduling attempts
        self.ar.increment_reschedule_attempts()
        self.assertTrue(self.ar.can_be_rescheduled())

        self.ar.increment_reschedule_attempts()
        self.assertFalse(self.ar.can_be_rescheduled(),
                         "Should not be reschedulable after reaching the limit")

    def test_appointment_request_with_invalid_date(self):
        """Appointment date should be valid and not in the past."""
        invalid_date = self.today - timedelta(days=1)
        with self.assertRaises(ValidationError, msg="Date cannot be in the past"):
            self.create_appointment_request_(
                self.service1, self.staff_member1, date_=invalid_date, start_time=time(10, 0), end_time=time(11, 0)
            )
        with self.assertRaises(ValidationError, msg="The date is not valid"):
            date_ = datetime.datetime.strptime("31-03-2021", "%d-%m-%Y").date()
            self.create_appointment_request_(
                self.service1, self.staff_member1, date_=date_,
                start_time=time(10, 0), end_time=time(11, 0)
            )

    def test_start_time_after_end_time(self):
        """Start time should not be after end time."""
        with self.assertRaises(ValueError, msg="Start time must be before end time"):
            self.create_appointment_request_(
                self.service1, self.staff_member1, date_=self.today, start_time=time(11, 0), end_time=time(10, 0)
            )

    def test_start_time_equals_end_time(self):
        """Start time and end time should not be the same."""
        with self.assertRaises(ValidationError, msg="Start time and end time cannot be the same"):
            self.create_appointment_request_(
                self.service1, self.staff_member1, date_=self.today, start_time=time(10, 0), end_time=time(10, 0)
            )

    def test_appointment_duration_not_exceed_service(self):
        """Appointment duration should not exceed the service's duration."""
        extended_end_time = time(11, 30)  # 2.5 hours, exceeding the 1-hour service duration
        with self.assertRaises(ValidationError, msg="Duration cannot exceed the service duration"):
            self.create_appointment_request_(
                self.service1, self.staff_member1, date_=self.today, start_time=time(9, 0), end_time=extended_end_time
            )
