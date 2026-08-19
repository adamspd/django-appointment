# date_time.py
# Path: appointment/utils/date_time.py

"""
Author: Adams Pierre David
Since: 2.0.0
"""

import datetime

from django.utils import timezone
from django.utils.formats import get_format
from django.utils.translation import gettext_lazy as _, ngettext

def js_timepicker_display_format():
    """Convert a localized time format to its Moment.js representation

    :return: The js format converted from timeformat
    """
    # P     -> h:mm a
    # f     -> h:mm
    # H:i   -> HH:mm
    # h:ia  -> hh:mma
    # h:i a -> hh:mm a
    # h:i A -> hh:mm A
    # G:i   -> H:mm
    # G.i   -> H.mm
    # g:i A -> h.mm A
    # g.i.a -> h.mm.a
    # A g:i -> A h.mm
    # H\xa0h\xa0i -> h cannot be sperator in js -> force HH:mm (fr_CA)

    DJANGO_TO_MOMENTS = {
        #"a": "a", no changes
        #"A": "A",
        "g": "h",
        "G": "H",
        "h": "hh",
        "H": "HH",
        "i": "mm",
        "s": "ss", # unused for now
    }

    DJANGO_COMPOSITES = {
        "P": "h:mm a",
        "f": "h:mm",
        #"c", datetime
        #"r", datetime
    }

    localized_time_format = get_format("TIME_FORMAT")
    print(localized_time_format)

    # handle fr_CA
    filtered_localized_time_format = localized_time_format.replace("\xa0h", ":").replace("\xa0", "")

    result = []
    for char in filtered_localized_time_format:
        if char in DJANGO_COMPOSITES:
            result.append(DJANGO_COMPOSITES[char])
        elif char in DJANGO_TO_MOMENTS:
            result.append(DJANGO_TO_MOMENTS[char])
        else:
            result.append(char)

    return "".join(result)


def combine_date_and_time(date, time) -> datetime.datetime:
    """Combine a date and a time into a datetime object.

    :param date: The date.
    :param time: The time.
    :return: A datetime object.
    """
    return datetime.datetime.combine(date, time)

def convert_ap_str_time_to_12_hour_str_time(time_str: str) -> str:
    """Convert a Associated Press 12-hour time to a 12-hour time format if needed
    
    :param time_str: The time str to convert.
    :return: The converted time.
    """
    #handle 10 a.m./ 15:25 p.m. format (django TIME_FORMAT "P", locale en)
    time_str = time_str.strip().upper()
    if (time_str == "NOON"):
        return "12:00 PM"
    elif (time_str == "MIDNIGHT"):
        return "12:00 AM"

    time_str_modifier = time_str[-4:]
    if (time_str_modifier == "A.M."):
        if ":" in time_str:
            #if xx:xx we match "%I:%M %p" format
            time_str = f"{time_str[:-5]} AM"
        else:
            #else we add :00 for 10 a.m. -> 10:00 AM case
            time_str = f"{time_str[:-5]}:00 AM"
    elif (time_str_modifier == "P.M."):
        if ":" in time_str:
            time_str = f"{time_str[:-5]} PM"
        else:
            time_str = f"{time_str[:-5]}:00 PM"

    return time_str


def convert_minutes_in_human_readable_format(minutes: float) -> str:
    """Convert a number of minutes in a human-readable format.

    :param minutes: The number of minutes to convert.
    :return: The converted minutes in a human-readable format.
    """
    if minutes == 0:
        return _("Not set.")
    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")
    days, remaining_minutes = divmod(int(minutes), 1440)
    hours, minutes = divmod(int(remaining_minutes), 60)

    parts = []
    if days:
        days_display = ngettext("%(count)d day", "%(count)d days", days) % {'count': days}
        parts.append(days_display)

    if hours:
        hours_display = ngettext("%(count)d hour", "%(count)d hours", hours) % {'count': hours}
        parts.append(hours_display)

    if minutes:
        minutes_display = ngettext("%(count)d minute", "%(count)d minutes", minutes) % {'count': minutes}
        parts.append(minutes_display)

    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return _("{first_part} and {second_part}").format(first_part=parts[0], second_part=parts[1])
    elif len(parts) == 3:
        return _("{days}, {hours} and {minutes}").format(days=parts[0], hours=parts[1], minutes=parts[2])

# TODO if required add support for locale format using : get_format('DATE_INPUT_FORMAT')
# but we have to discernate year first, month first or day first format properly
def convert_str_to_date(date_str: str) -> datetime.date:
    """Convert a date string to a datetime date object.

    :param date_str: The date string.
                     Supported formats include `%Y-%m-%d` (like "2023-12-31"), `%Y/%m/%d` (like "2023/12/31") and `%Y.%m.%d` (like "2023.12.31").
    :return: The converted `datetime.date`'s object.
    """
    date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d']

    for fmt in date_formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"Invalid date format for '{date_str}'. Supported formats are `YYYY-MM-DD`, `YYYY/MM/DD` and `YYYY.MM.DD`.")

