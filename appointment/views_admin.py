# views_admin.py
# Path: appointment/views_admin.py
# Url root: /app-admins/

"""
Author: Adams Pierre David
Version: 2.0.0
Since: 2.0.0
"""

import datetime
import json

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from appointment.decorators import require_user_authenticated, require_staff_or_superuser, require_ajax, \
    require_superuser
from appointment.forms import StaffAppointmentInformationForm, PersonalInformationForm, ServiceForm
from appointment.models import Appointment, StaffMember, WorkingHours, DayOff
from appointment.services import fetch_user_appointments, prepare_appointment_display_data, prepare_user_profile_data, \
    handle_entity_management_request, save_appointment, save_appt_date_time, update_personal_info_service, \
    email_change_verification_service, create_staff_member_service, handle_service_management_request
from appointment.utils.db_helpers import get_user_model, get_staff_member_by_user_id, get_day_off_by_id, \
    get_working_hours_by_id, Service
from appointment.utils.error_codes import ErrorCode
from appointment.utils.json_context import convert_appointment_to_json, json_response, \
    get_generic_context_with_extra, get_generic_context, handle_unauthorized_response
from appointment.utils.permissions import check_permissions, check_extensive_permissions


###############################################################


@require_user_authenticated
@require_staff_or_superuser
def get_user_appointments(request, response_type='html'):
    appointments = fetch_user_appointments(request.user)
    appointments_json = convert_appointment_to_json(request, appointments)

    if response_type == 'json':
        return json_response("Successfully fetched appointments.", custom_data={'appointments': appointments_json},
                             safe=False)

    # Render the HTML template
    extra_context = {
        'appointments': json.dumps(appointments_json),
    }
    context = get_generic_context_with_extra(request=request, extra=extra_context)
    return render(request, 'administration/staff_index.html', context)


@require_user_authenticated
@require_staff_or_superuser
@require_user_authenticated
@require_staff_or_superuser
def display_appointment(request, appointment_id):
    appointment, page_title, error_message, status_code = prepare_appointment_display_data(request.user, appointment_id)

    if error_message:
        context = get_generic_context(request=request)
        return render(request, 'error_pages/404_not_found.html', context=context)
    # If everything is okay, render the HTML template.
    extra_context = {
        'appointment': appointment,
        'page_title': page_title,
    }
    context = get_generic_context_with_extra(request=request, extra=extra_context)
    return render(request, 'administration/display_appointment.html', context)


@require_user_authenticated
@require_staff_or_superuser
def user_profile(request, staff_user_id=None):
    data = prepare_user_profile_data(request.user, staff_user_id)
    error = data.get('error')
    status_code = data.get('status_code', 400)
    context = get_generic_context_with_extra(request=request, extra=data['extra_context'])
    error_template = 'error_pages/403_forbidden.html' if status_code == 403 else 'error_pages/404_not_found.html'
    template = data['template'] if not error else error_template
    return render(request, template, context)


###############################################################


@require_user_authenticated
@require_staff_or_superuser
def add_day_off(request, staff_user_id=None, response_type='html'):
    staff_user_id = staff_user_id or request.user.pk
    if not check_permissions(staff_user_id, request.user):
        message = _("You can only add your own days off")
        return handle_unauthorized_response(request, message, response_type)

    staff_user_id = staff_user_id if staff_user_id else request.user.pk
    staff_member = get_staff_member_by_user_id(user_id=staff_user_id)
    return handle_entity_management_request(request, staff_member, entity_type='day_off')


@require_user_authenticated
@require_staff_or_superuser
def update_day_off(request, day_off_id, staff_user_id=None, response_type='html'):
    day_off = get_day_off_by_id(day_off_id)
    if not day_off:
        if response_type == 'json':
            return json_response("Day off does not exist.", status=404, success=False,
                                 error_code=ErrorCode.DAY_OFF_NOT_FOUND)
        else:
            context = get_generic_context(request=request)
            return render(request, 'error_pages/404_not_found.html', context=context)
    staff_user_id = staff_user_id or request.user.pk
    if not check_extensive_permissions(staff_user_id, request.user, day_off):
        message = _("You can only update your own days off.")
        return handle_unauthorized_response(request, message, response_type)
    staff_member = get_staff_member_by_user_id(user_id=staff_user_id)
    return handle_entity_management_request(request, staff_member, entity_type='day_off', instance=day_off)


@require_user_authenticated
@require_staff_or_superuser
def delete_day_off(request, day_off_id, staff_user_id=None):
    day_off = get_object_or_404(DayOff, pk=day_off_id)
    if not check_extensive_permissions(staff_user_id, request.user, day_off):
        message = _("You can only delete your own days off.")
        return handle_unauthorized_response(request, message, 'html')
    day_off.delete()
    if staff_user_id:
        return redirect('appointment:user_profile', staff_user_id=staff_user_id)
    return redirect('appointment:user_profile')


###############################################################


