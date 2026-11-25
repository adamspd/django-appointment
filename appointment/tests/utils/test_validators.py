import datetime

from appointment.utils.validators import BOOKING_CONTEXT_MAX_LENGTH, not_in_the_past, validate_booking_context
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.translation import gettext as _


class NotInThePastTests(TestCase):
    def test_date_in_the_past_raises_validation_error(self):
        """Test that a date in the past raises a ValidationError."""
        past_date = timezone.localdate() - datetime.timedelta(days=1)
        with self.assertRaises(ValidationError) as context:
            not_in_the_past(past_date)
        self.assertEqual(str(context.exception.message), _('Date is in the past'))

    def test_date_today_does_not_raise_error(self):
        """Test that today's date does not raise an error."""
        today = timezone.localdate()
        try:
            not_in_the_past(today)
        except ValidationError:
            self.fail("not_in_the_past() raised ValidationError unexpectedly for today's date!")

    def test_date_in_the_future_does_not_raise_error(self):
        """Test that a date in the future does not raise an error."""
        future_date = timezone.localdate() + datetime.timedelta(days=1)
        try:
            not_in_the_past(future_date)
        except ValidationError:
            self.fail("not_in_the_past() raised ValidationError unexpectedly for a future date!")


@override_settings(APPOINTMENT_BOOKING_CONTEXT_KEYS=['utm_source', 'utm_campaign'])
class ValidateBookingContextTests(TestCase):
    def assert_refused(self, value, code):
        with self.assertRaises(ValidationError) as context:
            validate_booking_context(value)
        self.assertEqual(context.exception.code, code)

    def test_none_and_allowed_values_pass(self):
        validate_booking_context(None)
        validate_booking_context({})
        validate_booking_context({'utm_source': 'newsletter', 'utm_campaign': 'été 2026'})
        validate_booking_context({'utm_source': 'x' * BOOKING_CONTEXT_MAX_LENGTH})

    def test_only_a_flat_dict_of_text(self):
        for value in (['utm_source'], 'utm_source=x', 42):
            self.assert_refused(value, 'invalid')
        self.assert_refused({'utm_source': {'nested': 'x'}}, 'invalid_value')
        self.assert_refused({'utm_source': ['x']}, 'invalid_value')
        self.assert_refused({'utm_source': 1}, 'invalid_value')
        self.assert_refused({'utm_source': None}, 'invalid_value')

    def test_unknown_key_is_refused_not_dropped(self):
        self.assert_refused({'utm_source': 'x', 'session_id': 'abc'}, 'unknown_key')

    def test_too_long_value_refused(self):
        self.assert_refused({'utm_source': 'x' * (BOOKING_CONTEXT_MAX_LENGTH + 1)}, 'too_long')

    def test_control_and_invisible_characters_refused(self):
        for text in ('a\nb', 'a\rb', 'a\x00b', 'a\x1b[31mb', 'a‮b', 'a​b'):
            self.assert_refused({'utm_source': text}, 'invalid_character')

    def test_error_never_repeats_the_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_booking_context({'utm_source': '<script>' + 'x' * 300})
        self.assertNotIn('<script>', str(context.exception))
        with self.assertRaises(ValidationError) as context:
            validate_booking_context({'<script>': 'x'})
        self.assertNotIn('<script>', str(context.exception))

    @override_settings(APPOINTMENT_BOOKING_CONTEXT_KEYS=[])
    def test_feature_is_off_by_default(self):
        validate_booking_context(None)
        self.assert_refused({'utm_source': 'x'}, 'unknown_key')

    def test_bad_key_setting_is_a_configuration_error(self):
        for keys in ('utm_source', ['UTM'], ['utm source'], ['1utm'], [1], ['x' * 51]):
            with self.subTest(keys=keys), override_settings(APPOINTMENT_BOOKING_CONTEXT_KEYS=keys):
                with self.assertRaises(ImproperlyConfigured):
                    validate_booking_context({})
