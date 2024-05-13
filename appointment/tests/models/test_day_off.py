from copy import deepcopy
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from appointment.models import DayOff
from appointment.tests.base.base_test import BaseTest


class DayOffCreationTestCase(BaseTest):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        self.day_off = DayOff.objects.create(
            staff_member=self.staff_member1,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2)
        )
        super().setUp()

    def tearDown(self):
        super().tearDown()
        DayOff.objects.all().delete()

    def test_default_attributes_on_creation(self):
        """Test basic creation of DayOff."""
        self.assertIsNotNone(self.day_off)
        self.assertEqual(self.day_off.staff_member, self.staff_member1)
        self.assertTrue(self.day_off.is_owner(self.users['staff1'].id))
        self.assertFalse(self.day_off.is_owner(9999))  # Assuming 9999 is not a valid user ID

    def test_day_off_str_method(self):
        """Test that the string representation of a day off is correct."""
        self.assertEqual(str(self.day_off), f"{date.today()} to {date.today() + timedelta(days=2)} - Day off")
        day_off = deepcopy(self.day_off)
        # Testing with a description
        day_off.description = "Vacation"
        day_off.save()
        self.assertEqual(str(day_off), f"{date.today()} to {date.today() + timedelta(days=2)} - Vacation")


class DayOffModelTestCase(BaseTest):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_day_off_start_date_before_end_date(self):
        """Test that start date must be before end date upon day off creation."""
        with self.assertRaises(ValidationError):
            DayOff.objects.create(
                staff_member=self.staff_member1,
                start_date=date.today() + timedelta(days=1),
                end_date=date.today()
            ).clean()

    def test_day_off_without_staff_member(self):
        """Test that a day off cannot be created without a staff member."""
        with self.assertRaises(IntegrityError):
            DayOff.objects.create(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1)
            )
