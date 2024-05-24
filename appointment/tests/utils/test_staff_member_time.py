import datetime
from unittest.mock import patch

from django.core.cache import cache
from django.test import override_settings

from appointment.models import StaffMember
from appointment.tests.base.base_test import BaseTest
from appointment.utils.db_helpers import Config, WorkingHours, get_staff_member_buffer_time, \
    get_staff_member_end_time, get_staff_member_slot_duration, get_staff_member_start_time


class BaseStaffMemberTimeTestSetup(BaseTest):
    """Base setup class for staff member time function tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

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

    @override_settings(DEBUG=True)
    def tearDown(self):
        super().tearDown()
        StaffMember.objects.all().delete()
        if Config.objects.exists():
            Config.objects.all().delete()
        WorkingHours.objects.all().delete()
        cache.clear()


@patch('appointment.utils.db_helpers.APPOINTMENT_BUFFER_TIME', 59)
class TestGetStaffMemberBufferTime(BaseStaffMemberTimeTestSetup):
    """Test suite for get_staff_member_buffer_time function."""

    def test_staff_member_buffer_time_with_global_setting(self):
        """Test buffer time when staff member-specific setting is None."""
        self.staff_member1.appointment_buffer_time = None
        self.staff_member1.save()
        buffer_time = get_staff_member_buffer_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(buffer_time, 59)  # Global setting

    def test_staff_member_buffer_time_with_staff_member_setting(self):
        """Test buffer time using staff member-specific setting."""
        buffer_time = get_staff_member_buffer_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(buffer_time, 45)  # Staff member specific setting

    def test_staff_member_buffer_time_with_working_hours_conflict(self):
        """Test buffer time when it conflicts with WorkingHours."""
        self.staff_member1.appointment_buffer_time = 120  # Set a buffer time greater than WorkingHours start time
        self.staff_member1.save()
        buffer_time = get_staff_member_buffer_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(buffer_time, 120)  # Should still use staff member-specific setting even if it causes conflict


@patch('appointment.utils.db_helpers.APPOINTMENT_SLOT_DURATION', 31)
class TestGetStaffMemberSlotDuration(BaseStaffMemberTimeTestSetup):
    """Test suite for get_staff_member_slot_duration function."""

    def test_staff_member_slot_duration_with_global_setting(self):
        """Test slot duration when staff member-specific setting is None."""
        self.staff_member1.slot_duration = None
        self.staff_member1.save()
        slot_duration = get_staff_member_slot_duration(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(slot_duration, 31)  # Global setting

    def test_staff_member_slot_duration_with_staff_member_setting(self):
        """Test slot duration using staff member-specific setting."""
        slot_duration = get_staff_member_slot_duration(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(slot_duration, 15)  # Staff member specific setting


class TestGetStaffMemberStartTime(BaseStaffMemberTimeTestSetup):
    """Test suite for get_staff_member_start_time function."""

    def test_staff_member_start_time(self):
        """Test start time based on WorkingHours."""
        start_time = get_staff_member_start_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(start_time, datetime.time(9, 0))

    def test_staff_member_start_time_with_lead_time(self):
        """Test start time when both lead_time and WorkingHours are available."""
        start_time = get_staff_member_start_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(start_time, self.wh.start_time)  # lead_time should prevail


class TestGetStaffMemberEndTime(BaseStaffMemberTimeTestSetup):
    """Test suite for get_staff_member_end_time function."""

    def test_staff_member_end_time(self):
        """Test end time based on WorkingHours."""
        end_time = get_staff_member_end_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(end_time, datetime.time(17, 0))

    def test_staff_member_end_time_with_finish_time(self):
        """Test end time when both finish_time and WorkingHours are available."""
        end_time = get_staff_member_end_time(self.staff_member1, datetime.date(2023, 10, 9))
        self.assertEqual(end_time, self.wh.end_time)  # finish_time should prevail
