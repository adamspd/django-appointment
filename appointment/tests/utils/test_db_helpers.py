# test_db_helpers.py
# Path: appointment/tests/utils/test_db_helpers.py

import datetime
from unittest.mock import patch, ANY

from django.apps import apps
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase
from django.urls import reverse

from appointment.models import DayOff, PaymentInfo
from appointment.tests.base.base_test import BaseTest
from appointment.utils.date_time import get_current_year
from appointment.utils.db_helpers import (calculate_slots, check_day_off_for_staff, create_and_save_appointment,
                                          create_payment_info_and_get_url, exclude_booked_slots,
                                          day_off_exists_for_date_range, get_all_staff_members,
                                          get_all_appointments, Config, get_appointment_buffer_time,
                                          get_appointment_by_id, get_appointment_finish_time,
                                          get_appointment_lead_time, get_appointment_slot_duration,
                                          get_appointments_for_date_and_time, get_config,
                                          get_day_off_by_id, WorkingHours, get_non_working_days_for_staff,
                                          get_staff_member_appointment_list,
                                          get_weekday_num_from_date, get_staff_member_start_time,
                                          get_staff_member_end_time, get_staff_member_buffer_time,
                                          get_staff_member_slot_duration, get_user_by_email, get_user_model,
                                          get_staff_member_from_user_id_or_logged_in,
                                          get_staff_member_by_user_id, working_hours_exist, is_working_day,
                                          get_working_hours_for_staff_and_day,
                                          get_working_hours_by_id, get_website_name, get_times_from_config,
                                          create_new_user, generate_unique_username_from_email, parse_name,
                                          create_user_with_email, create_user_with_username)


class TestCalculateSlots(TestCase):
    def setUp(self):
        self.start_time = datetime.datetime(2023, 10, 8, 8, 0)  # 8:00 AM
        self.end_time = datetime.datetime(2023, 10, 8, 12, 0)  # 12:00 PM
        self.slot_duration = datetime.timedelta(hours=1)  # 1 hour
        # Buffer time should've been datetime.datetime.now() but for the purpose of the tests, we'll use a fixed time.
        self.buffer_time = datetime.datetime(2023, 10, 8, 8, 0) + self.slot_duration

    def test_multiple_slots(self):
        """Buffer time goes 1 hour after the start time, it should only return three slots.
           Start time: 08:00 AM\n
           End time: 12:00 AM\n
           Buffer time: 09:00 AM\n
           Slot duration: 1 hour\n
        """

        expected = [
            datetime.datetime(2023, 10, 8, 9, 0),
            datetime.datetime(2023, 10, 8, 10, 0),
            datetime.datetime(2023, 10, 8, 11, 0)
        ]
        result = calculate_slots(self.start_time, self.end_time, self.buffer_time, self.slot_duration)
        self.assertEqual(result, expected)

    def test_buffer_after_end_time(self):
        """Buffer time goes beyond the end time, it should not then return any slots.
           Start time: 08:00 AM\n
           End time: 09:00 AM\n
           Buffer time: 10:00 AM\n
        """
        end_time = datetime.datetime(2023, 10, 8, 9, 0)
        buffer_time = datetime.datetime(2023, 10, 8, 10, 0)

        expected = []
        result = calculate_slots(self.start_time, end_time, buffer_time, self.slot_duration)
        self.assertEqual(result, expected)

    def test_one_slot_available(self):
        """Buffer time goes beyond the end time, it should not then return any slots.
           Start time: 08:00 AM\n
           End time: 09:00 AM\n
           Buffer time: 10:00 AM\n
        """
        end_time = datetime.datetime(2023, 10, 8, 9, 0)
        buffer_time = datetime.datetime(2023, 10, 8, 7, 30)
        slot_duration = datetime.timedelta(minutes=30)

        expected = [datetime.datetime(2023, 10, 8, 8, 0), datetime.datetime(2023, 10, 8, 8, 30)]
        result = calculate_slots(self.start_time, end_time, buffer_time, slot_duration)
        self.assertEqual(result, expected)


