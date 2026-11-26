# appointment_tags.py
# Path: appointment/templatetags/appointment_tags.py

"""
Template tags the package's own templates use: {% load appointment_tags %}.

Author: Adams Pierre David
Since: 3.13.0
"""

from django import template

from appointment.utils.date_time import local_date_format, long_date_format

register = template.Library()


@register.filter(expects_localtime=True, is_safe=False)
def local_date(value, format=None):
    """Like the date filter, but in the Jalali calendar for Persian. Empty for an empty value."""
    if value in (None, ''):
        return ''
    return local_date_format(value, format)


@register.filter(expects_localtime=True, is_safe=False)
def long_date(value):
    """The date with its weekday, in the active language's format from DATE_FORMATS ("Thu, August 14, 2025")."""
    if value in (None, ''):
        return ''
    return local_date_format(value, long_date_format())


@register.simple_tag(takes_context=True)
def first_time(context, key):
    """True the first time it runs with ``key`` in a request, False after: to render a shared element only once."""
    request = context.get('request')
    if request is None:
        return True
    seen = getattr(request, '_djappt_rendered_once', None)
    if seen is None:
        seen = request._djappt_rendered_once = set()
    if key in seen:
        return False
    seen.add(key)
    return True
