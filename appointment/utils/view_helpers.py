# view_helpers.py
# Path: appointment/view_helpers.py

"""
Author: Adams Pierre David
Since: 2.0.0
"""

import uuid

from django.utils.translation import to_locale, get_language

from appointment.settings import APP_TIME_ZONE


def get_locale() -> str:
    """Get the current locale based on the user's language settings, without the country code.
    Used in the javascript files.
    Can't use the lang_country format because it is not supported.

    :return: The current locale as a string (language code only)
    """
    locale = to_locale(get_language())
    # Split the locale by '_' and take the first part (language code)
    return locale.split('_')[0]


def is_ajax(request):
    """Check if the request is an AJAX request.

    :param request: HttpRequest object
    :return: bool, True if the request is an AJAX request, False otherwise
    """
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def generate_random_id() -> str:
    """Generate a random UUID and return it as a hexadecimal string.

    :return: The randomly generated UUID as a hex string
    """
    return uuid.uuid4().hex


def get_timezone_txt() -> str:
    # TODO: To be better implemented in the future
    """Get the current timezone as a string. To be used in the HTML template when the user is choosing the appointment's
    time.

    :return: The current timezone in a string format.
    """
    tmz = APP_TIME_ZONE
    timezone_map = {
        'UTC': 'Universal Time Coordinated (UTC)',
        'US/Eastern': 'Eastern Daylight Time (US & Canada)',
        'US/Central': 'Central Time (US & Canada)',
        'US/Mountain': 'Mountain Time (US & Canada)',
        'US/Pacific': 'Pacific Time (US & Canada)',
        'US/Alaska': 'Alaska Time (US & Canada)',
        'US/Hawaii': 'Hawaii Time (US & Canada)',
        'Europe/Paris': 'Paris Time (Europe)',
        'Europe/London': 'London Time (Europe)',
        'EDT': 'Eastern Daylight Time (US & Canada)',
    }
    return timezone_map.get(tmz, 'Universal Time Coordinated (UTC)')
