from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from appointment.models import Unavailability
from appointment.tests.base.base_test import BaseTest


class UnavailabilityCreationTestCase(BaseTest):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.unavailability = Unavailability.objects.create(
            staff_member=self.staff_member1,
            date=date.today() + timedelta(days=1),
            start_time=time(12, 0),
            end_time=time(13, 0)
        )
        super().setUp()

    def tearDown(self):
        super().tearDown()
        Unavailability.objects.all().delete()

    def test_default_attributes_on_creation(self):
        """Test basic creation of Unavailability."""
        self.assertIsNotNone(self.unavailability)
        self.assertEqual(self.unavailability.staff_member, self.staff_member1)
        self.assertIsNone(self.unavailability.description)
        self.assertTrue(self.unavailability.is_owner(self.users['staff1'].id))
        self.assertFalse(self.unavailability.is_owner(9999))  # Assuming 9999 is not a valid user ID

    def test_unavailability_str_method(self):
        """Test that the string representation of an unavailability is correct."""
        self.assertEqual(str(self.unavailability), f"{time(12, 0)} to {time(13, 0)} - Unavailability")
        # Testing with a description
        self.unavailability.description = "Lunch"
        self.unavailability.save()
        self.assertEqual(str(self.unavailability), f"{time(12, 0)} to {time(13, 0)} - Lunch")

    def test_datetime_getters(self):
        """Test that the date and times can be recombined into datetimes."""
        tomorrow = date.today() + timedelta(days=1)
        self.assertEqual(self.unavailability.get_date(), tomorrow)
        self.assertEqual(self.unavailability.get_start_time(), time(12, 0))
        self.assertEqual(self.unavailability.get_end_time(), time(13, 0))
        self.assertEqual(self.unavailability.get_start_datetime().date(), tomorrow)
        self.assertEqual(self.unavailability.get_start_datetime().time(), time(12, 0))
        self.assertEqual(self.unavailability.get_end_datetime().time(), time(13, 0))


class UnavailabilityModelTestCase(BaseTest):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_unavailability_without_staff_member(self):
        """Test that an unavailability cannot be created without a staff member."""
        with self.assertRaises(IntegrityError):
            Unavailability.objects.create(
                date=date.today() + timedelta(days=1),
                start_time=time(12, 0),
                end_time=time(13, 0)
            )


class UnavailabilityCleanTestCase(BaseTest):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def build(self, date_=None, start_time=time(12, 0), end_time=time(13, 0)):
        return Unavailability(
            staff_member=self.staff_member1,
            date=date_ if date_ is not None else date.today() + timedelta(days=1),
            start_time=start_time,
            end_time=end_time
        )

    def test_clean_accepts_a_valid_unavailability(self):
        """A future unavailability with start before end validates without raising."""
        self.build().clean()

    def test_clean_accepts_today(self):
        """Today is not a past date, so it must be accepted."""
        self.build(date_=date.today()).clean()

    def test_clean_rejects_start_time_after_end_time(self):
        with self.assertRaises(ValidationError):
            self.build(start_time=time(13, 0), end_time=time(12, 0)).clean()

    def test_clean_rejects_equal_start_and_end_time(self):
        with self.assertRaises(ValidationError):
            self.build(start_time=time(12, 0), end_time=time(12, 0)).clean()

    def test_clean_rejects_a_past_date(self):
        with self.assertRaises(ValidationError):
            self.build(date_=date.today() - timedelta(days=1)).clean()

    def test_full_clean_validates_instead_of_raising_type_error(self):
        """full_clean() is what a ModelForm calls, so the Django admin depends on it."""
        self.build().full_clean(exclude=['staff_member'])

        with self.assertRaises(ValidationError):
            self.build(date_=date.today() - timedelta(days=1)).full_clean(exclude=['staff_member'])
