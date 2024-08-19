from copy import deepcopy
from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext as _

from appointment.models import Appointment, DayOff, WorkingHours
from appointment.tests.base.base_test import BaseTest
from appointment.utils.date_time import get_weekday_num


class AppointmentCreationTestCase(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.address = 'Stargate Command, Cheyenne Mountain Complex, Colorado Springs, CO'
        self.ar = self.create_appt_request_for_sm1()
        self.appointment = self.create_appt_for_sm1(appointment_request=self.ar)
        self.client_ = self.users['client1']
        self.expected_end_time = datetime.combine(self.ar.date, self.ar.end_time)
        self.expected_service_name = 'Stargate Activation'
        self.expected_service_price = 100000
        self.expected_start_time = datetime.combine(self.ar.date, self.ar.start_time)
        self.phone = '+12392340543'
        return super().setUp()

    def tearDown(self):
        self.appointment.delete()
        return super().tearDown()

    def test_default_attributes_on_creation(self):
        """Test default attributes when an appointment is created."""
        self.assertIsNotNone(self.appointment)
        self.assertIsNotNone(self.appointment.created_at)
        self.assertIsNotNone(self.appointment.updated_at)
        self.assertIsNotNone(self.appointment.get_appointment_id_request())
        self.assertIsNone(self.appointment.additional_info)
        self.assertEqual(self.appointment.client, self.users['client1'])
        self.assertEqual(self.appointment.phone, self.phone)
        self.assertEqual(self.appointment.address, self.address)
        self.assertFalse(self.appointment.want_reminder)

    def test_str_representation(self):
        """Test if an appointment's string representation is correct."""
        expected_str = f"{self.client_} - {self.ar.start_time.strftime('%Y-%m-%d %H:%M')} to " \
                       f"{self.ar.end_time.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.appointment), expected_str)

    def test_appointment_getters(self):
        """Test getter methods for appointment details."""
        self.assertEqual(self.appointment.get_start_time(), self.expected_start_time)
        self.assertEqual(self.appointment.get_end_time(), self.expected_end_time)
        self.assertEqual(self.appointment.get_service_name(), self.expected_service_name)
        self.assertEqual(self.appointment.get_service_price(), self.expected_service_price)
        self.assertEqual(self.appointment.is_paid_text(), _('No'))
        self.assertEqual(self.appointment.get_appointment_amount_to_pay(), self.expected_service_price)
        self.assertEqual(self.appointment.get_service_down_payment(), self.service1.get_down_payment())
        self.assertEqual(self.appointment.get_service_description(), self.service1.description)
        self.assertEqual(self.appointment.get_appointment_date(), self.ar.date)
        self.assertEqual(self.appointment.get_service_duration(), "1 hour")
        self.assertEqual(self.appointment.get_appointment_currency(), "USD")
        self.assertEqual(self.appointment.get_appointment_amount_to_pay(), self.ar.get_service_price())
        self.assertEqual(self.appointment.get_service_img_url(), "")
        self.assertEqual(self.appointment.get_staff_member_name(), self.staff_member1.get_staff_member_name())
        self.assertTrue(self.appointment.service_is_paid())
        self.assertFalse(self.appointment.is_paid())

    def test_conversion_to_dict(self):
        response = {
            'id': 1,
            'client_name': self.client_.first_name + ' ' + self.client_.last_name,
            'client_email': self.client_.email,
            'start_time': '1900-01-01 09:00',
            'end_time': '1900-01-01 10:00',
            'service_name': self.expected_service_name,
            'address': self.address,
            'want_reminder': False,
            'additional_info': None,
            'paid': False,
            'amount_to_pay': self.expected_service_price,
        }
        actual_response = self.appointment.to_dict()
        actual_response.pop('id_request', None)
        self.assertEqual(actual_response, response)


class AppointmentValidDateTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.weekday = "Monday"  # Example weekday
        self.weekday_num = get_weekday_num(self.weekday)
        self.wh = WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=self.weekday_num,
                                              start_time=time(9, 0), end_time=time(17, 0))
        self.appt_date = timezone.now().date() + timedelta(days=(self.weekday_num - timezone.now().weekday()) % 7)
        self.start_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        self.current_appointment_id = None

    def tearDown(self):
        self.wh.delete()
        return super().tearDown()

    def test_staff_member_works_on_given_day(self):
        is_valid, message = Appointment.is_valid_date(self.appt_date, self.start_time, self.staff_member1,
                                                      self.current_appointment_id, self.weekday)
        self.assertTrue(is_valid)

    def test_staff_member_does_not_work_on_given_day(self):
        non_working_day = "Sunday"
        non_working_day_num = get_weekday_num(non_working_day)
        appt_date = self.appt_date + timedelta(days=(non_working_day_num - self.weekday_num) % 7)
        is_valid, message = Appointment.is_valid_date(appt_date, self.start_time, self.staff_member1,
                                                      self.current_appointment_id, non_working_day)
        self.assertFalse(is_valid)
        self.assertIn("does not work on this day", message)

    def test_start_time_outside_working_hours(self):
        early_start_time = timezone.now().replace(hour=8, minute=0)  # Before working hours
        is_valid, message = Appointment.is_valid_date(self.appt_date, early_start_time, self.staff_member1,
                                                      self.current_appointment_id, self.weekday)
        self.assertFalse(is_valid)
        self.assertIn("outside of", message)

    def test_staff_member_has_day_off(self):
        DayOff.objects.create(staff_member=self.staff_member1, start_date=self.appt_date, end_date=self.appt_date)
        is_valid, message = Appointment.is_valid_date(self.appt_date, self.start_time, self.staff_member1,
                                                      self.current_appointment_id, self.weekday)
        self.assertFalse(is_valid)
        self.assertIn("has a day off on this date", message)


