from datetime import time

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext as _

from appointment.models import WorkingHours
from appointment.tests.mixins.base_mixin import ServiceMixin, StaffMemberMixin, UserMixin


class WorkingHoursModelTestCase(TestCase, UserMixin, ServiceMixin, StaffMemberMixin):
    def setUp(self):
        self.user = self.create_user_()
        self.service = self.create_service_()
        self.staff_member = self.create_staff_member_(self.user, self.service)
        self.working_hours = WorkingHours.objects.create(
                staff_member=self.staff_member,
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(17, 0)
        )

    def test_default_attributes_on_creation(self):
        """Test if a WorkingHours instance can be created."""
        self.assertIsNotNone(self.working_hours)
        self.assertEqual(self.working_hours.staff_member, self.staff_member)
        self.assertEqual(self.working_hours.get_start_time(), time(9, 0))
        self.assertEqual(self.working_hours.get_end_time(), time(17, 0))

    def test_working_hours_str_method(self):
        """Test that the string representation of a WorkingHours instance is correct."""
        self.assertEqual(str(self.working_hours), "Monday - 09:00:00 to 17:00:00")

    def test_get_day_of_week_str(self):
        """Test that the get_day_of_week_str method in WorkingHours model works as expected."""
        self.assertEqual(self.working_hours.get_day_of_week_str(), _("Monday"))


class WorkingHoursValidationTestCase(TestCase, UserMixin, ServiceMixin, StaffMemberMixin):
    def setUp(self):
        self.user = self.create_user_()
        self.service = self.create_service_()
        self.staff_member = self.create_staff_member_(self.user, self.service)
        self.working_hours = WorkingHours.objects.create(
                staff_member=self.staff_member,
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(17, 0)
        )

    def test_working_hours_start_time_before_end_time(self):
        """A WorkingHours instance cannot be created if start_time is after end_time."""
        with self.assertRaises(ValidationError):
            WorkingHours.objects.create(
                staff_member=self.staff_member,
                day_of_week=2,
                start_time=time(17, 0),
                end_time=time(9, 0)
            ).clean()

    def test_working_hours_without_staff_member(self):
        """A WorkingHours instance cannot be created without a staff member."""
        with self.assertRaises(IntegrityError):
            WorkingHours.objects.create(
                day_of_week=3,
                start_time=time(9, 0),
                end_time=time(17, 0)
            )

    def test_working_hours_is_owner(self):
        """Test that is_owner method in WorkingHours model works as expected."""
        self.assertTrue(self.working_hours.is_owner(self.user.id))
        self.assertFalse(self.working_hours.is_owner(9999))  # Assuming 9999 is not a valid user ID in your tests

    def test_staff_member_weekend_status_update(self):
        """Test that the staff member's weekend status is updated when a WorkingHours instance is created."""
        WorkingHours.objects.create(
            staff_member=self.staff_member,
            day_of_week=6,  # Saturday
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        self.staff_member.refresh_from_db()
        self.assertTrue(self.staff_member.work_on_saturday)

        WorkingHours.objects.create(
            staff_member=self.staff_member,
            day_of_week=0,  # Sunday
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        self.staff_member.refresh_from_db()
        self.assertTrue(self.staff_member.work_on_sunday)

    def test_working_hours_duplicate_day(self):
        """A WorkingHours instance cannot be created if the staff member already has a working hours on that day."""
        with self.assertRaises(IntegrityError):
            WorkingHours.objects.create(
                staff_member=self.staff_member,
                day_of_week=1,  # Same day as the working_hours created in setUp
                start_time=time(9, 0),
                end_time=time(17, 0)
            )
