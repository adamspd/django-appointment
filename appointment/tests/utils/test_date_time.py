import datetime
from unittest.mock import Mock, patch

from django.test import TestCase

from appointment.settings import APP_TIME_ZONE
from appointment.utils.date_time import convert_12_hour_time_to_24_hour_time, \
    convert_str_to_date, convert_str_to_time, get_ar_end_time, time_difference, get_timezone, get_current_year, \
    get_weekday_num, get_timestamp, convert_minutes_in_human_readable_format


class Convert12HourTo24HourTimeTests(TestCase):
    def test_valid_basic_conversion(self):
        """Test basic 12-hour to 24-hour conversions."""
        self.assertEqual(convert_12_hour_time_to_24_hour_time("01:10 AM"), "01:10:00")
        self.assertEqual(convert_12_hour_time_to_24_hour_time("01:20 PM"), "13:20:00")

    def test_convert_midnight_and_noon(self):
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

    def test_out_of_bounds_values(self):
        """Test conversion with out-of-bounds values."""
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("13:00 PM")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("12:60 AM")

    def test_invalid_datatypes(self):
        """Test conversion with invalid data types."""
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time(["12:00 AM"])
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time({"time": "12:00 AM"})

    def test_invalid_inputs(self):
        """Test conversion with various invalid inputs."""
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("25:00 AM")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("01:00")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("Random String")
        with self.assertRaises(ValueError):
            convert_12_hour_time_to_24_hour_time("01:60 AM")


class ConvertMinutesInHumanReadableFormatTests(TestCase):
    def test_valid_basic_conversions(self):
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

    def test_valid_date_strings_with_hyphen_separator(self):
        """Test valid date with hyphen separator works correctly"""
        self.assertEqual(convert_str_to_date("2023-12-31"), datetime.date(2023, 12, 31))
        self.assertEqual(convert_str_to_date("2020-02-29"), datetime.date(2020, 2, 29))  # Leap year
        self.assertEqual(convert_str_to_date("2021-02-28"), datetime.date(2021, 2, 28))

    def test_valid_date_strings_with_slash_separator(self):
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
    def test_convert_12h_format_str_to_time(self):
        """Test valid time strings"""
        # These tests check if a 12-hour time format string converts correctly.
        self.assertEqual(convert_str_to_time("10:00 AM"), datetime.time(10, 0))
        self.assertEqual(convert_str_to_time("12:00 PM"), datetime.time(12, 0))
        self.assertEqual(convert_str_to_time("01:30 PM"), datetime.time(13, 30))

    def test_convert_24h_format_str_to_time(self):
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

    def test_convert_str_to_time_invalid(self):
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
            convert_str_to_time("10:00")
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


class TimeDifferenceTests(TestCase):

    def test_valid_difference_with_time_objects(self):
        """Test difference between two time objects"""
        time1 = datetime.time(10, 0)
        time2 = datetime.time(11, 0)
        difference = time_difference(time1, time2)
        self.assertEqual(difference, datetime.timedelta(hours=1))

    def test_valid_difference_with_datetime_objects(self):
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


class TimestampTests(TestCase):
    @patch('appointment.utils.date_time.timezone.now')
    def test_get_timestamp(self, mock_now):
        """Test get_timestamp function"""
        mock_datetime = Mock()
        mock_datetime.timestamp.return_value = 1612345678.1234  # Sample timestamp with decimal
        mock_now.return_value = mock_datetime

        self.assertEqual(get_timestamp(), "16123456781234")


class GeneralDateTimeTests(TestCase):
    def test_get_timezone(self):
        """Test get_timezone function"""
        self.assertEqual(get_timezone(), APP_TIME_ZONE)

    def test_get_current_year(self):
        """Test get_current_year function"""
        self.assertEqual(get_current_year(), datetime.datetime.now().year)

    def test_get_current_year_mocked(self):
        """Test get_current_year function with a mocked year."""
        with patch('appointment.utils.date_time.datetime.datetime') as mock_date:
            mock_date.now.return_value.year = 1999  # Setting year attribute of the mock object
            self.assertEqual(get_current_year(), 1999)

    @patch('appointment.utils.date_time.APP_TIME_ZONE', new="Asia/Tokyo")
    def test_get_timezone_with_modified_setting(self):
        """Test get_timezone function with a modified timezone setting."""
        self.assertEqual(get_timezone(), "Asia/Tokyo")

    def test_get_weekday_num(self):
        """Test get_weekday_num function with valid input"""
        self.assertEqual(get_weekday_num("Monday"), 1)
        self.assertEqual(get_weekday_num("Sunday"), 0)

    def test_invalid_get_weekday_num(self):
        """Test get_weekday_num function with invalid input which should return -1"""
        self.assertEqual(get_weekday_num("InvalidDay"), -1)
