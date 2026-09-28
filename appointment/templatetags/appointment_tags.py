# appointment_tags.py
# Path: appointment/templatetags/appointment_tags.py

"""
Template tags the package's own templates use: {% load appointment_tags %}.

Author: Adams Pierre David
Since: 3.13.0
"""

from django import template

register = template.Library()


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
