from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from appointment.models import AppointmentRescheduleHistory
from appointment.tests.base.base_test import BaseTest


class AppointmentRescheduleHistoryCreationTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        self.appointment_request = self.create_appt_request_for_sm1()
        self.future_date = timezone.now().date() + timedelta(days=3)
        return super().setUp()

    def test_reschedule_history_creation_with_valid_data(self):
        reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.appointment_request,
            date=self.future_date,
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            staff_member=self.staff_member1,
            reason_for_rescheduling="Client request",
            reschedule_status='pending'
        )
        self.assertIsNotNone(reschedule_history)
        self.assertEqual(reschedule_history.reschedule_status, 'pending')
        self.assertTrue(reschedule_history.still_valid())

    def test_auto_generation_of_id_request_on_creation(self):
        reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.appointment_request,
            date=self.future_date,
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            staff_member=self.staff_member1
        )
        self.assertIsNotNone(reschedule_history.id_request)


class AppointmentRescheduleHistoryValidationTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.past_date = timezone.now().date() - timedelta(days=3)
        cls.future_date = timezone.now().date() + timedelta(days=3)

    def setUp(self):
        self.appointment_request = self.create_appt_request_for_sm1()

    def test_creation_with_past_date_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            AppointmentRescheduleHistory.objects.create(
                appointment_request=self.appointment_request,
                date=self.past_date,
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timedelta(hours=1)).time(),
                staff_member=self.staff_member1
            )

    def test_invalid_date_format_raises_type_error(self):
        with self.assertRaises(TypeError):
            AppointmentRescheduleHistory.objects.create(
                appointment_request=self.appointment_request,
                date="invalid-date",
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timedelta(hours=1)).time(),
                staff_member=self.staff_member1
            )


class AppointmentRescheduleHistoryTimingTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    def setUp(self):
        self.appointment_request = self.create_appt_request_for_sm1()
        self.future_date = timezone.now().date() + timedelta(days=3)
        return super().setUp()

    def test_still_valid_within_time_frame(self):
        reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.appointment_request,
            date=self.future_date,
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            staff_member=self.staff_member1,
            reason_for_rescheduling="Client request",
            reschedule_status='pending'
        )
        self.assertTrue(reschedule_history.still_valid())

    def test_still_valid_outside_time_frame(self):
        reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.appointment_request,
            date=self.future_date,
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            staff_member=self.staff_member1,
            reason_for_rescheduling="Client request",
            reschedule_status='pending'
        )
        self.assertTrue(reschedule_history.still_valid())
        # Simulate passage of time beyond the validity window
        reschedule_history.created_at -= timedelta(minutes=6)
        reschedule_history.save()
        self.assertFalse(reschedule_history.still_valid())
