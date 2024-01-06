from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase

from appointment.models import Service, StaffMember
from appointment.tests.mixins.base_mixin import ServiceMixin, StaffMemberMixin, UserMixin


class StaffMemberModelTestCase(TestCase, UserMixin, ServiceMixin, StaffMemberMixin):
    def setUp(self):
        self.user = self.create_user_()
        self.service = self.create_service_()
        self.staff_member = self.create_staff_member_(self.user, self.service)

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

    # Assuming there's a function to get the next available slot

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

        # Try to add a non-existent service to the staff member's services_offered
        with self.assertRaises(ValueError):
            new_staff_member.services_offered.add(
                Service(id=9999, name="Non-existent Service", duration=timedelta(hours=2), price=200))
