# test_services.py
# Path: appointment/tests/test_services.py

import datetime
import json
from _decimal import Decimal
from datetime import date, time, timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, override_settings
from django.test.client import RequestFactory
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy as _

from appointment.forms import StaffDaysOffForm
from appointment.services import (
    create_staff_member_service, email_change_verification_service, fetch_user_appointments, get_available_slots,
    get_available_slots_for_staff, get_finish_button_text, handle_day_off_form, handle_entity_management_request,
    handle_service_management_request, handle_working_hours_form, prepare_appointment_display_data,
    prepare_user_profile_data, save_appointment, save_appt_date_time, update_personal_info_service
)
from appointment.tests.base.base_test import BaseTest
from appointment.tests.mixins.base_mixin import (
    ConfigMixin)
from appointment.utils.date_time import convert_str_to_time, get_ar_end_time
from appointment.utils.db_helpers import Config, DayOff, EmailVerificationCode, StaffMember, WorkingHours
from appointment.views import get_appointments_and_slots


class GetAvailableSlotsTests(BaseTest):
    """Test cases for get_available_slots"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        ar = self.create_appt_request_for_sm1(date_=self.tomorrow, start_time=time(11, 0), end_time=time(12, 0))
        self.appointment = self.create_appt_for_sm1(appointment_request=ar)

    @override_settings(DEBUG=True)
    def tearDown(self):
        Config.objects.all().delete()
        super().tearDown()
        cache.clear()

    def test_get_available_slots(self):
        slots = get_available_slots(self.tomorrow, [self.appointment])
        self.assertIsInstance(slots, list)
        self.assertNotIn('11:00 AM', slots)

    def test_get_available_slots_with_config(self):
        Config.objects.create(
                lead_time=datetime.time(11, 0),
                finish_time=datetime.time(15, 0),
                slot_duration=30,
                appointment_buffer_time=2.0
        )
        slots = get_available_slots(self.tomorrow, [self.appointment])
        self.assertIsInstance(slots, list)
        self.assertNotIn('11:00 AM', slots)


class FetchUserAppointmentsTests(BaseTest):
    """Test suite for the `fetch_user_appointments` service function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # Create some appointments for testing purposes
        self.appointment_for_user1 = self.create_appt_for_sm1()
        self.appointment_for_user2 = self.create_appt_for_sm2()

    def test_fetch_appointments_for_superuser(self):
        """Test that a superuser can fetch all appointments."""
        # Make user1 a superuser
        jack = self.users['superuser']
        jack.is_superuser = True
        jack.save()

        # Fetch appointments for superuser
        appointments = fetch_user_appointments(jack)

        # Assert that the superuser sees all appointments
        self.assertIn(self.appointment_for_user1, appointments,
                      "Superuser should be able to see all appointments, including those created for user1.")
        self.assertIn(self.appointment_for_user2, appointments,
                      "Superuser should be able to see all appointments, including those created for user2.")

    def test_fetch_appointments_for_staff_member(self):
        """Test that a staff member can only fetch their own appointments."""
        # Fetch appointments for staff member (user1 in this case)
        daniel = self.users['staff1']
        daniel.is_staff = True
        daniel.save()

        appointments = fetch_user_appointments(daniel)

        # Assert that the staff member sees only their own appointments
        self.assertIn(self.appointment_for_user1, appointments,
                      "Staff members should only see appointments linked to them. User1's appointment is missing.")
        self.assertNotIn(self.appointment_for_user2, appointments,
                         "Staff members should not see appointments not linked to them. User2's appointment was found.")

    def test_fetch_appointments_for_regular_user(self):
        """Test that a regular user (not a user with staff member instance or staff) cannot fetch appointments."""
        # Fetching appointments for a regular user (client1 in this case) should raise ValueError
        georges = self.users['client1']
        with self.assertRaises(ValueError,
                               msg="Regular users without staff or superuser status should raise a ValueError."):
            fetch_user_appointments(georges)

    def test_fetch_appointments_for_staff_user_without_staff_member_instance(self):
        """Test that a staff user without a staff member instance gets an empty list of appointments."""
        janet = self.create_user_()
        janet.is_staff = True
        janet.save()

        appointments = fetch_user_appointments(janet)
        # Check that the returned value is an empty list
        self.assertEqual(appointments, [], "Expected an empty list for a staff user without a staff member instance.")