class TestCheckDayOffForStaff(BaseTest):
    def setUp(self):
        super().setUp()  # Call the parent class setup
        # Specific setups for this test class
        self.day_off1 = DayOff.objects.create(staff_member=self.staff_member1, start_date="2023-10-08",
                                              end_date="2023-10-10")
        self.day_off2 = DayOff.objects.create(staff_member=self.staff_member2, start_date="2023-10-05",
                                              end_date="2023-10-05")

    def test_staff_member_has_day_off(self):
        # Test for a date within the range of days off for staff_member1
        self.assertTrue(check_day_off_for_staff(self.staff_member1, "2023-10-09"))

    def test_staff_member_does_not_have_day_off(self):
        # Test for a date outside the range of days off for staff_member1
        self.assertFalse(check_day_off_for_staff(self.staff_member1, "2023-10-11"))

    def test_another_staff_member_day_off(self):
        # Test for a date within the range of days off for staff_member2
        self.assertTrue(check_day_off_for_staff(self.staff_member2, "2023-10-05"))

    def test_another_staff_member_no_day_off(self):
        # Test for a date outside the range of days off for staff_member2
        self.assertFalse(check_day_off_for_staff(self.staff_member2, "2023-10-06"))


class TestCreateAndSaveAppointment(BaseTest):

    def setUp(self):
        super().setUp()  # Call the parent class setup
        # Specific setups for this test class
        self.ar = self.create_appt_request_for_sm1()

    def test_create_and_save_appointment(self):
        client_data = {
            'email': 'tester2@gmail.com',
            'name': 'Tester2',
        }
        appointment_data = {
            'phone': '123456789',
            'want_reminder': True,
            'address': '123 Main St',
            'additional_info': 'Additional Test Info'
        }

        appointment = create_and_save_appointment(self.ar, client_data, appointment_data)

        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.client.email, client_data['email'])
        self.assertEqual(appointment.phone, appointment_data['phone'])
        self.assertEqual(appointment.want_reminder, appointment_data['want_reminder'])
        self.assertEqual(appointment.address, appointment_data['address'])
        self.assertEqual(appointment.additional_info, appointment_data['additional_info'])


def get_mock_reverse(url_name, **kwargs):
    """A mocked version of the reverse function."""
    if url_name == "app:view":
        return f'/mocked-url/{kwargs["kwargs"]["object_id"]}/{kwargs["kwargs"]["id_request"]}/'
    return reverse(url_name, **kwargs)


class TestCreatePaymentInfoAndGetUrl(BaseTest):

    def setUp(self):
        super().setUp()  # Call the parent class setup
        # Specific setups for this test class
        self.ar = self.create_appt_request_for_sm1()
        self.appointment = self.create_appointment_for_user2(appointment_request=self.ar)

    def test_create_payment_info_and_get_url_string(self):
        expected_url = "https://payment.com/1/1234567890"
        with patch('appointment.utils.db_helpers.APPOINTMENT_PAYMENT_URL', expected_url):
            payment_url = create_payment_info_and_get_url(self.appointment)
            self.assertEqual(payment_url, expected_url)

    def test_create_payment_info_and_get_url_application(self):
        expected_url = "app:view"

        with patch('appointment.utils.db_helpers.APPOINTMENT_PAYMENT_URL', expected_url):
            with patch('appointment.utils.db_helpers.reverse', side_effect=get_mock_reverse):
                self.assertEqual(PaymentInfo.objects.count(), 0)

                # Call the function to create PaymentInfo and get the URL
                payment_url = create_payment_info_and_get_url(self.appointment)

                # Now, there should be one PaymentInfo object
                self.assertEqual(PaymentInfo.objects.count(), 1)

                # Fetch the newly created PaymentInfo object
                payment_info = PaymentInfo.objects.first()

                # Construct the expected mocked URL
                expected_mocked_url = f'/mocked-url/{payment_info.id}/{payment_info.get_id_request()}/'

                # Assert that the appointment in the PaymentInfo object matches the appointment we provided
                self.assertEqual(payment_info.appointment, self.appointment)
                self.assertEqual(payment_url, expected_mocked_url)


