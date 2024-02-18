from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from appointment.models import AppointmentRescheduleHistory
from appointment.tests.base.base_test import BaseTest


class AppointmentRescheduleHistoryTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment_request = self.create_appt_request_for_sm1()

    def test_successful_creation(self):
        reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.appointment_request,
            date=timezone.now().date() + timedelta(days=1),  # Future date
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            staff_member=self.staff_member1,
            reason_for_rescheduling="Client request",
            reschedule_status='pending'
        )
        self.assertIsNotNone(reschedule_history.id_request)  # Auto-generated id_request
        self.assertTrue(reschedule_history.still_valid())

    def test_date_in_past_validation(self):
        with self.assertRaises(ValidationError):
            AppointmentRescheduleHistory.objects.create(
                appointment_request=self.appointment_request,
                date=timezone.now().date() - timedelta(days=1),  # Past date
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timedelta(hours=1)).time(),
                staff_member=self.staff_member1
            )

    def test_invalid_date_validation(self):
        with self.assertRaises(TypeError):
            AppointmentRescheduleHistory.objects.create(
                appointment_request=self.appointment_request,
                date="invalid-date",  # Invalid date format
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timedelta(hours=1)).time(),
                staff_member=self.staff_member1
            )

    def test_still_valid(self):
        reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.appointment_request,
            date=timezone.now().date() + timedelta(days=1),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            staff_member=self.staff_member1,
            reason_for_rescheduling="Client request",
            reschedule_status='pending'
        )
        # Directly test the still_valid method
        self.assertTrue(reschedule_history.still_valid())

        # Simulate passages of time beyond the validity window
        reschedule_history.created_at -= timedelta(minutes=6)
        reschedule_history.save()
        self.assertFalse(reschedule_history.still_valid())