# TODO if required add support for locale format using : get_format('TIME_INPUT_FORMAT')
def convert_str_to_time(time_str: str) -> datetime.time:
    """Convert a string representation of time to a Python `time` object.

    The function tries both 12-hour and 24-hour formats.

    :param time_str: A string representation of time.
    :return: A Python `time` object.
    """
    normalized_time = convert_ap_str_time_to_12_hour_str_time(time_str)

    time_formats = ["%I:%M %p", "%H:%M:%S", "%H:%M"]

    for fmt in time_formats:
        try:
            return datetime.datetime.strptime(normalized_time, fmt).time()
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


DATE_FORMATS = {
    'ar': "D، j F Y",                        # "خ، 14 أغسطس 2025" (Arabic: RTL with Arabic comma)
    'bg': "D, j F Y",                        # "чт, 14 август 2025" (Bulgarian: comma after weekday)
    'bn': "D, j F Y",                        # "বৃহ, 14 আগস্ট 2025" (Bengali: comma after weekday)
    'cs': "D j. F Y",                        # "čt 14. srpna 2025" (Czech: period after day)
    'da': "D j. F Y",                        # "tor 14. august 2025" (Danish: period after day)
    'de': "D, j. F Y",                       # "Do, 14. August 2025" (German: period after day)
    'el': "D, j F Y",                        # "Πέμ, 14 Αυγούστου 2025" (Greek: comma after weekday)
    'en': "D, F j, Y",                       # "Thu, August 14, 2025" (English: commas)
    'es': r"D, j \d\e F \d\e Y",               # "jue, 14 de agosto de 2025" (Spanish: with "de")
    'et': "D, j. F Y",                       # "N, 14. august 2025" (Estonian: period after day)
    'fa': "D، j F Y",                        # "پ، 14 اوت 2025" (Persian: RTL with Persian comma)
    'fi': "D j. Fta Y",                      # "to 14. elokuuta 2025" (Finnish: partitive case for month)
    'fr': "D j F Y",                         # "jeu 14 août 2025" (French: no comma, day before month)
    'he': "D، j בF Y",                       # "ה، 14 באוגוסט 2025" (Hebrew: RTL format)
    'hi': "D, j F Y",                        # "गुरु, 14 अगस्त 2025" (Hindi: comma after weekday)
    'hr': "D, j. F Y.",                      # "čet, 14. kolovoza 2025." (Croatian: periods)
    'hu': "Y. F j., D",                      # "2025. augusztus 14., csütörtök" (Hungarian: year first)
    'id': "D, j F Y",                        # "Kam, 14 Agustus 2025" (Indonesian: comma after weekday)
    'it': "D j F Y",                         # "gio 14 agosto 2025" (Italian: no comma, day before month)
    'ja': "Y年Fj日(D)",                       # "2025年八月14日(木)" (Japanese: weekday in parentheses)
    'ko': "Y년 F j일 D",                      # "2025년 8월 14일 목요일" (Korean: spaces between elements)
    'lt': "Y m. F j d., D",                  # "2025 m. rugpjūčio 14 d., ketvirtadienis" (Lithuanian: unique format)
    'lv': r"D, Y. \gada j. F",               # "ceturtd, 2025. gada 14. augusts" (Latvian: unique format)
    'ms': "D, j F Y",                        # "Kha, 14 Ogos 2025" (Malay: comma after weekday)
    'nl': "D j F Y",                         # "do 14 augustus 2025" (Dutch: no comma, day before month)
    'no': "D j. F Y",                        # "tor 14. august 2025" (Norwegian: period after day)
    'pl': "D, j F Y",                        # "czw, 14 sierpnia 2025" (Polish: comma after weekday)
    'pt': r"D, j \de F \de Y",               # "qui, 14 de agosto de 2025" (Portuguese: with "de")
    'ro': "D, j F Y",                        # "joi, 14 august 2025" (Romanian: comma after weekday)
    'ru': "D, j F Y",                        # "чт, 14 август 2025" (Russian: comma after weekday)
    'sk': "D j. F Y",                        # "št 14. augusta 2025" (Slovak: period after day)
    'sl': "D, j. F Y",                       # "čet, 14. avgusta 2025" (Slovenian: period after day)
    'sr': "D, j. F Y.",                      # "чет, 14. августа 2025." (Serbian: periods)
    'sv': "D j F Y",                         # "tors 14 augusti 2025" (Swedish: no comma, day before month)
    'th': r"D\ที่ j F Y",                     # "พฤหัสที่ 14 สิงหาคม 2025" (Thai: with Thai characters)
    'tr': "j F Y D",                         # "14 Ağustos 2025 Perşembe" (Turkish: day-month-year weekday)
    'uk': "D, j F Y",                        # "чт, 14 серпня 2025" (Ukrainian: comma after weekday)
    'vi': r"D, \ngày j \tháng n \năm Y",     # "Th 5, ngày 14 tháng 8 năm 2025" (Vietnamese: with words; corrected to use n for numeric month)
    'zh': "Y年Fj日 D",                        # "2025年八月14日 星期四" (Chinese: year-month-day format)
}