class TestExcludeBookedSlots(BaseTest):

    def setUp(self):
        super().setUp()
        self.appointment = self.create_appointment_for_user1()

        # Sample slots for testing
        self.today = datetime.date.today()

        self.slots = [
            datetime.datetime.combine(self.today, datetime.time(8, 0)),
            datetime.datetime.combine(self.today, datetime.time(9, 0)),
            datetime.datetime.combine(self.today, datetime.time(10, 0)),
            datetime.datetime.combine(self.today, datetime.time(11, 0)),
            datetime.datetime.combine(self.today, datetime.time(12, 0))
        ]
        self.slot_duration = datetime.timedelta(hours=1)

    def test_no_appointments(self):
        result = exclude_booked_slots([], self.slots, self.slot_duration)
        self.assertEqual(result, self.slots)

    def test_appointment_not_intersecting_slots(self):
        self.appointment.appointment_request.start_time = datetime.time(13, 30)
        self.appointment.appointment_request.end_time = datetime.time(14, 30)
        self.appointment.save()

        result = exclude_booked_slots([self.appointment], self.slots, self.slot_duration)
        self.assertEqual(result, self.slots)

    def test_appointment_intersecting_single_slot(self):
        self.appointment.appointment_request.start_time = datetime.time(8, 0)
        self.appointment.appointment_request.end_time = datetime.time(9, 0)
        self.appointment.save()

        result = exclude_booked_slots([self.appointment], self.slots, self.slot_duration)
        expected = [
            datetime.datetime.combine(self.today, datetime.time(9, 0)),
            datetime.datetime.combine(self.today, datetime.time(10, 0)),
            datetime.datetime.combine(self.today, datetime.time(11, 0)),
            datetime.datetime.combine(self.today, datetime.time(12, 0))
        ]
        self.assertEqual(result, expected)

    def test_multiple_overlapping_appointments(self):
        ar2 = self.create_appt_request_for_sm2(start_time=datetime.time(10, 30),
                                               end_time=datetime.time(11, 30))
        appointment2 = self.create_appointment_for_user2(appointment_request=ar2)
        appointment2.save()
        result = exclude_booked_slots([self.appointment, appointment2], self.slots, self.slot_duration)
        expected = [
            datetime.datetime.combine(self.today, datetime.time(8, 0)),
            datetime.datetime.combine(self.today, datetime.time(12, 0))
        ]
        self.assertEqual(result, expected)


class TestDayOffExistsForDateRange(BaseTest):

    def setUp(self):
        super().setUp()
        self.user = self.create_user_(email="tester@gmail.com")
        self.service = self.create_service_()
        self.staff_member = self.create_staff_member_(user=self.user, service=self.service)
        self.day_off1 = DayOff.objects.create(staff_member=self.staff_member, start_date="2023-10-08",
                                              end_date="2023-10-10")
        self.day_off2 = DayOff.objects.create(staff_member=self.staff_member, start_date="2023-10-15",
                                              end_date="2023-10-17")

    def test_day_off_exists(self):
        # Check for a date range that intersects with day_off1
        self.assertTrue(day_off_exists_for_date_range(self.staff_member, "2023-10-09", "2023-10-11"))

    def test_day_off_does_not_exist(self):
        # Check for a date range that doesn't intersect with any day off
        self.assertFalse(day_off_exists_for_date_range(self.staff_member, "2023-10-11", "2023-10-14"))

    def test_day_off_exists_but_excluded(self):
        # Check for a date range that intersects with day_off1 but exclude day_off1 from the check using its ID
        self.assertFalse(
            day_off_exists_for_date_range(self.staff_member, "2023-10-09", "2023-10-11", days_off_id=self.day_off1.id))

    def test_day_off_exists_for_other_range(self):
        # Check for a date range that intersects with day_off2
        self.assertTrue(day_off_exists_for_date_range(self.staff_member, "2023-10-16", "2023-10-18"))


class TestGetAllAppointments(BaseTest):

    def setUp(self):
        super().setUp()
        self.appointment1 = self.create_appointment_for_user1()
        self.appointment2 = self.create_appointment_for_user2()

    def test_get_all_appointments(self):
        appointments = get_all_appointments()
        self.assertEqual(len(appointments), 2)
        self.assertIn(self.appointment1, appointments)
        self.assertIn(self.appointment2, appointments)


class TestGetAllStaffMembers(BaseTest):

    def setUp(self):
        super().setUp()

    def test_get_all_staff_members(self):
        staff_members = get_all_staff_members()
        self.assertEqual(len(staff_members), 2)
        self.assertIn(self.staff_member1, staff_members)
        self.assertIn(self.staff_member2, staff_members)