@require_user_authenticated
@require_staff_or_superuser
def add_working_hours(request, staff_user_id=None, response_type='html'):
    staff_user_id = staff_user_id or request.user.pk
    if not check_permissions(staff_user_id, request.user):
        message = _("You can only add your own working hours.")
        return handle_unauthorized_response(request, message, response_type)
    staff_user_id = staff_user_id if staff_user_id else request.user.pk
    staff_member = get_staff_member_by_user_id(user_id=staff_user_id)
    return handle_entity_management_request(request=request, staff_member=staff_member, staff_user_id=staff_user_id,
                                            entity_type='working_hours')


@require_user_authenticated
@require_staff_or_superuser
def update_working_hours(request, working_hours_id, staff_user_id=None, response_type='html'):
    working_hours = get_working_hours_by_id(working_hours_id)
    if not working_hours:
        if response_type == 'json':
            return json_response("Working hours does not exist.", status=404, success=False,
                                 error_code=ErrorCode.WORKING_HOURS_NOT_FOUND)
        else:
            context = get_generic_context(request=request)
            return render(request, 'error_pages/404_not_found.html', context=context)

    staff_user_id = staff_user_id or request.user.pk
    if not check_extensive_permissions(staff_user_id, request.user, working_hours):
        message = _("You can only update your own working hours.")
        return handle_unauthorized_response(request, message, response_type)
    staff_member = get_object_or_404(StaffMember, user_id=staff_user_id or request.user.id)
    return handle_entity_management_request(request=request, staff_member=staff_member, add=False,
                                            instance_id=working_hours_id, staff_user_id=staff_user_id,
                                            entity_type='working_hours', instance=working_hours)


@require_user_authenticated
@require_staff_or_superuser
def delete_working_hours(request, working_hours_id, staff_user_id=None):
    working_hours = get_object_or_404(WorkingHours, pk=working_hours_id)
    staff_member = working_hours.staff_member
    if not check_extensive_permissions(staff_user_id, request.user, working_hours):
        message = _("You can only delete your own working hours.")
        return handle_unauthorized_response(request, message, 'html')
    # update weekend hours if necessary
    staff_member.update_upon_working_hours_deletion(working_hours.day_of_week)

    working_hours.delete()

    if staff_user_id:
        return redirect('appointment:user_profile', staff_user_id=staff_user_id)
    return redirect('appointment:user_profile')


###############################################################


@require_user_authenticated
@require_staff_or_superuser
def add_or_update_staff_info(request, user_id=None):
    user = request.user

    # Only allow superusers or the authenticated user to edit his staff info
    if not check_permissions(staff_user_id=user_id, user=user):
        return json_response(_("Not authorized."), status=403, success=False, error_code=ErrorCode.NOT_AUTHORIZED)

    target_user = get_user_model().objects.get(pk=user_id) if user_id else user

    staff_member, created = StaffMember.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        form = StaffAppointmentInformationForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            if user_id:
                return redirect('appointment:user_profile', staff_user_id=user_id)
            return redirect('appointment:user_profile')
    else:
        form = StaffAppointmentInformationForm(instance=staff_member)

    context = get_generic_context_with_extra(request=request, extra={'form': form})
    return render(request, 'administration/manage_staff_member.html', context)


@require_user_authenticated
@require_staff_or_superuser
def fetch_service_list_for_staff(request):
    appointmentId = request.GET.get('appointmentId')
    if request.user.is_superuser:
        appointment = Appointment.objects.get(id=appointmentId)
        staff_member = appointment.get_staff_member()
    else:
        staff_member = StaffMember.objects.get(user=request.user)
    # This will give a list of dictionaries with 'id' and 'name' as keys
    services = list(staff_member.get_services_offered().values('id', 'name'))
    return json_response("Successfully fetched services.", custom_data={'services_offered': services})


@require_user_authenticated
@require_staff_or_superuser
@require_ajax
@require_POST
def update_appt_min_info(request):
    data = json.loads(request.body)

    # Extracting the data
    start_time = data.get("start_time")
    client_name = data.get("client_name")
    client_email = data.get("client_email")
    phone_number = data.get("phone_number")
    client_address = data.get("client_address")
    appointment_id = data.get("appointment_id")
    service_id = data.get("service_id")

    # save the data
    try:
        appt = Appointment.objects.get(id=appointment_id)
        appt = save_appointment(appt, client_name, client_email, start_time, phone_number,
                                client_address, service_id)

    except Appointment.DoesNotExist:
        return json_response("Appointment does not exist.", status=404, success=False,
                             error_code=ErrorCode.APPOINTMENT_NOT_FOUND)
    appointments_json = convert_appointment_to_json(request, [appt])[0]

    # Responding after processing the data
    return json_response("Appointment updated successfully.", custom_data={'appt': appointments_json})


