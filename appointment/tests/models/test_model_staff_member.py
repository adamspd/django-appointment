import datetime
from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext as _

from appointment.models import DayOff, Service, StaffMember, WorkingHours
from appointment.tests.mixins.base_mixin import ConfigMixin, ServiceMixin, StaffMemberMixin, UserMixin


class StaffMemberModelTestCase(TestCase, UserMixin, ServiceMixin, StaffMemberMixin, ConfigMixin):
    def setUp(self):
        self.user = self.create_user_()
        self.service = self.create_service_()
        self.staff_member = self.create_staff_member_(self.user, self.service)
        self.config = self.create_config_(lead_time=datetime.time(9, 0), finish_time=datetime.time(17, 0),
                                          slot_duration=30)

    def test_staff_member_creation(self):
        """Test if a staff member can be created."""
        self.assertIsNotNone(self.staff_member)
        self.assertEqual(self.staff_member.user, self.user)
        self.assertEqual(list(self.staff_member.get_services_offered()), [self.service])
        self.assertIsNone(self.staff_member.lead_time)
        self.assertIsNone(self.staff_member.finish_time)
        self.assertIsNone(self.staff_member.slot_duration)
        self.assertIsNone(self.staff_member.appointment_buffer_time)

    def test_staff_member_without_user(self):
        """A staff member cannot be created without a user."""
        with self.assertRaises(IntegrityError):
            StaffMember.objects.create()

    def test_staff_member_without_service(self):
        """A staff member can be created without a service."""
        self.staff_member.delete()
        new_staff_member = StaffMember.objects.create(user=self.user)
        self.assertIsNotNone(new_staff_member)
        self.assertEqual(new_staff_member.services_offered.count(), 0)

    def test_date_joined_auto_creation(self):
        """Test if the date_joined field is automatically set upon creation."""
        self.assertIsNotNone(self.staff_member.created_at)

    # Edge cases
    def test_staff_member_multiple_services(self):
        """A staff member can offer multiple services."""
        service2 = Service.objects.create(name="Test Service 2", duration=timedelta(hours=2), price=200)
        self.staff_member.services_offered.add(service2)
        self.assertIn(service2, self.staff_member.services_offered.all())

    def test_staff_member_with_non_existent_service(self):
        """A staff member cannot offer a non-existent service."""
        # Create a new staff member without any services
        self.staff_member.delete()
        new_staff_member = StaffMember.objects.create(user=self.user)

        # Trying to add a non-existent service to the staff member's services_offered
        with self.assertRaises(ValueError):
            new_staff_member.services_offered.add(
                Service(id=9999, name="Non-existent Service", duration=timedelta(hours=2), price=200))

    def test_str_representation(self):
        """Test the string representation of a StaffMember."""
        expected_str = self.staff_member.get_staff_member_name()
        self.assertEqual(str(self.staff_member), expected_str)

    def test_get_slot_duration_with_config(self):
        """Test get_slot_duration method with Config set."""
        self.config.slot_duration = 30
        self.config.save()
        self.assertEqual(self.staff_member.get_slot_duration(), 30)

    def test_get_slot_duration_text(self):
        """Test get_slot_duration_text method."""
        self.staff_member.slot_duration = 45
        self.assertEqual(self.staff_member.get_slot_duration_text(), "45 minutes")

    def test_get_lead_time(self):
        """Test get_lead_time method."""
        self.config.lead_time = datetime.time(9, 0)
        self.config.save()
        self.assertIsNone(self.staff_member.lead_time)
        self.assertEqual(self.staff_member.get_lead_time(), datetime.time(9, 0))

    def test_works_on_both_weekends_day(self):
        """Test works_on_both_weekends_day method."""
        self.staff_member.work_on_saturday = True
        self.staff_member.work_on_sunday = True
        self.assertTrue(self.staff_member.works_on_both_weekends_day())

    def test_get_non_working_days(self):
        """Test get_non_working_days method."""
        self.staff_member.work_on_saturday = False
        self.staff_member.work_on_sunday = False
        self.assertEqual(self.staff_member.get_non_working_days(),
                         [6, 0])  # [6, 0] represents Saturday and Sunday

    def test_get_services_offered(self):
        """Test get_services_offered method."""
        self.assertIn(self.service, self.staff_member.get_services_offered())

    def test_get_service_offered_text(self):
        """Test get_service_offered_text method."""
        self.assertEqual(self.staff_member.get_service_offered_text(), self.service.name)

    def test_get_appointment_buffer_time(self):
        """Test get_appointment_buffer_time method."""
        self.config.appointment_buffer_time = 15
        self.config.save()
        self.assertIsNone(self.staff_member.appointment_buffer_time)
        self.assertEqual(self.staff_member.get_appointment_buffer_time(), 15)

    def test_get_finish_time(self):
        """Test that the finish time is correctly returned from staff member or config."""
        # Case 1: Staff member has a defined finish time
        self.staff_member.finish_time = datetime.time(18, 0)
        self.staff_member.save()
        self.assertEqual(self.staff_member.get_finish_time(), datetime.time(18, 0))

        # Case 2: Staff member does not have a defined finish time, use config's
        self.staff_member.finish_time = None
        self.staff_member.save()
        self.assertEqual(self.staff_member.get_finish_time(), self.config.finish_time)

    def test_get_staff_member_first_name(self):
        """Test that the staff member's first name is returned."""
        self.assertEqual(self.staff_member.get_staff_member_first_name(), self.user.first_name)

    def test_get_weekend_days_worked_text(self):
        """Test various combinations of weekend work."""
        self.staff_member.work_on_saturday = True
        self.staff_member.work_on_sunday = False
        self.staff_member.save()
        self.assertEqual(self.staff_member.get_weekend_days_worked_text(), _("Saturday"))

        self.staff_member.work_on_sunday = True
        self.staff_member.save()
        self.assertEqual(self.staff_member.get_weekend_days_worked_text(), _("Saturday and Sunday"))

        self.staff_member.work_on_saturday = False
        self.staff_member.save()
        self.assertEqual(self.staff_member.get_weekend_days_worked_text(), _("Sunday"))

        self.staff_member.work_on_saturday = False
        self.staff_member.work_on_sunday = False
        self.staff_member.save()
        self.assertEqual(self.staff_member.get_weekend_days_worked_text(), _("None"))

    def test_get_appointment_buffer_time_text(self):
        """Test the textual representation of the appointment buffer time."""
        self.staff_member.appointment_buffer_time = 45  # 45 minutes
        self.assertEqual(self.staff_member.get_appointment_buffer_time_text(), "45 minutes")

    def test_get_days_off(self):
        """Test retrieval of days off."""
        DayOff.objects.create(staff_member=self.staff_member, start_date="2023-01-01", end_date="2023-01-02")
        self.assertEqual(len(self.staff_member.get_days_off()), 1)

    def test_get_working_hours(self):
        """Test retrieval of working hours."""
        WorkingHours.objects.create(staff_member=self.staff_member, day_of_week=1, start_time=datetime.time(9, 0),
                                    end_time=datetime.time(17, 0))
        self.assertEqual(len(self.staff_member.get_working_hours()), 1)

    def test_update_upon_working_hours_deletion(self):
        """Test the update of work_on_saturday and work_on_sunday upon working hours deletion."""
        self.staff_member.update_upon_working_hours_deletion(6)
        self.assertFalse(self.staff_member.work_on_saturday)
        self.staff_member.update_upon_working_hours_deletion(0)
        self.assertFalse(self.staff_member.work_on_sunday)

    def test_is_working_day(self):
        """Test whether a day is considered a working day."""
        self.staff_member.work_on_saturday = False
        self.staff_member.work_on_sunday = False
        self.staff_member.save()
        self.assertFalse(self.staff_member.is_working_day(6))  # Saturday
        self.assertTrue(self.staff_member.is_working_day(1))  # Monday