class TestGetAppointmentByID(BaseTest):

    def setUp(self):
        super().setUp()
        self.appointment = self.create_appointment_for_user1()

    def test_existing_appointment(self):
        """Test fetching an existing appointment."""
        fetched_appointment = get_appointment_by_id(self.appointment.id)
        self.assertEqual(fetched_appointment, self.appointment)

    def test_non_existing_appointment(self):
        """Test attempting to fetch a non-existing appointment."""
        non_existent_id = 9999  # Assume this ID doesn't exist in the test database
        fetched_appointment = get_appointment_by_id(non_existent_id)
        self.assertIsNone(fetched_appointment)


@patch('appointment.utils.db_helpers.APPOINTMENT_BUFFER_TIME', 60)
@patch('appointment.utils.db_helpers.APPOINTMENT_LEAD_TIME', '07:00:00')
@patch('appointment.utils.db_helpers.APPOINTMENT_FINISH_TIME', '15:00:00')
@patch('appointment.utils.db_helpers.APPOINTMENT_SLOT_DURATION', 30)
@patch('appointment.utils.db_helpers.APPOINTMENT_WEBSITE_NAME', "django-appointment-website")
class TestGetAppointmentConfigTimes(TestCase):
    def test_no_config_object(self):
        """Test when there's no Config object in the database."""
        self.assertIsNone(Config.objects.first())  # Ensure no Config object exists
        self.assertEqual(get_appointment_buffer_time(), 60)
        self.assertEqual(get_appointment_lead_time(), '07:00:00')
        self.assertEqual(get_appointment_finish_time(), '15:00:00')
        self.assertEqual(get_appointment_slot_duration(), 30)
        self.assertEqual(get_website_name(), "django-appointment-website")

    def test_config_object_no_time_set(self):
        """Test with a Config object without 'slot_duration'; 'buffer', 'lead' and 'finish' time set."""
        Config.objects.create()
        self.assertEqual(get_appointment_buffer_time(), 60)
        self.assertEqual(get_appointment_lead_time(), '07:00:00')
        self.assertEqual(get_appointment_finish_time(), '15:00:00')
        self.assertEqual(get_appointment_slot_duration(), 30)
        self.assertEqual(get_website_name(), "django-appointment-website")

    def test_config_object_with_finish_time(self):
        """Test with a Config object with 'slot_duration'; 'buffer', 'lead' and 'finish' time set."""
        Config.objects.create(finish_time='17:00:00', lead_time='09:00:00',
                              appointment_buffer_time=60, slot_duration=30, website_name="config")
        self.assertEqual(get_appointment_buffer_time(), 60)
        self.assertEqual(get_appointment_lead_time().strftime('%H:%M:%S'), '09:00:00')
        self.assertEqual(get_appointment_finish_time().strftime('%H:%M:%S'), '17:00:00')
        self.assertEqual(get_appointment_slot_duration(), 30)
        self.assertEqual(get_website_name(), "config")

    def test_config_not_set_but_constants_patched(self):
        """Test with no Config object and patched constants."""
        self.assertEqual(get_appointment_buffer_time(), 60)
        self.assertEqual(get_appointment_lead_time(), '07:00:00')
        self.assertEqual(get_appointment_finish_time(), '15:00:00')
        self.assertEqual(get_appointment_slot_duration(), 30)
        self.assertEqual(get_website_name(), "django-appointment-website")


class TestGetAppointmentsForDateAndTime(BaseTest):

    def setUp(self):
        super().setUp()

        # Setting up some appointment requests and appointments for testing
        self.date_sample = datetime.datetime.today()

        # Creating overlapping appointments for staff_member1
        ar1 = self.create_appt_request_for_sm1(start_time=datetime.time(9, 0), end_time=datetime.time(10, 0))
        self.appointment1 = self.create_appointment_(user=self.client1, appointment_request=ar1)

        ar2 = self.create_appt_request_for_sm1(start_time=datetime.time(10, 30), end_time=datetime.time(11, 30))
        self.appointment2 = self.create_appointment_(user=self.client2, appointment_request=ar2)

        # Creating a non-overlapping appointment for staff_member1
        ar3 = self.create_appt_request_for_sm1(start_time=datetime.time(13, 0), end_time=datetime.time(14, 0))
        self.appointment3 = self.create_appointment_(user=self.client1, appointment_request=ar3)

    def test_get_appointments_overlapping_time_range(self):
        """Test retrieving appointments overlapping with a specific time range."""
        appointments = get_appointments_for_date_and_time(self.date_sample, datetime.time(10, 0), datetime.time(12, 0),
                                                          self.staff_member1)
        self.assertEqual(appointments.count(), 2)
        self.assertIn(self.appointment1, appointments)
        self.assertIn(self.appointment2, appointments)

    def test_get_appointments_outside_time_range(self):
        """Test retrieving appointments outside a specific time range."""
        appointments = get_appointments_for_date_and_time(self.date_sample, datetime.time(7, 0), datetime.time(8, 30),
                                                          self.staff_member1)
        self.assertEqual(appointments.count(), 0)

    def test_get_appointments_for_different_date(self):
        """Test retrieving appointments for a different date."""
        appointments = get_appointments_for_date_and_time(datetime.date(2023, 10, 11), datetime.time(9, 0),
                                                          datetime.time(12, 0), self.staff_member1)
        self.assertEqual(appointments.count(), 0)

    def test_get_appointments_for_different_staff_member(self):
        """Test retrieving appointments for a different staff member."""
        appointments = get_appointments_for_date_and_time(self.date_sample, datetime.time(9, 0), datetime.time(12, 0),
                                                          self.staff_member2)
        self.assertEqual(appointments.count(), 0)


