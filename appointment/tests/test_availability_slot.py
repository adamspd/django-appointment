from django.test import TestCase
from datetime import date, timedelta, time
from appointment.models import Service, AppointmentRequest, Config, Appointment
from appointment.utils import Utility
from appointment.views import get_appointments_and_slots


class SlotAvailabilityTest(TestCase):
    def setUp(self):
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=2), price=100)
        self.start_time = time(11, 0)
        self.finish_time = time(14, 0)
        self.slot_duration = 120
        self.appointment_buffer_time = 0
        self.config = Config.objects.create(
            lead_time=self.start_time,
            finish_time=self.finish_time,
            slot_duration=self.slot_duration,
            appointment_buffer_time=self.appointment_buffer_time
        )
        self.user_model = Utility.get_user_model()
        self.user = self.user_model.objects.create_user(first_name="Tester",
                                                        email="testemail@gmail.com",
                                                        username="test_user", password="Kfdqi3!?n")
        self.test_date = date.today() + timedelta(days=1)  # Use tomorrow's date for the tests

    def test_slot_availability_without_appointments(self):
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['11:00 AM', '01:00 PM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_first_slot_booked(self):
        ar = AppointmentRequest.objects.create(date=self.test_date, start_time=self.start_time, end_time=time(13, 0),
                                               service=self.service)
        Appointment.objects.create(client=self.user, appointment_request=ar)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['01:00 PM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_second_slot_booked(self):
        ar = AppointmentRequest.objects.create(date=self.test_date, start_time=time(13, 0), end_time=time(15, 0),
                                               service=self.service)
        Appointment.objects.create(client=self.user, appointment_request=ar)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['11:00 AM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_both_slots_booked(self):
        ar1 = AppointmentRequest.objects.create(date=self.test_date, start_time=self.start_time, end_time=time(13, 0),
                                                service=self.service)
        ar2 = AppointmentRequest.objects.create(date=self.test_date, start_time=time(13, 0), end_time=time(15, 0),
                                                service=self.service)
        Appointment.objects.create(client=self.user, appointment_request=ar1)
        Appointment.objects.create(client=self.user, appointment_request=ar2)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = []
        self.assertEqual(available_slots, expected_slots)
