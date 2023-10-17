# date_time.py
# Path: appointment/utils/date_time.py

"""
Author: Adams Pierre David
Since: 2.0.0
"""

import datetime

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from appointment.settings import APP_TIME_ZONE


def convert_12_hour_time_to_24_hour_time(time_to_convert) -> str:
    """Convert a 12-hour time to a 24-hour time.

    :param time_to_convert: The time to convert.
    :return: The converted time.
    :raises ValueError: If the input time is not in the correct format or is invalid.
    """
    if isinstance(time_to_convert, (datetime.datetime, datetime.time)):
        return time_to_convert.strftime('%H:%M:%S')
    elif isinstance(time_to_convert, str):
        try:
            time_str = time_to_convert.strip().upper()
            return datetime.datetime.strptime(time_str, '%I:%M %p').strftime('%H:%M:%S')
        except ValueError:
            raise ValueError(f"Invalid 12-hour time format: {time_to_convert}")
    else:
        raise ValueError(f"Unsupported data type for time conversion: {type(time_to_convert)}")


def convert_minutes_in_human_readable_format(minutes: float) -> str:
    """Convert a number of minutes in a human-readable format.

    :param minutes: The number of minutes to convert.
    :return: The converted minutes in a human-readable format.
    """
    if minutes == 0:
        return _("Not set.")
    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")
    days, minutes = divmod(int(minutes), 1440)
    hours, minutes = divmod(int(minutes), 60)

    def format_unit(value, single_name, plural_name):
        return _("{value} {name}").format(value=value, name=single_name if value <= 1 else plural_name)

    parts = []
    if days:
        parts.append(format_unit(days, "day", "days"))
    if hours:
        parts.append(format_unit(hours, "hour", "hours"))
    if minutes:
        parts.append(format_unit(minutes, "minute", "minutes"))
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return _(" and ").join(parts)
    elif len(parts) == 3:
        return _("{days}, {hours} and {minutes}").format(days=parts[0], hours=parts[1], minutes=parts[2])
    else:
        return ""


def convert_str_to_date(date_str: str) -> datetime.date:
    """Convert a date string to a datetime date object.

    :param date_str: The date string.
                     Supported formats include '%Y-%m-%d' (like "2023-12-31") and '%Y/%m/%d' (like "2023/12/31").
    :return: datetime.date, the converted date
    """
    date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d']

    for fmt in date_formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"Invalid date format for '{date_str}'. Supported formats are YYYY-MM-DD and YYYY/MM/DD.")


def convert_str_to_time(time_str: str) -> datetime.time:
    """Convert a string representation of time to a Python `time` object.

    The function tries both 12-hour and 24-hour formats.

    :param time_str: A string representation of time.
    :return: A Python `time` object.
    """
    formats = ["%I:%M %p", "%H:%M:%S"]

    for fmt in formats:
        try:
            return datetime.datetime.strptime(time_str.strip().upper(), fmt).time()
        except ValueError:
            pass

    raise ValueError(
        f"Invalid time format for '{time_str}'. Expected either a 12-hour (e.g., '10:00 AM') or 24-hour (e.g., "
        f"'13:00:00') format.")


def get_ar_end_time(start_time, duration) -> datetime.time:
    """Get the end time of an appointment request based on the start time and the duration.

    :param start_time: The start time of the appointment request.
    :param duration: The duration in minutes or as timedelta of the appointment request.
    :return: The end time of the appointment request.
    """
    # Check types
    if not isinstance(start_time, (datetime.time, str)):
        raise TypeError("start_time must be a datetime.time object or a string in 'HH:MM:SS' format.")

    if not isinstance(duration, (datetime.timedelta, int, float)):
        raise TypeError("duration must be either a datetime.timedelta or a numeric type representing minutes.")

    if isinstance(duration, (int, float)) and duration < 0:
        raise ValueError("duration cannot be negative.")

    # Convert the time object to a datetime object
    if isinstance(start_time, str):
        start_time = convert_str_to_time(start_time)

    dt_start_time = datetime.datetime.combine(datetime.datetime.today(), start_time)

    # Convert duration to minutes if it's a timedelta
    if isinstance(duration, datetime.timedelta):
        duration_minutes = duration.total_seconds() / 60
    else:
        duration_minutes = int(duration)

    # Add the duration
    dt_end_time = dt_start_time + datetime.timedelta(minutes=duration_minutes)

    # If end time goes past midnight, wrap it around
    if dt_end_time.day > dt_start_time.day:
        dt_end_time = dt_end_time - datetime.timedelta(days=1)

    return dt_end_time.time()


def get_timezone() -> str:
    """Return the current timezone of the application."""
    return APP_TIME_ZONE


def get_timestamp() -> str:
    """Get the current timestamp as a string without the decimal part.

    :return: The current timestamp (e.g. "1612345678")
    """
    timestamp = str(timezone.now().timestamp())
    return timestamp.replace('.', '')


def get_current_year() -> int:
    """Get the current year as an integer.

    :return: The current year
    """
    return datetime.datetime.now().year


def get_weekday_num(weekday: str) -> int:
    """Get the number of the weekday.

    :param weekday: The weekday (e.g. "Monday", "Tuesday", etc.)
    :return: The number of the weekday (0 for Sunday, 1 for Monday, etc.)
    """
    weekdays = {
        'monday': 1,
        'tuesday': 2,
        'wednesday': 3,
        'thursday': 4,
        'friday': 5,
        'saturday': 6,
        'sunday': 0
    }
    return weekdays.get(weekday.lower(), -1)


def time_difference(time1, time2):
    # If inputs are datetime.time objects, convert them to datetime.datetime objects for the same day
    if isinstance(time1, datetime.time) and isinstance(time2, datetime.time):
        today = datetime.datetime.today()
        datetime1 = datetime.datetime.combine(today, time1)
        datetime2 = datetime.datetime.combine(today, time2)
    elif isinstance(time1, datetime.datetime) and isinstance(time2, datetime.datetime):
        datetime1 = time1
        datetime2 = time2
    else:
        raise ValueError("Both inputs should be of the same type, either datetime.time or datetime.datetime")

    # Check if datetime2 is earlier than datetime1
    if datetime2 < datetime1:
        raise ValueError("The second time provided (time2) should not be earlier than the first time (time1).")

    # Find the difference
    delta = datetime2 - datetime1

    return delta