class TestGetConfig(TestCase):

    def setUp(self):
        # Clear the cache at the start of each test to ensure a clean state
        cache.clear()

    def test_no_config_in_cache_or_db(self):
        """Test when there's no Config in cache or the database."""
        config = get_config()
        self.assertIsNone(config)

    def test_config_in_db_not_in_cache(self):
        """Test when there's a Config object in the database but not in the cache."""
        db_config = Config.objects.create(finish_time='17:00:00')
        config = get_config()
        self.assertEqual(config, db_config)

    def test_config_in_cache(self):
        """Test when there's a Config object in the cache."""
        db_config = Config.objects.create(finish_time='17:00:00')
        cache.set('config', db_config)
        # Use 'patch' to ensure the Config model isn't hit during the test
        with patch('appointment.models.Config.objects.first') as mock_first:
            config = get_config()
            self.assertEqual(config, db_config)
            mock_first.assert_not_called()  # Ensure the database wasn't hit


class TestGetDayOffById(BaseTest):  # Assuming you have a BaseTest class with some initial setups
    def setUp(self):
        super().setUp()  # Call the parent class setup

        # Assuming you have already set up some StaffMember objects in the BaseTest
        self.day_off = DayOff.objects.create(staff_member=self.staff_member1, start_date="2023-10-08",
                                             end_date="2023-10-10")

    def test_retrieve_existing_day_off(self):
        """Test retrieving an existing DayOff object."""
        retrieved_day_off = get_day_off_by_id(self.day_off.id)
        self.assertEqual(retrieved_day_off, self.day_off)

    def test_nonexistent_day_off_id(self):
        """Test trying to retrieve a DayOff object using a non-existent ID."""
        nonexistent_id = self.day_off.id + 1  # Just to ensure a non-existent ID, you can use any logic that suits you
        retrieved_day_off = get_day_off_by_id(nonexistent_id)
        self.assertIsNone(retrieved_day_off)


class TestGetNonWorkingDaysForStaff(BaseTest):
    def setUp(self):
        super().setUp()  # Call the parent class setup

        self.staff_member_with_working_days = self.staff_member1
        WorkingHours.objects.create(staff_member=self.staff_member_with_working_days, day_of_week=0,
                                    start_time=datetime.time(8, 0), end_time=datetime.time(12, 0))
        WorkingHours.objects.create(staff_member=self.staff_member_with_working_days, day_of_week=2,
                                    start_time=datetime.time(8, 0), end_time=datetime.time(12, 0))

        self.staff_member_without_working_days = self.staff_member2

    def test_retrieve_non_working_days_for_staff_with_some_working_days(self):
        """Test retrieving non-working days for a StaffMember with some working days set."""
        non_working_days = get_non_working_days_for_staff(self.staff_member_with_working_days.id)
        expected_days = [1, 3, 4, 5, 6]
        self.assertListEqual(non_working_days, expected_days)

    def test_retrieve_non_working_days_for_staff_without_working_days(self):
        """Test retrieving non-working days for a StaffMember with no working days set."""
        non_working_days = get_non_working_days_for_staff(self.staff_member_without_working_days.id)
        expected_days = [0, 1, 2, 3, 4, 5, 6]
        self.assertListEqual(non_working_days, expected_days)

    def test_nonexistent_staff_member_id(self):
        """Test trying to retrieve non-working days using a non-existent StaffMember ID."""
        nonexistent_id = self.staff_member_with_working_days.id + 100  # Just to ensure a non-existent ID
        non_working_days = get_non_working_days_for_staff(nonexistent_id)
        self.assertListEqual(non_working_days, [])


