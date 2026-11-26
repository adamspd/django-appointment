# test_date_time.py
# Path: appointment/tests/utils/test_date_time.py

import datetime
import warnings
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from appointment.utils.date_time import (
    DATE_FORMATS, combine_date_and_time, convert_12_hour_time_to_24_hour_time, convert_24_hour_time_to_12_hour_time,
    convert_minutes_in_human_readable_format, convert_str_to_date,
    convert_str_to_time, get_ar_end_time, get_client_time_text, get_current_year, get_timestamp,
    get_valid_timezone_name, get_weekday_num, gregorian_to_jalali, local_date_format, local_digits, long_date_format,
    time_difference
)


class Convert12HourTo24HourTimeTests(TestCase):
    def setUp(self):
        ctx = warnings.catch_warnings()
        ctx.__enter__()
        warnings.simplefilter("ignore", DeprecationWarning)
        self.addCleanup(ctx.__exit__, None, None, None)

    def test_basic_conversion(self):
        """Test basic 12-hour to 24-hour conversions."""
        self.assertEqual(convert_12_hour_time_to_24_hour_time("01:10 AM"), "01:10:00")
        self.assertEqual(convert_12_hour_time_to_24_hour_time("01:20 PM"), "13:20:00")

    def test_midnight_and_noon(self):
        """Test conversion of midnight and noon times."""
        self.assertEqual(convert_12_hour_time_to_24_hour_time("12:00 AM"), "00:00:00")
        self.assertEqual(convert_12_hour_time_to_24_hour_time("12:00 PM"), "12:00:00")

    def test_boundary_times(self):
        """Test conversion of boundary times."""
        self.assertEqual(convert_12_hour_time_to_24_hour_time("12:00 AM"), "00:00:00")
        self.assertEqual(convert_12_hour_time_to_24_hour_time("11:59 PM"), "23:59:00")

    def test_datetime_and_time_objects(self):
        """Test conversion using datetime and time objects."""
        dt_obj = datetime.datetime(2023, 1, 1, 14, 30)
        time_obj = datetime.time(14, 30)
        self.assertEqual(convert_12_hour_time_to_24_hour_time(dt_obj), "14:30:00")
        self.assertEqual(convert_12_hour_time_to_24_hour_time(time_obj), "14:30:00")

    def test_case_insensitivity_and_whitespace(self):
        """Test conversion handling of different case formats and white-space."""
        self.assertEqual(convert_12_hour_time_to_24_hour_time(" 12:00 am "), "00:00:00")
        self.assertEqual(convert_12_hour_time_to_24_hour_time("01:00 pM "), "13:00:00")

    def test_invalid_values(self):
        """Test invalid values."""
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("13:00 PM")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("12:60 AM")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time(["12:00 AM"])
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time({"time": "12:00 AM"})
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("25:00 AM")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("01:00")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("Random String")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("01:60 AM")