class PrepareAppointmentDisplayDataTests(BaseTest):
    """Test suite for the `prepare_appointment_display_data` service function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()

        # Create an appointment for testing purposes
        self.appointment = self.create_appt_for_sm1()
        self.daniel = self.users['staff1']
        self.samantha = self.users['staff2']
        self.georges = self.users['client1']

    def test_non_existent_appointment(self):
        """Test that the function handles a non-existent appointment correctly."""
        # Fetch data for a non-existent appointment
        x, y, error_message, status_code = prepare_appointment_display_data(self.samantha, 9999)

        self.assertEqual(status_code, 404, "Expected status code to be 404 for a non-existent appointment.")
        self.assertEqual(error_message, _("Appointment does not exist."))

    def test_unauthorized_user(self):
        """A user who doesn't own the appointment cannot view it."""
        # Fetch data for an appointment that user2 doesn't own
        x, y, error_message, status_code = prepare_appointment_display_data(self.georges, self.appointment.id)

        self.assertEqual(status_code, 403, "Expected status code to be 403 for an unauthorized user.")
        self.assertEqual(error_message, _("You are not authorized to view this appointment."))

    def test_authorized_user(self):
        """An authorized user can view the appointment."""
        # Fetch data for the appointment owned by user1
        appointment, page_title, error_message, status_code = prepare_appointment_display_data(self.daniel,
                                                                                               self.appointment.id)

        self.assertEqual(status_code, 200, "Expected status code to be 200 for an authorized user.")
        self.assertIsNone(error_message)
        self.assertEqual(appointment, self.appointment)
        self.assertTrue(self.georges.first_name in page_title)

    def test_superuser(self):
        """A superuser can view any appointment and sees the staff member name in the title."""

        jack = self.users['superuser']
        jack.is_superuser = True
        jack.save()

        # Fetch data for the appointment as a superuser
        appointment, page_title, error_message, status_code = prepare_appointment_display_data(jack,
                                                                                               self.appointment.id)

        self.assertEqual(status_code, 200, "Expected status code to be 200 for a superuser.")
        self.assertIsNone(error_message)
        self.assertEqual(appointment, self.appointment)
        self.assertTrue(self.georges.first_name in page_title)
        self.assertTrue(self.daniel.first_name in page_title)