class TestGetStaffMemberAppointmentList(BaseTest):
    def setUp(self):
        super().setUp()

        # Creating appointments for each staff member.
        self.appointment1_for_user1 = self.create_appointment_for_user1()
        self.appointment2_for_user2 = self.create_appointment_for_user2()

    def test_retrieve_appointments_for_specific_staff_member(self):
        """Test retrieving appointments for a specific StaffMember."""
        # Testing for staff_member1
        appointments_for_staff_member1 = get_staff_member_appointment_list(self.staff_member1)
        self.assertIn(self.appointment1_for_user1, appointments_for_staff_member1)
        self.assertNotIn(self.appointment2_for_user2, appointments_for_staff_member1)

        # Testing for staff_member2
        appointments_for_staff_member2 = get_staff_member_appointment_list(self.staff_member2)
        self.assertIn(self.appointment2_for_user2, appointments_for_staff_member2)
        self.assertNotIn(self.appointment1_for_user1, appointments_for_staff_member2)

    def test_retrieve_appointments_for_staff_member_with_no_appointments(self):
        """Test retrieving appointments for a StaffMember with no appointments."""
        # Creating a new staff member with no appointments
        staff_member_with_no_appointments = self.create_staff_member_(user=self.client1, service=self.service1)
        appointments = get_staff_member_appointment_list(staff_member_with_no_appointments)
        self.assertListEqual(list(appointments), [])


class TestGetWeekdayNumFromDate(TestCase):
    def test_get_weekday_num_from_date(self):
        """Test getting the weekday number from a date."""
        sample_dates = {
            datetime.date(2023, 10, 9): 1,  # Monday
            datetime.date(2023, 10, 10): 2,  # Tuesday
            datetime.date(2023, 10, 11): 3,  # Wednesday
            datetime.date(2023, 10, 12): 4,  # Thursday
            datetime.date(2023, 10, 13): 5,  # Friday
            datetime.date(2023, 10, 14): 6,  # Saturday
            datetime.date(2023, 10, 15): 0,  # Sunday
        }

        for date, expected_weekday_num in sample_dates.items():
            self.assertEqual(get_weekday_num_from_date(date), expected_weekday_num)


