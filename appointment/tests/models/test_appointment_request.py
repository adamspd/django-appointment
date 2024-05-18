from copy import deepcopy
from datetime import date, datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from appointment.tests.base.base_test import BaseTest


class AppointmentRequestCreationAndBasicAttributesTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self) -> None:
        self.ar = self.create_appt_request_for_sm1()
        return super().setUp()

    def tearDown(self):
        self.ar.delete()
        super().tearDown()

    def test_default_attributes_on_creation(self):
        self.assertIsNotNone(self.ar)
        self.assertEqual(self.ar.service, self.service1)
        self.assertEqual(self.ar.staff_member, self.staff_member1)
        self.assertEqual(self.ar.start_time, time(9, 0))
        self.assertEqual(self.ar.end_time, time(10, 0))
        self.assertIsNotNone(self.ar.get_id_request())
        self.assertEqual(self.ar.date, timezone.now().date())
        self.assertTrue(isinstance(self.ar.get_id_request(), str))
        self.assertIsNotNone(self.ar.created_at)
        self.assertIsNotNone(self.ar.updated_at)

    def test_appointment_request_initial_state(self):
        """Check the initial state of "reschedule attempts" and string representation."""
        self.assertEqual(self.ar.reschedule_attempts, 0)
        expected_representation = f"{self.ar.date} - {self.ar.start_time} to {self.ar.end_time} - {self.ar.service.name}"
        self.assertEqual(str(self.ar), expected_representation)


class AppointmentRequestServiceAttributesTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self) -> None:
        self.ar = self.create_appt_request_for_sm1()
        return super().setUp()

    def tearDown(self):
        self.ar.delete()
        super().tearDown()

    def test_service_related_attributes_are_correct(self):
        """Validate attributes related to the service within an appointment request."""
        self.assertEqual(self.ar.get_service_name(), self.service1.name)
        self.assertEqual(self.ar.get_service_price(), self.service1.get_price())
        self.assertEqual(self.ar.get_service_down_payment(), self.service1.get_down_payment())
        self.assertEqual(self.ar.get_service_image(), self.service1.image)
        self.assertEqual(self.ar.get_service_image_url(), self.service1.get_image_url())
        self.assertEqual(self.ar.get_service_description(), self.service1.description)
        self.assertTrue(self.ar.is_a_paid_service())
        self.assertEqual(self.ar.payment_type, 'full')
        self.assertFalse(self.ar.accepts_down_payment())


class AppointmentRequestAttributeValidation(BaseTest):
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self) -> None:
        self.ar = self.create_appt_request_for_sm1()
        return super().setUp()

    def tearDown(self):
        self.ar.delete()
        super().tearDown()

    def test_appointment_request_time_validations(self):
        """Ensure start and end times are validated correctly."""
        ar = deepcopy(self.ar)

        # End time before start time
        ar.start_time = time(11, 0)
        ar.end_time = time(9, 0)
        with self.assertRaises(ValidationError):
            ar.full_clean()

        # End time equal to start time
        ar.end_time = time(11, 0)
        with self.assertRaises(ValidationError):
            ar.full_clean()

        with self.assertRaises(ValidationError, msg="Start time and end time cannot be the same"):
            self.create_appointment_request_(
                self.service1, self.staff_member1, date_=date.today(), start_time=time(10, 0), end_time=time(10, 0)
            )

    def test_appointment_request_date_validations(self):
        """Validate that appointment requests cannot be in the past or have invalid durations."""
        ar = deepcopy(self.ar)

        past_date = date.today() - timedelta(days=30)
        ar.date = past_date
        with self.assertRaises(ValidationError):
            ar.full_clean()

        with self.assertRaises(ValidationError, msg="Date cannot be in the past"):
            self.create_appointment_request_(self.service1, self.staff_member1, date_=past_date)

        with self.assertRaises(ValidationError, msg="The date is not valid"):
            date_ = datetime.strptime("31-03-2021", "%d-%m-%Y").date()
            self.create_appointment_request_(
                self.service1, self.staff_member1, date_=date_)

    def test_appointment_duration_exceeds_service_time(self):
        """Test that an appointment cannot be created with a duration greater than the service duration."""
        long_duration = timedelta(hours=3)
        service = self.create_service_(name="Asgard Technology Retrofit", duration=long_duration)
        service.duration = long_duration
        service.save()

        # Create an appointment request with a 4-hour duration and the 3-hour service (should not work)
        with self.assertRaises(ValidationError):
            self.create_appointment_request_(service, self.staff_member1, start_time=time(9, 0),
                                             end_time=time(13, 0))

    def test_invalid_payment_type_raises_error(self):
        """Payment type must be either 'full' or 'down'"""
        ar = deepcopy(self.ar)
        ar.payment_type = "Naquadah Instead of Credits"
        with self.assertRaises(ValidationError):
            ar.full_clean()


class AppointmentRequestRescheduleHistory(BaseTest):
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self) -> None:
        service = deepcopy(self.service1)
        service.reschedule_limit = 2
        service.allow_rescheduling = True
        service.save()
        self.ar_ = self.create_appt_request_for_sm1(service=service)
        return super().setUp()

    def test_ar_can_be_reschedule(self):
        self.assertTrue(self.ar_.can_be_rescheduled())

    def test_reschedule_attempts_increment(self):
        self.assertTrue(self.ar_.can_be_rescheduled())
        self.ar_.increment_reschedule_attempts()
        self.assertEqual(self.ar_.reschedule_attempts, 1)
        self.assertTrue(self.ar_.can_be_rescheduled())
        self.ar_.increment_reschedule_attempts()
        self.assertEqual(self.ar_.reschedule_attempts, 2)
        self.assertFalse(self.ar_.can_be_rescheduled())

    def test_no_reschedule_history(self):
        service = deepcopy(self.service1)
        ar = self.create_appointment_request_(service, self.staff_member1)
        self.assertFalse(ar.get_reschedule_history().exists())