class Convert24HourTimeTo12HourTimeTests(TestCase):
    def setUp(self):
        ctx = warnings.catch_warnings()
        ctx.__enter__()
        warnings.simplefilter("ignore", DeprecationWarning)
        self.addCleanup(ctx.__exit__, None, None, None)


    def test_valid_24_hour_strings(self):
        self.assertEqual(convert_24_hour_time_to_12_hour_time("13:00"), "01:00 PM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("00:00"), "12:00 AM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("23:59"), "11:59 PM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("12:00"), "12:00 PM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("01:00"), "01:00 AM")

    def test_valid_24_hour_with_seconds(self):
        self.assertEqual(convert_24_hour_time_to_12_hour_time("13:00:01"), "01:00:01 PM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("00:00:59"), "12:00:59 AM")

    def test_time_object_input(self):
        time_input = datetime.time(13, 15)
        self.assertEqual(convert_24_hour_time_to_12_hour_time(time_input), "01:15 PM")
        time_input = datetime.time(0, 0)
        self.assertEqual(convert_24_hour_time_to_12_hour_time(time_input), "12:00 AM")

    def test_invalid_time_strings(self):
        with self.assertRaises(ValueError):
            convert_24_hour_time_to_12_hour_time("25:00")
        with self.assertRaises(ValueError):
            convert_24_hour_time_to_12_hour_time("-01:00")
        with self.assertRaises(ValueError):
            convert_24_hour_time_to_12_hour_time("13:60")
        with self.assertRaises(ValueError):
            convert_24_hour_time_to_12_hour_time("invalid")
        with self.assertRaises(ValueError):
            convert_24_hour_time_to_12_hour_time("1 PM")
        with self.assertRaises(ValueError):
            convert_24_hour_time_to_12_hour_time("13 PM")
        with self.assertRaises(ValueError):
            convert_24_hour_time_to_12_hour_time("24:00")

    def test_edge_cases(self):
        self.assertEqual(convert_24_hour_time_to_12_hour_time("12:00"), "12:00 PM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("00:00"), "12:00 AM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("11:59"), "11:59 AM")
        self.assertEqual(convert_24_hour_time_to_12_hour_time("23:59"), "11:59 PM")

class DeprecatedTimeHelperWarningTests(TestCase):
    def test_convert_12_hour_time_to_24_hour_time_warns(self):
        """The 12h -> 24h helper is deprecated and must say so."""
        with self.assertWarns(DeprecationWarning):
            convert_12_hour_time_to_24_hour_time("01:10 AM")

    def test_convert_24_hour_time_to_12_hour_time_warns(self):
        """The 24h -> 12h helper is deprecated and must say so."""
        with self.assertWarns(DeprecationWarning):
            convert_24_hour_time_to_12_hour_time("13:00")


class ConvertMinutesInHumanReadableFormatTests(TestCase):
    def test_basic_conversions(self):
        """Test basic conversions"""
        self.assertEqual(convert_minutes_in_human_readable_format(30), "30 minutes")
        self.assertEqual(convert_minutes_in_human_readable_format(90), "1 hour and 30 minutes")

    def test_edge_cases(self):
        """Test edgy cases"""
        self.assertEqual(convert_minutes_in_human_readable_format(59), "59 minutes")
        self.assertEqual(convert_minutes_in_human_readable_format(60), "1 hour")
        self.assertEqual(convert_minutes_in_human_readable_format(1439), "23 hours and 59 minutes")
        # '1440' minutes is the total number of minutes in a day, hence it should convert to "1 day".
        self.assertEqual(convert_minutes_in_human_readable_format(1440), "1 day")

    def test_valid_combinations(self):
        """Test various combinations"""
        self.assertEqual(convert_minutes_in_human_readable_format(1441), "1 day and 1 minute")
        self.assertEqual(convert_minutes_in_human_readable_format(1500), "1 day and 1 hour")
        self.assertEqual(convert_minutes_in_human_readable_format(1560), "1 day and 2 hours")
        self.assertEqual(convert_minutes_in_human_readable_format(1501), "1 day, 1 hour and 1 minute")
        self.assertEqual(convert_minutes_in_human_readable_format(1562), "1 day, 2 hours and 2 minutes")
        self.assertEqual(convert_minutes_in_human_readable_format(808), "13 hours and 28 minutes")

    def test_non_positive_values(self):
        """Test that non-positive values are handled correctly"""
        self.assertEqual(convert_minutes_in_human_readable_format(0), "Not set.")
        # Expectation for negative values might depend on desired behavior, just an example below
        with self.assertRaises(ValueError):
            convert_minutes_in_human_readable_format(-5)

    def test_float_values(self):
        """Test float values which should be correctly rounded down"""
        self.assertEqual(convert_minutes_in_human_readable_format(2.5), "2 minutes")
        self.assertEqual(convert_minutes_in_human_readable_format(2.9), "2 minutes")

    def test_invalid_inputs(self):
        """Test invalid inputs which should raise an error"""
        with self.assertRaises(TypeError):
            convert_minutes_in_human_readable_format("30 minutes")
        with self.assertRaises(TypeError):
            convert_minutes_in_human_readable_format(["30"])
        with self.assertRaises(TypeError):
            convert_minutes_in_human_readable_format({"minutes": 30})
        with self.assertRaises(TypeError):
            convert_minutes_in_human_readable_format(None)


class ConvertStrToDateTests(TestCase):

    def test_valid_date_with_hyphen_separator(self):
        """Test valid date with hyphen separator works correctly"""
        self.assertEqual(convert_str_to_date("2023-12-31"), datetime.date(2023, 12, 31))
        self.assertEqual(convert_str_to_date("2020-02-29"), datetime.date(2020, 2, 29))  # Leap year
        self.assertEqual(convert_str_to_date("2021-02-28"), datetime.date(2021, 2, 28))

    def test_valid_date_with_slash_separator(self):
        """Test valid date with slash separator works correctly"""
        self.assertEqual(convert_str_to_date("2021/01/01"), datetime.date(2021, 1, 1))
        self.assertEqual(convert_str_to_date("2023/12/31"), datetime.date(2023, 12, 31))
        self.assertEqual(convert_str_to_date("2023.12.31"), datetime.date(2023, 12, 31))

    def test_invalid_date_formats(self):
        """The date format "MM-DD-YYY" & "DD/MM/YYYY" are not supported, hence it should raise an error."""
        with self.assertRaises(ValueError):
            convert_str_to_date("12-31-2023")
        with self.assertRaises(ValueError):
            convert_str_to_date("31/12/2023")

    def test_nonexistent_dates(self):
        """Test nonexistent dates"""
        with self.assertRaises(ValueError):
            convert_str_to_date("2023-02-30")
        with self.assertRaises(ValueError):
            convert_str_to_date("2021-02-29")  # Not a leap year

    def test_other_invalid_inputs(self):
        """Test other invalid inputs"""
        with self.assertRaises(ValueError):
            convert_str_to_date("")
        with self.assertRaises(ValueError):
            convert_str_to_date("RandomString")
        with self.assertRaises(ValueError):
            convert_str_to_date("0000-00-00")


class ConvertStrToTimeTests(TestCase):
    def test_12h_format_str_to_time(self):
        """Test valid time strings"""
        # These tests check if a 12-hour time format string converts correctly.
        self.assertEqual(convert_str_to_time("10:00 AM"), datetime.time(10, 0))
        self.assertEqual(convert_str_to_time("12:00 PM"), datetime.time(12, 0))
        self.assertEqual(convert_str_to_time("01:30 PM"), datetime.time(13, 30))

    def test_24h_format_str_to_time(self):
        """Test if a 24-hour time format string converts correctly."""
        # These tests check if a 24-hour time format string converts correctly.
        self.assertEqual(convert_str_to_time("10:00:00"), datetime.time(10, 0))
        self.assertEqual(convert_str_to_time("12:00:00"), datetime.time(12, 0))
        self.assertEqual(convert_str_to_time("13:30:00"), datetime.time(13, 30))

    def test_case_insensitivity_and_whitespace(self):
        """Test conversion handling of different case formats and white-space."""
        self.assertEqual(convert_str_to_time(" 12:00 am "), datetime.time(0, 0))
        self.assertEqual(convert_str_to_time("01:00 pM "), datetime.time(13, 0))
        self.assertEqual(convert_str_to_time(" 13:00:00 "), datetime.time(13, 0))

    def test_invalid_time_strings(self):
        """Test invalid time strings"""
        with self.assertRaises(ValueError):
            convert_str_to_time("")
        with self.assertRaises(ValueError):
            convert_str_to_time("13:00 PM")
        with self.assertRaises(ValueError):
            convert_str_to_time("25:00 AM")
        with self.assertRaises(ValueError):
            convert_str_to_time("25:00:00")
        with self.assertRaises(ValueError):
            convert_str_to_time("10:60 AM")
        with self.assertRaises(ValueError):
            convert_str_to_time("10:60:00")
        with self.assertRaises(ValueError):
            convert_str_to_time("Random String")


class GetAppointmentRequestEndTimeTests(TestCase):
    def test_get_ar_end_time_with_valid_inputs(self):
        """Test positive cases"""
        self.assertEqual(get_ar_end_time("10:00:00", 60), datetime.time(11, 0))
        self.assertEqual(get_ar_end_time(datetime.time(10, 0), 120), datetime.time(12, 0))
        self.assertEqual(get_ar_end_time(datetime.time(10, 0), datetime.timedelta(hours=2)), datetime.time(12, 0))

    def test_negative_duration(self):
        """Test negative duration"""
        with self.assertRaises(ValueError):
            get_ar_end_time("10:00:00", -60)

    def test_invalid_start_time_format(self):
        """Test invalid start time format"""
        with self.assertRaises(ValueError):
            get_ar_end_time("25:00:00", 60)

    def test_invalid_duration_format(self):
        """Test invalid duration format"""
        with self.assertRaises(TypeError):
            get_ar_end_time("10:00:00", "60")

    def test_end_time_past_midnight(self):
        """Test end time past midnight"""
        # If the end time goes past midnight, it should wrap around to the next day,
        # hence "23:30:00" + 60 minutes = "00:30:00".
        self.assertEqual(get_ar_end_time("23:30:00", 60), datetime.time(0, 30))

    def test_invalid_start_time_type(self):
        """Test that an invalid start_time type raises a TypeError."""
        with self.assertRaises(TypeError):
            get_ar_end_time([], 60)  # Passing a list instead of a datetime.time object or string
        with self.assertRaises(TypeError):
            get_ar_end_time(12345, 30)  # Passing an integer
        with self.assertRaises(TypeError):
            get_ar_end_time(None, 30)  # Passing None


class TimeDifferenceTests(TestCase):

    def test_difference_with_time_objects(self):
        """Test difference between two time objects"""
        time1 = datetime.time(10, 0)
        time2 = datetime.time(11, 0)
        difference = time_difference(time1, time2)
        self.assertEqual(difference, datetime.timedelta(hours=1))

    def test_difference_with_datetime_objects(self):
        """Test difference between two datetime objects"""
        datetime1 = datetime.datetime(2023, 1, 1, 10, 0)
        datetime2 = datetime.datetime(2023, 1, 1, 11, 0)
        difference = time_difference(datetime1, datetime2)
        self.assertEqual(difference, datetime.timedelta(hours=1))

    def test_negative_difference_with_time_objects(self):
        """Two time objects cannot have a negative difference"""
        time1 = datetime.time(10, 0)
        time2 = datetime.time(11, 0)
        with self.assertRaises(ValueError):
            time_difference(time2, time1)

    def test_negative_difference_with_datetime_objects(self):
        """Two datetime objects cannot have a negative difference"""
        datetime1 = datetime.datetime(2023, 1, 1, 10, 0)
        datetime2 = datetime.datetime(2023, 1, 1, 11, 0)
        with self.assertRaises(ValueError):
            time_difference(datetime2, datetime1)

    def test_mismatched_input_types(self):
        """Test that providing one 'datetime.time' and one datetime.datetime raises a ValueError."""
        time_obj = datetime.time(10, 0)
        datetime_obj = datetime.datetime(2023, 1, 1, 11, 0)

        with self.assertRaises(ValueError) as context:
            time_difference(time_obj, datetime_obj)

        self.assertEqual(str(context.exception),
                         "Both inputs should be of the same type, either datetime.time or datetime.datetime")

        # Test the reverse case as well for completeness
        with self.assertRaises(ValueError) as context:
            time_difference(datetime_obj, time_obj)

        self.assertEqual(str(context.exception),
                         "Both inputs should be of the same type, either datetime.time or datetime.datetime")


class CombineDateAndTimeTests(TestCase):
    def test_valid_date_and_time(self):
        """Test combining a valid date and time."""
        date = datetime.date(2023, 1, 1)
        time = datetime.time(12, 30)
        expected_datetime = datetime.datetime(2023, 1, 1, 12, 30)
        result = combine_date_and_time(date, time)
        self.assertEqual(result, expected_datetime)

    def test_combine_with_midnight(self):
        """Test combining a date with a midnight time."""
        date = datetime.date(2023, 1, 1)
        time = datetime.time(0, 0)
        expected_datetime = datetime.datetime(2023, 1, 1, 0, 0)
        result = combine_date_and_time(date, time)
        self.assertEqual(result, expected_datetime)

    def test_combine_with_leap_year_date(self):
        """Test combining a leap year date and time."""
        date = datetime.date(2024, 2, 29)
        time = datetime.time(23, 59)
        expected_datetime = datetime.datetime(2024, 2, 29, 23, 59)
        result = combine_date_and_time(date, time)
        self.assertEqual(result, expected_datetime)

    def test_combine_with_end_of_day(self):
        """Test combining a date with 'end of day time'."""
        date = datetime.date(2023, 1, 1)
        time = datetime.time(23, 59, 59)
        expected_datetime = datetime.datetime(2023, 1, 1, 23, 59, 59)
        result = combine_date_and_time(date, time)
        self.assertEqual(result, expected_datetime)

    def test_combine_with_microseconds(self):
        """Test combining a date and time with microseconds."""
        date = datetime.date(2023, 1, 1)
        time = datetime.time(12, 30, 15, 123456)
        expected_datetime = datetime.datetime(2023, 1, 1, 12, 30, 15, 123456)
        result = combine_date_and_time(date, time)
        self.assertEqual(result, expected_datetime)


class TimestampTests(TestCase):
    @patch('appointment.utils.date_time.timezone.now')
    def test_get_timestamp(self, mock_now):
        """Test get_timestamp function"""
        mock_datetime = Mock()
        mock_datetime.timestamp.return_value = 1612345678.1234  # Sample timestamp with decimal
        mock_now.return_value = mock_datetime

        self.assertEqual(get_timestamp(), "16123456781234")


class GeneralDateTimeTests(TestCase):
    def test_get_current_year(self):
        """Test get_current_year function"""
        self.assertEqual(get_current_year(), timezone.localdate().year)

    def test_get_current_year_mocked(self):
        """Test get_current_year function with a mocked year."""
        with patch('appointment.utils.date_time.timezone.localdate', return_value=datetime.date(1999, 12, 31)):
            self.assertEqual(get_current_year(), 1999)

    def test_get_weekday_num(self):
        """Test get_weekday_num function with valid input"""
        self.assertEqual(get_weekday_num("Monday"), 1)
        self.assertEqual(get_weekday_num("Sunday"), 0)

    def test_invalid_get_weekday_num(self):
        """Test get_weekday_num function with invalid input which should return -1"""
        self.assertEqual(get_weekday_num("InvalidDay"), -1)


class DateFormatsTests(TestCase):
    """Every entry of DATE_FORMATS must format a date: letters meant as text have to be escaped."""

    def test_every_format_works_on_a_date(self):
        from django.utils import translation
        from django.utils.formats import date_format
        day = datetime.date(2025, 8, 14)
        for lang, fmt in DATE_FORMATS.items():
            with self.subTest(lang=lang), translation.override(lang):
                date_format(day, fmt, use_l10n=True)

    def test_portuguese_keeps_the_word_de(self):
        from django.utils import translation
        from django.utils.formats import date_format
        with translation.override('pt-br'):
            self.assertEqual(date_format(datetime.date(2025, 8, 14), DATE_FORMATS['pt'], use_l10n=True),
                             "Qui, 14 de Agosto de 2025")

    def test_long_date_format_follows_the_language(self):
        from django.utils import translation
        for lang, expected in (('en', DATE_FORMATS['en']), ('fr', DATE_FORMATS['fr']), ('pt-br', DATE_FORMATS['pt']),
                               ('xx', "D, F j, Y")):
            with self.subTest(lang=lang), translation.override(lang):
                self.assertEqual(long_date_format(), expected)

    def test_long_date_filter(self):
        from django.template import Context, Template
        from django.utils import translation
        template = Template('{% load appointment_tags %}{{ day|long_date }}|{{ empty|long_date }}')
        with translation.override('fr'):
            self.assertEqual(template.render(Context({'day': datetime.date(2025, 8, 14), 'empty': None})),
                             "Jeu 14 août 2025|")


class ClientTimeTextTests(TestCase):
    """The client's own time is shown only when their clock differs from the site's (TIME_ZONE is UTC in tests)."""
    date = datetime.date(2026, 11, 24)
    start = datetime.time(9, 0)

    def test_other_offset_shows_the_client_time(self):
        text = get_client_time_text('America/New_York', self.date, self.start)
        self.assertIn('(America/New_York)', text)
        self.assertIn('4', text)  # 9:00 UTC is 4:00 in New York in November

    def test_same_offset_shows_nothing(self):
        self.assertIsNone(get_client_time_text('UTC', self.date, self.start))
        self.assertIsNone(get_client_time_text('Europe/London', self.date, self.start))  # UTC+0 in November

    def test_unknown_or_missing_time_zone_shows_nothing(self):
        for name in ('', None, 'Not/A_Zone', '../../etc/passwd', 'x' * 100):
            self.assertIsNone(get_client_time_text(name, self.date, self.start))

    def test_valid_timezone_name(self):
        self.assertEqual(get_valid_timezone_name('Australia/Sydney'), 'Australia/Sydney')
        self.assertEqual(get_valid_timezone_name('Mars/Olympus'), '')
        self.assertEqual(get_valid_timezone_name(42), '')


class GregorianToJalaliTests(TestCase):
    def test_known_dates(self):
        for day, expected in (
                (datetime.date(1979, 2, 11), (1357, 11, 22)),
                (datetime.date(1996, 3, 20), (1375, 1, 1)),  # Nowruz, the first day of the year
                (datetime.date(2025, 3, 20), (1403, 12, 30)),  # last day of a leap year
                (datetime.date(2025, 3, 21), (1404, 1, 1)),
                (datetime.date(2026, 11, 25), (1405, 9, 4)),
                (datetime.date(2100, 3, 21), (1479, 1, 1)),
        ):
            with self.subTest(day=day):
                self.assertEqual(gregorian_to_jalali(day), expected)

    def test_days_follow_each_other(self):
        """From 1990 to 2060, each day is the next day of the same month, or the first day of the next month."""
        day = datetime.date(1990, 1, 1)
        previous = gregorian_to_jalali(day)
        while day < datetime.date(2060, 1, 1):
            day += datetime.timedelta(days=1)
            current = gregorian_to_jalali(day)
            year, month, day_of_month = previous
            if current[2] == 1:
                # The month that ended had its full length
                lengths = (31,) if month <= 6 else (30,) if month <= 11 else (29, 30)
                self.assertIn(day_of_month, lengths)
                self.assertEqual(current[:2], (year + 1, 1) if month == 12 else (year, month + 1))
            else:
                self.assertEqual(current, (year, month, day_of_month + 1))
            previous = current


class LocalDateFormatTests(TestCase):
    """Persian dates are in the Jalali calendar with Persian digits; other languages keep Django's date_format."""
    day = datetime.date(2025, 8, 14)

    def test_other_languages_are_unchanged(self):
        from django.utils import translation
        from django.utils.formats import date_format
        for lang in ('en', 'fr', 'ar'):
            with self.subTest(lang=lang), translation.override(lang):
                self.assertEqual(local_date_format(self.day, long_date_format()),
                                 date_format(self.day, long_date_format(), use_l10n=True))
                self.assertEqual(local_date_format(self.day), date_format(self.day, use_l10n=True))

    def test_persian_uses_the_jalali_calendar(self):
        from django.utils import translation
        with translation.override('fa'):
            self.assertEqual(local_date_format(self.day, long_date_format()), "پنجشنبه، ۲۳ مرداد ۱۴۰۴")
            self.assertEqual(local_date_format(self.day, "d/m/y"), "۲۳/۰۵/۰۴")
            # Escaped letters stay text, and the time is unchanged
            self.assertEqual(local_date_format(datetime.datetime(2025, 8, 14, 9, 5), r"\Y j، H:i"), "Y ۲۳، ۰۹:۰۵")

    def test_local_date_filter(self):
        from django.template import Context, Template
        from django.utils import translation
        template = Template('{% load appointment_tags %}{{ day|local_date:"j F Y" }}|{{ empty|local_date }}')
        context = Context({'day': self.day, 'empty': None})
        with translation.override('fa'):
            self.assertEqual(template.render(context), "۲۳ مرداد ۱۴۰۴|")
        with translation.override('en'):
            self.assertEqual(template.render(context), "14 August 2025|")


class LocalDigitsTests(TestCase):
    """Persian writes times, durations and prices with Persian digits; other languages keep theirs."""

    def test_local_digits(self):
        from django.utils import translation
        with translation.override('fa'):
            self.assertEqual(local_digits('10:30'), '۱۰:۳۰')
        with translation.override('en'):
            self.assertEqual(local_digits('10:30'), '10:30')

    def test_local_time_filter(self):
        from django.template import Context, Template
        from django.utils import translation
        template = Template('{% load appointment_tags %}{{ start|local_time:"H:i" }}|{{ empty|local_time }}')
        context = Context({'start': datetime.time(9, 5), 'empty': None})
        with translation.override('fa'):
            self.assertEqual(template.render(context), '۰۹:۰۵|')
        with translation.override('en'):
            self.assertEqual(template.render(context), '09:05|')

    def test_durations(self):
        from django.utils import translation
        with translation.override('fa'):
            self.assertNotRegex(convert_minutes_in_human_readable_format(90), '[0-9]')
        with translation.override('en'):
            self.assertEqual(convert_minutes_in_human_readable_format(90), '1 hour and 30 minutes')
