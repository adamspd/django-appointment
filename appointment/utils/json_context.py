# json_context.py
# Path: appointment/utils/json_context.py

"""
Author: Adams Pierre David
Since: 2.0.0
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from appointment.settings import APPOINTMENT_ADMIN_BASE_TEMPLATE, APPOINTMENT_BASE_TEMPLATE
from appointment.utils.db_helpers import username_in_user_model
from appointment.utils.error_codes import ErrorCode


def convert_appointment_to_json(request, appointments: list) -> list:
    """Convert a queryset of Appointment objects to a JSON serializable format."""
    su = request.user.is_superuser
    return [{
        "id": appt.id,
        "client": appt.client.username if username_in_user_model() else "",
        "start_time": appt.get_start_time().isoformat(),
        "end_time": appt.get_end_time().isoformat(),
        "client_name": appt.get_client_name(),
        "url": appt.get_absolute_url(request),
        "background_color": appt.get_background_color(),
        "service_name": appt.get_service_name() if not su else f"{appt.get_service_name()} ({appt.get_staff_member_name()})",
        "client_email": appt.client.email,
        "client_phone": str(appt.phone),
        "client_address": appt.address,
        "service_id": appt.get_service().id,
        "staff_id": appt.appointment_request.staff_member.id,
        "additional_info": appt.additional_info,
        "want_reminder": appt.want_reminder,
    } for appt in appointments]


def json_response(message, status=200, success=True, custom_data=None, error_code=None, **kwargs):
    """Return a generic JSON response."""
    response_data = {
        "message": message,
        "success": success
    }
    if error_code:
        response_data["errorCode"] = error_code.value
    if custom_data:
        response_data.update(custom_data)
    return JsonResponse(response_data, status=status, **kwargs)


def get_generic_context(request, admin=True):
    """Get the generic context for the admin pages."""
    return {
        'BASE_TEMPLATE': APPOINTMENT_ADMIN_BASE_TEMPLATE if admin else APPOINTMENT_BASE_TEMPLATE,
        'user': request.user,
        'is_superuser': request.user.is_superuser,
    }


def get_generic_context_with_extra(request, extra, admin=True):
    """Get the generic context for the admin pages with extra context."""
    context = get_generic_context(request, admin=admin)
    context.update(extra)
    return context


def handle_unauthorized_response(request, message, response_type):
    """Handle unauthorized response based on the response type."""
    if response_type == 'json':
        return json_response(message=message, status=403, success=False, error_code=ErrorCode.NOT_AUTHORIZED)

    # If not 'json', handle as HTML response by default.
    context = {
        'message': message,
        'back_url': reverse('appointment:user_profile'),
        'BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
    }
    # set return code to 403
    return render(request, 'error_pages/403_forbidden.html', context=context, status=403)
