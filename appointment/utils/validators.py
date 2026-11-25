import re
import unicodedata

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

BOOKING_CONTEXT_MAX_LENGTH = 200
BOOKING_CONTEXT_KEY_PATTERN = re.compile(r'[a-z][a-z0-9_]{0,49}')


def not_in_the_past(date):
    if date < timezone.localdate():
        raise ValidationError(_('Date is in the past'))


def get_booking_context_keys():
    keys = getattr(settings, 'APPOINTMENT_BOOKING_CONTEXT_KEYS', ())
    if isinstance(keys, (str, bytes)) or not all(
            isinstance(key, str) and BOOKING_CONTEXT_KEY_PATTERN.fullmatch(key) for key in keys):
        raise ImproperlyConfigured(
            "APPOINTMENT_BOOKING_CONTEXT_KEYS must be a list of lowercase names made of letters, digits and "
            "underscores, starting with a letter, 50 characters at most.")
    return frozenset(keys)


def validate_booking_context(value):
    """Allow only a flat dict of short, printable strings under allowed keys. Errors never repeat a value."""
    if value is None:
        return
    if not isinstance(value, dict):
        raise ValidationError(_("The booking context must be a flat object of text values."), code='invalid')
    allowed = get_booking_context_keys()
    unknown = sum(1 for key in value if key not in allowed)
    if unknown:
        raise ValidationError(
            _("The booking context has %(count)d key(s) that are not in APPOINTMENT_BOOKING_CONTEXT_KEYS."),
            code='unknown_key', params={'count': unknown})
    for key, text in value.items():
        if not isinstance(text, str):
            raise ValidationError(_("The booking context value for '%(key)s' must be text."),
                                  code='invalid_value', params={'key': key})
        if len(text) > BOOKING_CONTEXT_MAX_LENGTH:
            raise ValidationError(_("The booking context value for '%(key)s' is longer than %(max)d characters."),
                                  code='too_long', params={'key': key, 'max': BOOKING_CONTEXT_MAX_LENGTH})
        # Control, invisible and unassigned characters
        if any(unicodedata.category(char).startswith('C') for char in text):
            raise ValidationError(_("The booking context value for '%(key)s' has characters that are not allowed."),
                                  code='invalid_character', params={'key': key})