class PrepareUserProfileDataTests(BaseTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.jack = self.users['superuser']
        self.jack.is_superuser = True
        self.jack.save()

    def test_superuser_without_staff_user_id(self):
        """A superuser without a staff_user_id should see the staff list page."""
        data = prepare_user_profile_data(self.jack, None)
        self.assertFalse(data['error'])
        self.assertEqual(data['template'], 'administration/staff_list.html')
        self.assertIn('btn_staff_me', data['extra_context'])

    def test_regular_user_with_mismatched_staff_user_id(self):
        """A regular user cannot view another user's profile."""
        data = prepare_user_profile_data(self.jack, self.users['client2'].pk)
        self.assertTrue(data['error'])
        self.assertEqual(data['status_code'], 403)

    def test_superuser_with_non_existent_staff_user_id(self):
        """A superuser with a non-existent staff_user_id cannot view the staff's profile."""
        data = prepare_user_profile_data(self.jack, 9999)
        self.assertTrue(data['error'])
        self.assertEqual(data['status_code'], 403)

    def test_regular_user_with_matching_staff_user_id(self):
        """A regular user can view their own profile."""
        data = prepare_user_profile_data(self.users['staff1'], self.staff_member1.pk)
        self.assertFalse(data['error'])
        self.assertEqual(data['template'], 'administration/user_profile.html')
        self.assertIn('user', data['extra_context'])
        self.assertEqual(data['extra_context']['user'], self.users['staff1'])

    def test_regular_user_with_non_existent_staff_user_id(self):
        """A regular user with a non-existent staff_user_id cannot view their profile."""
        data = prepare_user_profile_data(self.jack, 9999)
        self.assertTrue(data['error'])
        self.assertEqual(data['status_code'], 403)


class HandleEntityManagementRequestTests(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.factory = RequestFactory()

        # Setup request object
        self.request = self.factory.post('/')
        self.request.user = self.staff_member1.user

    def tearDown(self):
        WorkingHours.objects.all().delete()
        super().tearDown()

    def test_staff_member_none(self):
        """A day off cannot be created for a staff member that doesn't exist."""
        response = handle_entity_management_request(self.request, None, 'day_off')
        self.assertEqual(response.status_code, 403)

    def test_day_off_get(self):
        """Test if a day off can be fetched."""
        self.request.method = 'GET'
        response = handle_entity_management_request(self.request, self.staff_member1, 'day_off')
        self.assertEqual(response.status_code, 200)

    def test_working_hours_get(self):
        """Test if working hours can be fetched."""
        self.request.method = 'GET'
        response = handle_entity_management_request(request=self.request, staff_member=self.staff_member1,
                                                    entity_type='working_hours', staff_user_id=self.staff_member1.id)
        self.assertEqual(response.status_code, 200)

    def test_day_off_post_conflicting_dates(self):
        """A day off cannot be created if the staff member already has a day off on the same dates."""
        DayOff.objects.create(staff_member=self.staff_member1, start_date='2022-01-01', end_date='2022-01-07')
        self.request.method = 'POST'
        self.request.POST = {
            'start_date': '2022-01-01',
            'end_date': '2022-01-07'
        }
        response = handle_entity_management_request(self.request, self.staff_member1, 'day_off')
        self.assertEqual(response.status_code, 400)

    def test_day_off_post_non_conflicting_dates(self):
        """A day off can be created if the staff member doesn't have a day off on the same dates."""
        self.request.method = 'POST'
        self.request.POST = {
            'start_date': '2022-01-08',
            'end_date': '2022-01-14'
        }
        response = handle_entity_management_request(self.request, self.staff_member1, 'day_off')
        content = json.loads(response.content)
        self.assertEqual(content['success'], True)

    def test_working_hours_post(self):
        """Test if working hours can be created with valid data."""
        # Assuming handle_working_hours_form always returns a JsonResponse
        self.request.method = 'POST'
        self.request.POST = {
            'day_of_week': '2',
            'start_time': '08:00 AM',
            'end_time': '12:00 PM'
        }
        # Create a WorkingHours instance for self.staff_member1
        working_hours_instance = WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=1,
                                                             start_time=datetime.time(8, 0),
                                                             end_time=datetime.time(12, 0))

        # Now, pass this instance to your function
        response = handle_entity_management_request(request=self.request, staff_member=self.staff_member1,
                                                    entity_type='working_hours',
                                                    staff_user_id=self.staff_member1.user.id,
                                                    instance=working_hours_instance)
        content = json.loads(response.content)
        self.assertTrue(content['success'])


class HandleWorkingHoursFormTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()

    def tearDown(self):
        WorkingHours.objects.all().delete()
        super().tearDown()

    def test_add_working_hours(self):
        """Test if working hours can be added."""
        response = handle_working_hours_form(self.staff_member1, 1, '09:00 AM', '05:00 PM', True)
        self.assertEqual(response.status_code, 200)

    def test_update_working_hours(self):
        """Test if working hours can be updated."""
        wh = WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=2, start_time='09:00',
                                         end_time='17:00')
        response = handle_working_hours_form(self.staff_member1, 3, '10:00 AM', '06:00 PM', False, wh_id=wh.id)
        self.assertEqual(response.status_code, 200)

    def test_invalid_data(self):
        """If the form is invalid, the function should return a JsonResponse with the appropriate error message."""
        response = handle_working_hours_form(None, 1, '09:00 AM', '05:00 PM', True)  # Missing staff_member
        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.getvalue())['success'])

    def test_invalid_time(self):
        """If the start time is after the end time, the function should return a JsonResponse with the
        appropriate error"""
        response = handle_working_hours_form(self.staff_member1, 1, '05:00 PM', '09:00 AM', True)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.getvalue())
        self.assertEqual(content['errorCode'], 5)
        self.assertFalse(content['success'])

    def test_working_hours_conflict(self):
        """A staff member cannot have two working hours on the same day."""
        WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=4, start_time='09:00',
                                    end_time='17:00')
        response = handle_working_hours_form(self.staff_member1, 4, '10:00 AM', '06:00 PM', True)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.getvalue())
        self.assertEqual(content['errorCode'], 11)
        self.assertFalse(content['success'])

    def test_invalid_working_hours_id(self):
        """If the working hours ID is invalid, the function should return a JsonResponse with the appropriate error"""
        response = handle_working_hours_form(self.staff_member1, 1, '10:00 AM', '06:00 PM', False, wh_id=9999)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.getvalue())
        self.assertEqual(content['success'], False)
        self.assertEqual(content['errorCode'], 10)

    def test_no_working_hours_id(self):
        """If the working hours ID is not provided, the function should return a JsonResponse with the
        appropriate error"""
        response = handle_working_hours_form(self.staff_member1, 1, '10:00 AM', '06:00 PM', False)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.getvalue())
        self.assertEqual(content['success'], False)
        self.assertEqual(content['errorCode'], 5)


