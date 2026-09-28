# appointment_tags.py
# Path: appointment/templatetags/appointment_tags.py

"""
Small read-only helpers for templates that override the package's pages: {% load appointment_tags %}.

Author: Adams Pierre David
Since: 3.13.0
"""

from django import template
from django.utils import timezone

from appointment.models import Appointment, StaffMember
from appointment.utils.view_helpers import format_price

register = template.Library()


@register.simple_tag
def upcoming_appointments(service=None, staff_member=None, limit=5):
    """Upcoming appointments (soonest first), with the upcoming and all-time counts.

    Filter by ``service`` and/or ``staff_member`` (a StaffMember, or its user). Use it as
    ``{% upcoming_appointments service=service limit=6 as bookings %}``, then ``bookings.upcoming``,
    ``bookings.upcoming_count`` and ``bookings.total_count``.
    """
    appointments = Appointment.objects.select_related(
        'client', 'appointment_request', 'appointment_request__service', 'appointment_request__staff_member__user')
    if service is not None:
        appointments = appointments.filter(appointment_request__service=service)
    if staff_member is not None:
        if isinstance(staff_member, StaffMember):
            appointments = appointments.filter(appointment_request__staff_member=staff_member)
        else:
            appointments = appointments.filter(appointment_request__staff_member__user=staff_member)
    upcoming = appointments.filter(appointment_request__date__gte=timezone.localdate()).order_by(
        'appointment_request__date', 'appointment_request__start_time')
    return {
        'upcoming': list(upcoming[:limit]),
        'upcoming_count': upcoming.count(),
        'total_count': appointments.count(),
    }


@register.filter
def initials(user):
    """Up to two letters for an avatar: the first and last name's, or the first letter of the username/email."""
    if user is None:
        return ''
    first = (getattr(user, 'first_name', '') or '')[:1]
    last = (getattr(user, 'last_name', '') or '')[:1]
    if first:
        return f'{first}{last}'.upper()
    name = getattr(user, 'get_username', lambda: '')() or getattr(user, 'email', '') or ''
    return name[:1].upper()


@register.filter
def money(amount, currency='USD'):
    """``{{ service.price|money:service.currency }}``: the amount in the active language, like the package's prices."""
    if amount in (None, ''):
        return ''
    return format_price(amount, currency)
