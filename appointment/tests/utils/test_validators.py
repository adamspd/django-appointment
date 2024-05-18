import datetime

from appointment.utils.validators import not_in_the_past
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _


class NotInThePastTests(TestCase):
    def test_date_in_the_past_raises_validation_error(self):
        """Test that a date in the past raises a ValidationError."""
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        with self.assertRaises(ValidationError) as context:
            not_in_the_past(past_date)
        self.assertEqual(str(context.exception.message), _('Date is in the past'))

    def test_date_today_does_not_raise_error(self):
        """Test that today's date does not raise an error."""
        today = datetime.date.today()
        try:
            not_in_the_past(today)
        except ValidationError:
            self.fail("not_in_the_past() raised ValidationError unexpectedly for today's date!")

    def test_date_in_the_future_does_not_raise_error(self):
        """Test that a date in the future does not raise an error."""
        future_date = datetime.date.today() + datetime.timedelta(days=1)
        try:
            not_in_the_past(future_date)
        except ValidationError:
            self.fail("not_in_the_past() raised ValidationError unexpectedly for a future date!")