class HandleDayOffFormTest(BaseTest):

    def setUp(self):
        super().setUp()

    def test_valid_day_off_form(self):
        """Test if a valid day off form is handled correctly."""
        data = {
            'start_date': '2023-01-01',
            'end_date': '2023-01-05'
        }
        day_off_form = StaffDaysOffForm(data)
        response = handle_day_off_form(day_off_form, self.staff_member1)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertTrue(content['success'])

    def test_invalid_day_off_form(self):
        """A day off form with invalid data should return a JsonResponse with the appropriate error message."""
        data = {
            'start_date': '2023-01-01',
            'end_date': ''  # Missing end_date
        }
        day_off_form = StaffDaysOffForm(data)
        response = handle_day_off_form(day_off_form, self.staff_member1)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content)
        self.assertFalse(content['success'])


class SaveAppointmentTests(BaseTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()

        # Assuming self.create_default_appointment creates an appointment with default values
        self.appt = self.create_appt_for_sm1()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    def test_save_appointment(self):
        """Test if an appointment can be saved with valid data."""
        client_name = "Teal'c of Chulak"
        client_email = "tealc@chulak.com"
        start_time_str = "10:00 AM"
        phone_number = "+1234567890"
        client_address = "123 Stargate Command, Cheyenne Mountain"
        service_id = self.service2.id
        staff_member_id = self.staff_member2.id

        # Call the function
        updated_appt = save_appointment(self.appt, client_name, client_email, start_time_str, phone_number,
                                        client_address, service_id, self.request, staff_member_id)

        # Check client details
        self.assertEqual(updated_appt.client.get_full_name(), client_name)
        self.assertEqual(updated_appt.client.email, client_email)

        # Check appointment request details
        self.assertEqual(updated_appt.appointment_request.service.id, service_id)
        self.assertEqual(updated_appt.appointment_request.start_time, convert_str_to_time(start_time_str))
        end_time = get_ar_end_time(convert_str_to_time(start_time_str), self.service2.duration)
        self.assertEqual(updated_appt.appointment_request.end_time, end_time)

        # Check appointment details
        self.assertEqual(updated_appt.phone, phone_number)
        self.assertEqual(updated_appt.address, client_address)


class SaveApptDateTimeTests(BaseTest):

    def setUp(self):
        super().setUp()

        # Assuming create_appt_for_sm1 creates an appointment for user1 with default values
        self.appt = self.create_appt_for_sm1()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    def test_save_appt_date_time(self):
        """Test if an appointment's date and time can be updated."""
        # Given new appointment date and time details
        appt_start_time_str = "10:00:00.000000Z"
        appt_date_str = (datetime.datetime.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        appt_id = self.appt.id

        # Call the function
        updated_appt = save_appt_date_time(appt_start_time_str, appt_date_str, appt_id, self.request)

        # Convert given date and time strings to appropriate formats
        time_format = "%H:%M:%S.%fZ"
        appt_start_time_obj = datetime.datetime.strptime(appt_start_time_str, time_format).time()
        appt_date_obj = datetime.datetime.strptime(appt_date_str, "%Y-%m-%d").date()

        # Calculate the expected end time
        service = updated_appt.get_service()
        end_time_obj = get_ar_end_time(appt_start_time_obj, service.duration)

        # Validate the updated appointment details
        self.assertEqual(updated_appt.appointment_request.date, appt_date_obj)
        self.assertEqual(updated_appt.appointment_request.start_time, appt_start_time_obj)
        self.assertEqual(updated_appt.appointment_request.end_time, end_time_obj)


def get_next_weekday(d, weekday):
    """
    Get the date of the next weekday from the given date.
    This function uses python's weekday format, where Monday is 0, and Sunday is 6.
    Remember that in my implementation for work days, I had to use a custom one where Monday is 1, and Sunday is 0.
    So in the setup, I will use my format to create day-offs, working hours, etc. But when calling this function, I will
    use the python format.
    """
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    next_day = d + datetime.timedelta(days_ahead)
    return next_day


class GetAvailableSlotsForStaffTests(BaseTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        cache.clear()
        self.today = datetime.date.today()
        # Staff member1 works only on Mondays and Wednesday (day_of_week: 1, 3)
        self.wh1 = WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=1,
                                               start_time=datetime.time(9, 0), end_time=datetime.time(17, 0))
        self.wh2 = WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=3,
                                               start_time=datetime.time(9, 0), end_time=datetime.time(17, 0))
        # But decides to take a day off next Monday
        self.next_monday = get_next_weekday(self.today, 0)
        self.next_tuesday = get_next_weekday(self.today, 1)
        self.next_wednesday = get_next_weekday(self.today, 2)
        self.next_thursday = get_next_weekday(self.today, 3)
        self.next_friday = get_next_weekday(self.today, 4)
        self.next_saturday = get_next_weekday(self.today, 5)
        self.next_sunday = get_next_weekday(self.today, 6)
        DayOff.objects.create(staff_member=self.staff_member1, start_date=self.next_monday, end_date=self.next_monday)
        Config.objects.create(slot_duration=60, lead_time=datetime.time(9, 0), finish_time=datetime.time(17, 0),
                              appointment_buffer_time=0)

    @override_settings(DEBUG=True)
    def tearDown(self):
        WorkingHours.objects.all().delete()
        DayOff.objects.all().delete()
        Config.objects.all().delete()
        cache.clear()
        super().tearDown()

    def test_day_off(self):
        """Test if a day off is handled correctly when getting available slots."""
        # Ask for slots for it, and it should return an empty list since next Monday is a day off
        slots = get_available_slots_for_staff(self.next_monday, self.staff_member1)
        self.assertEqual(slots, [])

    def test_staff_does_not_work(self):
        """Test if a staff member who doesn't work on a given day is handled correctly when getting available slots."""
        # For next week, the staff member works only on Monday and Wednesday, but puts a day off on Monday
        # So the staff member should not have any available slots except for Wednesday, which is day #2 (python weekday)
        slots = get_available_slots_for_staff(self.next_monday, self.staff_member1)
        self.assertEqual(slots, [])
        slots = get_available_slots_for_staff(self.next_tuesday, self.staff_member1)
        self.assertEqual(slots, [])
        slots = get_available_slots_for_staff(self.next_thursday, self.staff_member1)
        self.assertEqual(slots, [])
        slots = get_available_slots_for_staff(self.next_friday, self.staff_member1)
        self.assertEqual(slots, [])
        slots = get_available_slots_for_staff(self.next_saturday, self.staff_member1)
        self.assertEqual(slots, [])
        slots = get_available_slots_for_staff(self.next_sunday, self.staff_member1)
        self.assertEqual(slots, [])

    def test_available_slots(self):
        """Test if available slots are returned correctly."""
        # On a Wednesday, the staff member should have slots from 9 AM to 5 PM
        slots = get_available_slots_for_staff(self.next_wednesday, self.staff_member1)
        expected_slots = [
            datetime.datetime(self.next_wednesday.year, self.next_wednesday.month, self.next_wednesday.day, hour) for
            hour in range(9, 17)]
        self.assertEqual(slots, expected_slots)

    def test_booked_slots(self):
        """On a given day, if a staff member has an appointment, that time slot should not be available."""
        # Let's book a slot for the staff member on next Wednesday
        start_time = datetime.time(10, 0)
        end_time = datetime.time(11, 0)

        # Create an appointment request for that time
        appt_request = self.create_appointment_request_(service=self.service1, staff_member=self.staff_member1,
                                                        date_=self.next_wednesday, start_time=start_time,
                                                        end_time=end_time)
        # Create an appointment using that request
        self.create_appointment_(user=self.users['client1'], appointment_request=appt_request)

        # Now, the staff member should not have that slot available
        slots = get_available_slots_for_staff(self.next_wednesday, self.staff_member1)
        expected_slots = [
            datetime.datetime(self.next_wednesday.year, self.next_wednesday.month, self.next_wednesday.day, hour, 0) for
            hour in range(9, 17) if hour != 10]
        self.assertEqual(slots, expected_slots)

    @override_settings(DEBUG=True)
    def test_no_working_hours(self):
        """If a staff member doesn't have working hours on a given day, no slots should be available."""
        # Let's ask for slots on a Thursday, which the staff member doesn't work
        # Let's remove the config object also since it may contain default working days
        Config.objects.all().delete()
        # Now no slots should be available
        slots = get_available_slots_for_staff(self.next_thursday, self.staff_member1)
        self.assertEqual(slots, [])


class UpdatePersonalInfoServiceTest(BaseTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.daniel = self.users['staff1']
        self.post_data_valid = {
            'first_name': 'UpdatedName',
            'last_name': 'UpdatedLastName',
            'email': self.daniel.email
        }

    def test_update_name(self):
        """Test if the user's name can be updated."""
        user, is_valid, error_message = update_personal_info_service(self.staff_member1.user.id, self.post_data_valid,
                                                                     self.daniel)
        self.assertTrue(is_valid)
        self.assertIsNone(error_message)
        self.assertEqual(user.first_name, 'UpdatedName')
        self.assertEqual(user.last_name, 'UpdatedLastName')

    def test_update_invalid_user_id(self):
        """Updating a user that doesn't exist should return an error message."""
        user, is_valid, error_message = update_personal_info_service(9999, self.post_data_valid,
                                                                     self.daniel)  # Assuming 9999 is an invalid user ID

        self.assertFalse(is_valid)
        self.assertEqual(error_message, _("User not found."))
        self.assertIsNone(user)

    def test_invalid_form(self):
        """Updating a user with invalid form data should return an error message."""
        user, is_valid, error_message = update_personal_info_service(self.staff_member1.user.id, {}, self.daniel)
        self.assertFalse(is_valid)
        self.assertEqual(error_message, _("Empty fields are not allowed."))

    def test_invalid_form_(self):
        """Updating a user with invalid form data should return an error message."""
        # remove email in post_data
        del self.post_data_valid['email']
        user, is_valid, error_message = update_personal_info_service(self.staff_member1.user.id, self.post_data_valid,
                                                                     self.daniel)
        self.assertFalse(is_valid)
        self.assertEqual(error_message, "email: This field is required.")


class EmailChangeVerificationServiceTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.georges = self.users['client1']
        self.valid_code = EmailVerificationCode.generate_code(self.georges)
        self.invalid_code = "INVALID_CODE456"

        self.old_email = self.georges.email
        self.new_email = "georges.hammond@django-appointment.com"

    def test_valid_code_and_email(self):
        """Test if a valid code and email can be verified."""
        is_verified = email_change_verification_service(self.valid_code, self.new_email, self.old_email)

        self.assertTrue(is_verified)
        self.georges.refresh_from_db()  # Refresh the user object to get the updated email
        self.assertEqual(self.georges.email, self.new_email)

    def test_invalid_code(self):
        """If the code is invalid, the email should not be updated."""
        is_verified = email_change_verification_service(self.invalid_code, self.new_email, self.old_email)

        self.assertFalse(is_verified)
        self.georges.refresh_from_db()
        self.assertEqual(self.georges.email, self.old_email)  # Email should not change

    def test_valid_code_no_user(self):
        """If the code is valid but the user doesn't exist, the email should not be updated."""
        is_verified = email_change_verification_service(self.valid_code, self.new_email, "nonexistent@gmail.com")

        self.assertFalse(is_verified)

    def test_code_doesnt_match_users_code(self):
        """If the code is valid but doesn't match the user's code, the email should not be updated."""
        # Using valid code but for another user
        is_verified = email_change_verification_service(self.valid_code, self.new_email,
                                                        "g.hammond@django-appointment.com")

        self.assertFalse(is_verified)


class CreateStaffMemberServiceTest(BaseTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

        # Setup request object
        self.request = self.factory.post('/')

    def test_valid_data(self):
        """Test if a staff member can be created with valid data."""
        post_data = {
            'first_name': 'Catherine',
            'last_name': 'Langford',
            'email': 'catherine.langford@django-appointment.com'
        }

        user, success, error_message = create_staff_member_service(post_data, self.request)

        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Catherine')
        self.assertEqual(user.last_name, 'Langford')
        self.assertEqual(user.email, 'catherine.langford@django-appointment.com')
        self.assertTrue(StaffMember.objects.filter(user=user).exists())

    def test_invalid_data(self):
        """Empty fields should not be allowed when creating a staff member."""
        post_data = {
            'first_name': '',  # Missing first name
            'last_name': 'Langford',
            'email': 'catherine.langford@django-appointment.com'
        }
        user, success, error_message = create_staff_member_service(post_data, self.request)

        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIsNotNone(error_message)

    def test_email_already_exists(self):
        """If the email already exists, the staff member should not be created."""
        self.create_user_()
        post_data = {
            'first_name': 'Janet',
            'last_name': 'Fraiser',
            'email': 'janet.fraiser@django-appointment.com'  # Using an email that already exists
        }
        user, success, error_message = create_staff_member_service(post_data, self.request)

        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertEqual(error_message, "email: This email is already taken.")

    @patch('appointment.services.send_reset_link_to_staff_member')
    def test_send_reset_link_to_new_staff_member(self, mock_send_reset_link):
        """Test if a reset password link is sent to a new staff member."""
        post_data = {
            'first_name': 'Janet',
            'last_name': 'Fraiser',
            'email': 'janet.fraiser@django-appointment.com'
        }
        user, success, _ = create_staff_member_service(post_data, self.request)
        self.assertTrue(success)
        self.assertIsNotNone(user)

        # Check that the mock_send_reset_link function was called once
        mock_send_reset_link.assert_called_once_with(user, self.request, user.email)


class HandleServiceManagementRequestTest(BaseTest):

    def setUp(self):
        super().setUp()

    def test_create_new_service(self):
        """Test if a new service can be created with valid data."""
        post_data = {
            'name': "Goa'uld extraction",
            'duration': '1:00:00',
            'price': '10000',
            'currency': 'USD',
            'down_payment': '5000',
        }
        service, success, message = handle_service_management_request(post_data)
        self.assertTrue(success)
        self.assertIsNotNone(service)
        self.assertEqual(service.name, "Goa'uld extraction")
        self.assertEqual(service.duration, datetime.timedelta(hours=1))
        self.assertEqual(service.price, Decimal('10000'))
        self.assertEqual(service.down_payment, Decimal('5000'))
        self.assertEqual(service.currency, 'USD')

    def test_update_existing_service(self):
        """Test if an existing service can be updated with valid data."""
        existing_service = self.create_service_()
        post_data = {
            'name': 'Quantum Mirror Repair',
            'duration': '2:00:00',
            'price': '15000',
            'down_payment': '7500',
            'currency': 'EUR'
        }
        service, success, message = handle_service_management_request(post_data, service_id=existing_service.id)

        self.assertTrue(success)
        self.assertIsNotNone(service)
        self.assertEqual(service.name, 'Quantum Mirror Repair')
        self.assertEqual(service.duration, datetime.timedelta(hours=2))
        self.assertEqual(service.price, Decimal('15000'))
        self.assertEqual(service.currency, 'EUR')

    def test_invalid_data(self):
        """Empty fields should not be allowed when creating a service."""
        post_data = {
            'name': '',  # Missing name
            'duration': '1:00:00',
            'price': '100',
            'currency': 'USD',
            'down_payment': '50',
        }
        service, success, message = handle_service_management_request(post_data, service_id=self.service1.id)

        self.assertFalse(success)
        self.assertIsNone(service)
        self.assertEqual(message, "name: This field is required.")

    def test_service_not_found(self):
        """If the service ID is invalid, the service should not be updated."""
        post_data = {
            'name': 'DHD maintenance',
            'duration': '1:00:00',
            'price': '10000',
            'currency': 'USD'
        }
        service, success, message = handle_service_management_request(post_data, service_id=9999)  # Invalid service_id

        self.assertFalse(success)
        self.assertIsNone(service)
        self.assertIn(str(_("Service matching query does not exist")), str(message))


class GetFinishButtonTextTests(BaseTest):
    """Test cases for get_finish_button_text"""

    def test_get_finish_button_text_free_service(self):
        button_text = get_finish_button_text(self.service1)
        self.assertEqual(button_text, _("Finish"))

    def test_get_finish_button_text_paid_service(self):
        with patch('appointment.services.APPOINTMENT_PAYMENT_URL', 'https://payment.com'):
            button_text = get_finish_button_text(self.service1)
            self.assertEqual(button_text, _("Pay Now"))


class SlotAvailabilityTest(BaseTest, ConfigMixin):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.service = self.create_service_(duration=timedelta(hours=2))
        self.config = self.create_config_(lead_time=time(11, 0), finish_time=time(15, 0), slot_duration=120)
        self.test_date = date.today() + timedelta(days=1)  # Use tomorrow's date for the tests

    @override_settings(DEBUG=True)
    def tearDown(self):
        self.service.delete()
        cache.clear()

    def test_slot_availability_without_appointments(self):
        """Test if the available slots are correct when there are no appointments."""
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['11:00 AM', '01:00 PM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_first_slot_booked(self):
        """Available slots (total 2) should be one when the first slot is booked."""
        self.ar = self.create_appt_request_for_sm1(service=self.service, date_=self.test_date, start_time=time(11, 0),
                                                   end_time=time(13, 0))
        self.create_appt_for_sm1(appointment_request=self.ar)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['01:00 PM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_second_slot_booked(self):
        """Available slots (total 2) should be one when the second slot is booked."""
        self.ar = self.create_appt_request_for_sm1(service=self.service, date_=self.test_date, start_time=time(13, 0),
                                                   end_time=time(15, 0))
        self.create_appt_for_sm1(appointment_request=self.ar)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = ['11:00 AM']
        self.assertEqual(available_slots, expected_slots)

    def test_slot_availability_with_both_slots_booked(self):
        """Available slots (total 2) should be zero when both slots are booked."""
        self.ar1 = self.create_appt_request_for_sm1(service=self.service, date_=self.test_date, start_time=time(11, 0),
                                                    end_time=time(13, 0))
        self.ar2 = self.create_appt_request_for_sm1(service=self.service, date_=self.test_date, start_time=time(13, 0),
                                                    end_time=time(15, 0))
        self.create_appt_for_sm1(appointment_request=self.ar1)
        self.create_appt_for_sm1(appointment_request=self.ar2)
        _, available_slots = get_appointments_and_slots(self.test_date, self.service)
        expected_slots = []
        self.assertEqual(available_slots, expected_slots)
