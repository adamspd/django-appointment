from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def not_in_the_past(date):
    if date < date.today():
        raise ValidationError(_('Date is in the past'))
