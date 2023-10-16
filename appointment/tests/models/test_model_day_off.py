from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from appointment.models import DayOff
from appointment.tests.base.base_test import BaseTest


class DayOffModelTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.day_off = DayOff.objects.create(
            staff_member=self.staff_member1,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1)
        )

    def test_day_off_creation(self):
        """Test basic creation of DayOff."""
        self.assertIsNotNone(self.day_off)
        self.assertEqual(self.day_off.staff_member, self.staff_member1)

    def test_day_off_start_date_before_end_date(self):
        """Test that start date must be before end date upon day off creation."""
        with self.assertRaises(ValidationError):
            DayOff.objects.create(
                staff_member=self.staff_member1,
                start_date=date.today() + timedelta(days=1),
                end_date=date.today()
            ).clean()

    def test_day_off_is_owner(self):
        """Test that is_owner method in day off model works as expected."""
        self.assertTrue(self.day_off.is_owner(self.user1.id))
        self.assertFalse(self.day_off.is_owner(9999))  # Assuming 9999 is not a valid user ID in your tests

    def test_day_off_without_staff_member(self):
        """Test that a day off cannot be created without a staff member."""
        with self.assertRaises(IntegrityError):
            DayOff.objects.create(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1)
            )

    def test_day_off_str_method(self):
        """Test that the string representation of a day off is correct."""
        self.assertEqual(str(self.day_off), f"{date.today()} to {date.today() + timedelta(days=1)} - Day off")

        # Testing with a description
        self.day_off.description = "Vacation"
        self.day_off.save()
        self.assertEqual(str(self.day_off), f"{date.today()} to {date.today() + timedelta(days=1)} - Vacation")