@patch('appointment.utils.db_helpers.APPOINTMENT_BUFFER_TIME', 60)
@patch('appointment.utils.db_helpers.APPOINTMENT_SLOT_DURATION', 30)
class TestStaffMemberTimeFunctions(BaseTest):
    """Test suite for staff member time functions."""

    def setUp(self):
        super().setUp()

        # Set staff member-specific settings
        self.staff_member1.slot_duration = 15
        self.staff_member1.lead_time = datetime.time(8, 30)
        self.staff_member1.finish_time = datetime.time(18, 0)
        self.staff_member1.appointment_buffer_time = 45
        self.staff_member1.save()

        # Setting WorkingHours for staff_member1 for Monday
        self.wh = WorkingHours.objects.create(
            staff_member=self.staff_member1,
            day_of_week=1,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0)
        )

    def test_staff_member_buffer_time_with_global_setting(self):
        """Test buffer time when staff member-specific setting is None."""
        self.staff_member1.appointment_buffer_time = None
        self.staff_member1.save()
        buffer_time = get_staff_member_buffer_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(buffer_time, 60)  # Global setting

    def test_staff_member_buffer_time_with_staff_member_setting(self):
        """Test buffer time using staff member-specific setting."""
        buffer_time = get_staff_member_buffer_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(buffer_time, 45)  # Staff member specific setting

    def test_staff_member_slot_duration_with_global_setting(self):
        """Test slot duration when staff member-specific setting is None."""
        self.staff_member1.slot_duration = None
        self.staff_member1.save()
        slot_duration = get_staff_member_slot_duration(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(slot_duration, 30)  # Global setting

    def test_staff_member_slot_duration_with_staff_member_setting(self):
        """Test slot duration using staff member-specific setting."""
        slot_duration = get_staff_member_slot_duration(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(slot_duration, 15)  # Staff member specific setting

    def test_staff_member_start_time(self):
        """Test start time based on WorkingHours."""
        start_time = get_staff_member_start_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(start_time, datetime.time(9, 0))

    def test_staff_member_end_time(self):
        """Test end time based on WorkingHours."""
        end_time = get_staff_member_end_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(end_time, datetime.time(17, 0))

    def test_staff_member_start_time_with_lead_time(self):
        """Test start time when both lead_time and WorkingHours are available."""
        start_time = get_staff_member_start_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(start_time, self.wh.start_time)  # lead_time should prevail

    def test_staff_member_end_time_with_finish_time(self):
        """Test end time when both finish_time and WorkingHours are available."""
        end_time = get_staff_member_end_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(end_time, self.wh.end_time)  # finish_time should prevail

    def test_staff_member_buffer_time_with_working_hours_conflict(self):
        """Test buffer time when it conflicts with WorkingHours."""
        self.staff_member1.appointment_buffer_time = 120  # Set a buffer time greater than WorkingHours start time
        self.staff_member1.save()
        buffer_time = get_staff_member_buffer_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(buffer_time, 120)  # Should still use staff member-specific setting even if it causes conflict


class TestDBHelpers(BaseTest):
    def setUp(self):
        super().setUp()

    def test_get_staff_member_by_user_id(self):
        """Test retrieving a StaffMember object using a user id works as expected."""
        staff = get_staff_member_by_user_id(self.user1.id)
        self.assertIsNotNone(staff)
        self.assertEqual(staff, self.staff_member1)

        # Test for a non-existent user id
        staff = get_staff_member_by_user_id(99999)
        self.assertIsNone(staff)

    def test_get_staff_member_from_user_id_or_logged_in(self):
        """Test retrieving a StaffMember object using a user id or the logged in user works as expected."""
        staff = get_staff_member_from_user_id_or_logged_in(self.user1)
        self.assertIsNotNone(staff)
        self.assertEqual(staff, self.staff_member1)

        staff = get_staff_member_from_user_id_or_logged_in(self.user1, self.user2.id)
        self.assertIsNotNone(staff)
        self.assertEqual(staff, self.staff_member2)

        # Test for a non-existent user id
        staff = get_staff_member_from_user_id_or_logged_in(self.user1, 99999)
        self.assertIsNone(staff)

    def test_get_user_model(self):
        """Test retrieving the user model works as expected."""
        user_model = get_user_model()
        user_model_in_settings = apps.get_model(settings.AUTH_USER_MODEL)
        self.assertEqual(user_model, user_model_in_settings)

    def test_get_user_by_email(self):
        """Retrieve a user by email."""
        user = get_user_by_email("tester1@gmail.com")
        self.assertIsNotNone(user)
        self.assertEqual(user, self.user1)

        # Test for a non-existent email
        user = get_user_by_email("nonexistent@gmail.com")
        self.assertIsNone(user)


class TestWorkingHoursFunctions(BaseTest):
    def setUp(self):
        super().setUp()
        self.working_hours = WorkingHours.objects.create(
            staff_member=self.staff_member1,
            day_of_week=1,  # Monday
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0)
        )

    def test_get_working_hours_by_id(self):
        """Test retrieving a WorkingHours object by ID."""
        working_hours = get_working_hours_by_id(self.working_hours.id)
        self.assertEqual(working_hours, self.working_hours)

        # Non-existent ID
        working_hours = get_working_hours_by_id(99999)
        self.assertIsNone(working_hours)

    def test_get_working_hours_for_staff_and_day(self):
        """Test retrieving WorkingHours for a specific staff member and day."""
        # With set WorkingHours
        result = get_working_hours_for_staff_and_day(self.staff_member1, 1)
        self.assertEqual(result['start_time'], datetime.time(9, 0))
        self.assertEqual(result['end_time'], datetime.time(17, 0))

        # Without set WorkingHours but with staff member's default times
        self.staff_member1.lead_time = datetime.time(8, 0)
        self.staff_member1.finish_time = datetime.time(18, 0)
        self.staff_member1.save()
        result = get_working_hours_for_staff_and_day(self.staff_member1, 2)  # Tuesday
        self.assertEqual(result['start_time'], datetime.time(8, 0))
        self.assertEqual(result['end_time'], datetime.time(18, 0))

    def test_is_working_day(self):
        """is_working_day() should return True if there are WorkingHours for the staff member and day,
           False otherwise."""
        self.assertTrue(is_working_day(self.staff_member1, 1))  # Monday
        self.assertFalse(is_working_day(self.staff_member1, 2))  # Tuesday

    def test_working_hours_exist(self):
        """working_hours_exist() should return True if there are WorkingHours for the staff member and day,"""
        self.assertTrue(working_hours_exist(1, self.staff_member1))  # Monday
        self.assertFalse(working_hours_exist(2, self.staff_member1))  # Tuesday


@patch('appointment.utils.db_helpers.APPOINTMENT_LEAD_TIME', (7, 0))
@patch('appointment.utils.db_helpers.APPOINTMENT_FINISH_TIME', (15, 0))
@patch('appointment.utils.db_helpers.APPOINTMENT_SLOT_DURATION', 30)
@patch('appointment.utils.db_helpers.APPOINTMENT_BUFFER_TIME', 60)
class TestGetTimesFromConfig(TestCase):
    def setUp(self):
        self.sample_date = datetime.date(2023, 10, 9)
        cache.clear()

    def test_times_from_config_object(self):
        """Test retrieving times from a Config object."""
        # Create a Config object with custom values
        Config.objects.create(
            lead_time=datetime.time(9, 0),
            finish_time=datetime.time(17, 0),
            slot_duration=45,
            appointment_buffer_time=90
        )

        start_time, end_time, slot_duration, buff_time = get_times_from_config(self.sample_date)

        # Assert times from 'Config' object
        self.assertEqual(start_time, datetime.datetime(2023, 10, 9, 9, 0))
        self.assertEqual(end_time, datetime.datetime(2023, 10, 9, 17, 0))
        self.assertEqual(slot_duration, datetime.timedelta(minutes=45))
        self.assertEqual(buff_time, datetime.timedelta(minutes=90))

    def test_times_from_default_settings(self):
        """Test retrieving times from default settings."""
        # Ensure no Config object exists
        Config.objects.all().delete()

        start_time, end_time, slot_duration, buff_time = get_times_from_config(self.sample_date)

        # Assert times from default settings
        self.assertEqual(start_time, datetime.datetime(2023, 10, 9, 7, 0))
        self.assertEqual(end_time, datetime.datetime(2023, 10, 9, 15, 0))
        self.assertEqual(slot_duration, datetime.timedelta(minutes=30))
        self.assertEqual(buff_time, datetime.timedelta(minutes=60))


class CreateNewUserTest(TestCase):
    def test_create_new_user_unique_username(self):
        """Test creating a new user with a unique username."""
        client_data = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        user = create_new_user(client_data)
        self.assertEqual(user.username, 'john.doe')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.email, 'john.doe@example.com')

    def test_create_new_user_duplicate_username(self):
        """Test creating a new user with a duplicate username."""
        client_data1 = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        user1 = create_new_user(client_data1)
        self.assertEqual(user1.username, 'john.doe')

        client_data2 = {'name': 'Jane Doe', 'email': 'john.doe@example.com'}
        user2 = create_new_user(client_data2)
        self.assertEqual(user2.username, 'john.doe01')  # Suffix added

        client_data3 = {'name': 'James Doe', 'email': 'john.doe@example.com'}
        user3 = create_new_user(client_data3)
        self.assertEqual(user3.username, 'john.doe02')  # Next suffix

    def test_generate_unique_username(self):
        """Test if generate_unique_username_from_email function generates unique usernames."""
        email = 'john.doe@example.com'
        username = generate_unique_username_from_email(email)
        self.assertEqual(username, 'john.doe')

        # Assuming we have a user with the same username
        CLIENT_MODEL = get_user_model()
        CLIENT_MODEL.objects.create_user(username='john.doe', email=email)
        new_username = generate_unique_username_from_email(email)
        self.assertEqual(new_username, 'john.doe01')

    def test_parse_name(self):
        """Test if parse_name function splits names correctly."""
        name = "John Doe"
        first_name, last_name = parse_name(name)
        self.assertEqual(first_name, 'John')
        self.assertEqual(last_name, 'Doe')

    def test_create_new_user_check_password(self):
        """Test creating a new user with a password."""
        client_data = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        user = create_new_user(client_data)
        password = f"{get_website_name()}{get_current_year()}"
        self.assertTrue(user.check_password(password))