class AppointmentValidationTestCase(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.ar = self.create_appointment_request_(service=self.service2, staff_member=self.staff_member2,
                                                   date_=self.tomorrow)
        self.appointment = self.create_appt_for_sm2(appointment_request=self.ar)
        self.client_ = self.users['client1']
        return super().setUp()

    def tearDown(self):
        self.appointment.delete()
        return super().tearDown()

    def test_invalid_phone_number(self):
        """Test that an appointment cannot be created with an invalid phone number."""
        self.appointment.phone = "1234"  # Invalid phone number
        with self.assertRaises(ValidationError):
            self.appointment.full_clean()

    def test_set_paid_status(self):
        """Test if an appointment's paid status can be set."""
        appointment = deepcopy(self.appointment)
        appointment.set_appointment_paid_status(True)
        self.assertTrue(appointment.is_paid())
        appointment.set_appointment_paid_status(False)
        self.assertFalse(appointment.is_paid())

    def test_save_with_down_payment(self):
        """Test if an appointment can be saved with a down payment."""
        ar = self.create_appointment_request_(service=self.service2, staff_member=self.staff_member2,
                                              date_=self.tomorrow)
        appointment = self.create_appt_for_sm2(appointment_request=ar)
        ar.payment_type = 'down'
        ar.save()
        appointment.save()
        self.assertEqual(appointment.get_service_down_payment(), self.service2.get_down_payment())

    def test_creation_without_appointment_request(self):
        """Test that an appointment cannot be created without an appointment request."""
        with self.assertRaises(ValidationError):  # Assuming model validation prevents this
            Appointment.objects.create(client=self.client_)

    def test_creation_without_client(self):
        """Test that an appointment can be created without a client."""
        ar = self.create_appointment_request_(service=self.service2, staff_member=self.staff_member2,
                                              date_=self.tomorrow)
        appt = Appointment.objects.create(appointment_request=ar)
        self.assertIsNone(appt.client)

    def test_creation_without_required_fields(self):
        """Test that an appointment cannot be created without the required fields."""
        with self.assertRaises(ValidationError):
            Appointment.objects.create()

    def test_get_staff_member_name_without_staff_member(self):
        """Test if you get_staff_member_name method returns an empty string when no staff member is associated."""
        ar = self.create_appointment_request_(service=self.service2, staff_member=self.staff_member2,
                                              date_=self.tomorrow)
        appointment = self.create_appt_for_sm2(appointment_request=ar)
        appointment.appointment_request.staff_member = None
        appointment.appointment_request.save()
        self.assertEqual(appointment.get_staff_member_name(), "")

    def test_rescheduling(self):
        """Simulate appointment rescheduling by changing the appointment date and times."""
        ar = self.create_appointment_request_(service=self.service2, staff_member=self.staff_member2,
                                              date_=self.tomorrow)
        appointment = self.create_appt_for_sm2(appointment_request=ar)
        new_date = ar.date + timedelta(days=1)
        new_start_time = time(10, 0)
        new_end_time = time(11, 0)
        ar.date = new_date
        ar.start_time = new_start_time
        ar.end_time = new_end_time
        ar.save()

        self.assertEqual(appointment.get_date(), new_date)
        self.assertEqual(appointment.get_start_time().time(), new_start_time)
        self.assertEqual(appointment.get_end_time().time(), new_end_time)
