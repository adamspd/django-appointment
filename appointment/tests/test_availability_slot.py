from datetime import date, time, timedelta

from django.test import TestCase

from appointment.models import Appointment, AppointmentRequest
from appointment.tests.mixins.base_mixin import AppointmentMixin, AppointmentRequestMixin, ConfigMixin, ServiceMixin, \
    StaffMemberMixin, UserMixin
from appointment.views import get_appointments_and_slots


class SlotAvailabilityTest(TestCase, UserMixin, ServiceMixin, StaffMemberMixin, AppointmentRequestMixin,
                           AppointmentMixin, ConfigMixin):
    def setUp(self):
        self.user = self.create_user_()
        self.service = self.create_service_(duration=timedelta(hours=2))
        self.staff_member = self.create_staff_member_(self.user, self.service)
        self.ar = self.create_appointment_request_(self.service, self.staff_member)
        self.appointment = self.create_appointment_(self.user, self.ar)
        self.config = self.create_config_(lead_time=time(11, 0), finish_time=time(15, 0), slot_duration=120)
        self.test_date = date.today() + timedelta(days=1)  # Use tomorrow's date for the tests

    def test_slot_availability_without_appointments(self):
        """Test if the available slots are correct when there are no appointments."""
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['11:00 AM', '01:00 PM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_first_slot_booked(self):
        """Available slots (total 2) should be one when the first slot is booked."""
        ar = AppointmentRequest.objects.create(date=self.test_date, start_time=time(11, 0), end_time=time(13, 0),
                                               service=self.service, staff_member=self.staff_member)
        Appointment.objects.create(client=self.user, appointment_request=ar)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['01:00 PM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_second_slot_booked(self):
        """Available slots (total 2) should be one when the second slot is booked."""
        ar = AppointmentRequest.objects.create(date=self.test_date, start_time=time(13, 0), end_time=time(15, 0),
                                               service=self.service, staff_member=self.staff_member)
        Appointment.objects.create(client=self.user, appointment_request=ar)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['11:00 AM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_both_slots_booked(self):
        """Available slots (total 2) should be zero when both slots are booked."""
        ar1 = AppointmentRequest.objects.create(date=self.test_date, start_time=time(11, 0), end_time=time(13, 0),
                                                service=self.service, staff_member=self.staff_member)
        ar2 = AppointmentRequest.objects.create(date=self.test_date, start_time=time(13, 0), end_time=time(15, 0),
                                                service=self.service, staff_member=self.staff_member)
        Appointment.objects.create(client=self.user, appointment_request=ar1)
        Appointment.objects.create(client=self.user, appointment_request=ar2)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = []
        self.assertEqual(available_slots, expected_slots)