@require_user_authenticated
@require_staff_or_superuser
@require_ajax
@require_POST
def validate_appointment_date(request):
    data = json.loads(request.body)
    start_time_str = data.get("start_time")
    appt_date_str = data.get("date")
    appointment_id = data.get("appointment_id")

    # Convert the string date and time to Python datetime objects
    start_time_obj = datetime.datetime.fromisoformat(start_time_str)
    appt_date = datetime.datetime.strptime(appt_date_str, "%Y-%m-%d").date()

    # Get the staff member for the appointment
    appt = Appointment.objects.get(id=appointment_id)
    staff_member = appt.appointment_request.staff_member

    # Check if the appointment's date and time are valid
    weekday: str = appt_date.strftime("%A")
    is_valid, message = Appointment.is_valid_date(appt_date, start_time_obj, staff_member, appointment_id, weekday)
    if not is_valid:
        return json_response(message, status=403, success=False, error_code=ErrorCode.INVALID_DATE)
    return json_response("Appointment date and time are valid.")


@require_user_authenticated
@require_staff_or_superuser
@require_ajax
@require_POST
def update_appt_date_time(request):
    data = json.loads(request.body)

    # Extracting the data
    start_time = data.get("start_time")
    appt_date = data.get("date")
    appointment_id = data.get("appointment_id")

    # save the data
    try:
        appt = save_appt_date_time(start_time, appt_date, appointment_id)
    except Appointment.DoesNotExist:
        return json_response("Appointment does not exist.", status=404, success=False,
                             error_code=ErrorCode.APPOINTMENT_NOT_FOUND)
    return json_response("Appointment updated successfully.", custom_data={'appt': appt.id})


@require_user_authenticated
@require_staff_or_superuser
def update_personal_info(request, staff_user_id=None):
    # only superuser or the staff member itself can update the personal info
    if not check_permissions(staff_user_id=staff_user_id, user=request.user) or (
            not staff_user_id and not request.user.is_superuser):
        return json_response(_("Not authorized."), status=403, success=False, error_code=ErrorCode.NOT_AUTHORIZED)

    if request.method == 'POST':
        user, is_valid, error_message = update_personal_info_service(staff_user_id, request.POST, request.user)
        if is_valid:
            return redirect('appointment:user_profile')
        else:
            messages.error(request, error_message)
            return redirect('appointment:update_personal_info')

    if staff_user_id:
        user = get_user_model().objects.get(pk=staff_user_id)
    else:
        user = request.user

    form = PersonalInformationForm(initial={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }, user=user)

    context = get_generic_context_with_extra(request=request, extra={'form': form})
    return render(request, 'administration/manage_staff_personal_info.html', context)


@require_user_authenticated
@require_staff_or_superuser
def email_change_verification_code(request):
    context = get_generic_context(request=request)

    if request.method == 'POST':
        code = request.POST.get('code')
        email = request.session.get('email')
        old_email = request.session.get('old_email')

        is_verified = email_change_verification_service(code, email, old_email)
        if is_verified:
            messages.success(request, _("Email updated successfully!"))
            return redirect('appointment:user_profile')
        else:
            messages.error(request, _("The verification code provided is incorrect. Please try again."))
            return render(request, 'administration/email_change_verification_code.html', context=context)

    return render(request, 'administration/email_change_verification_code.html', context=context)


###############################################################


@require_user_authenticated
@require_superuser
def create_new_staff_member(request):
    if request.method == 'POST':
        user, is_valid, error_message = create_staff_member_service(request.POST)
        if is_valid:
            return redirect('appointment:user_profile', staff_user_id=user.pk)
        else:
            messages.error(request, error_message)
            return redirect('appointment:create_new_staff_member')

    form = PersonalInformationForm()
    context = get_generic_context_with_extra(request=request, extra={'form': form})
    return render(request, 'administration/manage_staff_personal_info.html', context=context)


@require_user_authenticated
@require_superuser
def make_superuser_staff_member(request, ):
    user = request.user
    StaffMember.objects.create(user=user)
    return redirect('appointment:user_profile')


@require_user_authenticated
@require_superuser
def remove_superuser_staff_member(request):
    user = request.user
    StaffMember.objects.filter(user=user).delete()
    return redirect('appointment:user_profile')


###############################################################
# Services

@require_user_authenticated
@require_superuser
def add_or_update_service(request, service_id=None):
    if request.method == 'POST':
        service, is_valid, error_message = handle_service_management_request(request.POST, service_id)
        if is_valid:
            messages.success(request, "Service saved successfully!")
            return redirect('appointment:user_profile')  # Modify this to the appropriate redirect
        else:
            messages.error(request, error_message)

    extra_context = {
        "btn_text": _("Save"),
        "page_title": _("Add Service"),
    }
    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        form = ServiceForm(instance=service)
        extra_context['btn_text'] = _("Update")
        extra_context['page_title'] = _("Update Service")
    else:
        form = ServiceForm()
    extra_context['form'] = form
    context = get_generic_context_with_extra(request=request, extra=extra_context)
    return render(request, 'administration/manage_service.html', context=context)


@require_user_authenticated
@require_superuser
def delete_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    service.delete()
    messages.success(request, _("Service deleted successfully!"))
    return redirect('appointment:user_profile')


###############################################################
# Remove staff member
def remove_staff_member(request, staff_user_id):
    staff_member = get_object_or_404(StaffMember, user_id=staff_user_id)
    staff_member.delete()
    messages.success(request, _("Staff member deleted successfully!"))
    return redirect('appointment:user_profile')
