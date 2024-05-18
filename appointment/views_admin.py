# views_admin.py
# Path: appointment/views_admin.py
# Url root: /app-admins/

"""
Author: Adams Pierre David
Since: 2.0.0
"""

import datetime
import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from appointment.decorators import (
    require_ajax, require_staff_or_superuser, require_superuser, require_user_authenticated)
from appointment.forms import PersonalInformationForm, ServiceForm, StaffAppointmentInformationForm, StaffMemberForm
from appointment.messages_ import appt_updated_successfully
from appointment.models import Appointment, DayOff, StaffMember, WorkingHours
from appointment.services import (
    create_new_appointment, create_staff_member_service, email_change_verification_service,
    fetch_user_appointments, handle_entity_management_request, handle_service_management_request,
    prepare_appointment_display_data, prepare_user_profile_data, save_appt_date_time, update_existing_appointment,
    update_personal_info_service)
from appointment.utils.db_helpers import (
    Service, get_day_off_by_id, get_staff_member_by_user_id, get_user_model,
    get_working_hours_by_id)
from appointment.utils.error_codes import ErrorCode
from appointment.utils.json_context import (
    convert_appointment_to_json, get_generic_context, get_generic_context_with_extra, handle_unauthorized_response,
    json_response)
from appointment.utils.permissions import check_extensive_permissions, check_permissions, \
    has_permission_to_delete_appointment


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
    # if appointment is empty and user doesn't have a staff-member instance, put a message
    # TODO: Refactor this logic, it's not clean
    if not appointments and not StaffMember.objects.filter(
            user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, _("User doesn't have a staff member instance. Please contact the administrator."))
    return render(request, 'administration/staff_index.html', context)


@require_user_authenticated
@require_staff_or_superuser
def display_appointment(request, appointment_id):
    appointment, page_title, error_message, status_code = prepare_appointment_display_data(request.user, appointment_id)

    if error_message:
        context = get_generic_context(request=request)
        return render(request, 'error_pages/404_not_found.html', context=context, status=status_code)
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
            return render(request, 'error_pages/404_not_found.html', context=context, status=404)
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


# TODO: Refactor this function, handle the different cases better.
@require_user_authenticated
@require_staff_or_superuser
def fetch_service_list_for_staff(request):
    appointment_id = request.GET.get('appointmentId')
    staff_id = request.GET.get('staff_member')
    if appointment_id:
        # Fetch services for a specific appointment (edit mode)
        if request.user.is_superuser:
            appointment = Appointment.objects.get(id=appointment_id)
            staff_member = appointment.get_staff_member()
        else:
            staff_member = StaffMember.objects.get(user=request.user)
            # Ensure the staff member is associated with this appointment
            if not Appointment.objects.filter(id=appointment_id,
                                              appointment_request__staff_member=staff_member).exists():
                return json_response(_("You do not have permission to access this appointment."), status_code=403)
        services = list(staff_member.get_services_offered().values('id', 'name'))
    elif staff_id:
        # Fetch services for the specified staff member (new mode based on staff member selection)
        staff_member = get_object_or_404(StaffMember, id=staff_id)
        services = list(staff_member.get_services_offered().values('id', 'name'))
    else:
        # Fetch all services for the staff member (create mode)
        try:
            staff_member = StaffMember.objects.get(user=request.user)
            services = list(staff_member.get_services_offered().values('id', 'name'))
        except StaffMember.DoesNotExist:
            if not request.user.is_superuser:
                return json_response(_("You're not a staff member. Can't perform this action !"), status=400,
                                     success=False)
            else:
                services = list(Service.objects.all().values('id', 'name'))

    if len(services) == 0:
        return json_response(_("No services offered by this staff member."), status=404, success=False,
                             error_code=ErrorCode.SERVICE_NOT_FOUND)
    return json_response(_("Successfully fetched services."), custom_data={'services_offered': services})


@require_user_authenticated
@require_superuser
def fetch_staff_list(request):
    staff_members = StaffMember.objects.all()
    staff_data = []
    for staff in staff_members:
        staff_data.append({
            'id': staff.id,
            'name': staff.get_staff_member_name(),
        })
    return json_response("Successfully fetched staff members.", custom_data={'staff_members': staff_data}, safe=False)


@require_user_authenticated
@require_staff_or_superuser
@require_ajax
@require_POST
def update_appt_min_info(request):
    data = json.loads(request.body)
    is_creating = data.get('isCreating', False)

    if is_creating:
        # Logic for creating a new appointment
        return create_new_appointment(data, request)
    else:
        # Logic for updating an existing appointment
        return update_existing_appointment(data, request)


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
    return json_response(_("Appointment date and time are valid."))


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
        appt = save_appt_date_time(start_time, appt_date, appointment_id, request)
    except Appointment.DoesNotExist:
        return json_response(_("Appointment does not exist."), status=404, success=False,
                             error_code=ErrorCode.APPOINTMENT_NOT_FOUND)
    except ValidationError as e:
        return json_response(e.message, status=400, success=False)
    return json_response(appt_updated_successfully, custom_data={'appt': appt.id})


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

    context = get_generic_context_with_extra(request=request, extra={'form': form, 'btn_text': _("Update")})
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
def add_staff_member_info(request):
    if request.method == 'POST':
        form = StaffMemberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('appointment:user_profile')
    else:
        form = StaffMemberForm()

    context = get_generic_context_with_extra(request=request, extra={'form': form})
    return render(request, 'administration/manage_staff_member.html', context)


@require_user_authenticated
@require_superuser
def create_new_staff_member(request):
    if request.method == 'POST':
        user, is_valid, error_message = create_staff_member_service(request.POST, request)
        if is_valid:
            return redirect('appointment:user_profile', staff_user_id=user.pk)
        else:
            messages.error(request, error_message)
            return redirect('appointment:add_staff_member_personal_info')

    form = PersonalInformationForm()
    context = get_generic_context_with_extra(request=request, extra={'form': form, 'btn_text': _("Create")})
    return render(request, 'administration/manage_staff_personal_info.html', context=context)


@require_user_authenticated
@require_superuser
def make_superuser_staff_member(request):
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
def add_or_update_service(request, service_id=None, view=0):
    if request.method == 'POST':
        service, is_valid, error_message = handle_service_management_request(request.POST, request.FILES, service_id)
        if is_valid:
            messages.success(request, "Service saved successfully!")
            return redirect('appointment:add_service')
        else:
            messages.error(request, error_message)

    extra_context = {
        "btn_text": _("Save"),
        "page_title": _("Add Service"),
    }
    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        form = ServiceForm(instance=service)
        if view != 1:
            extra_context['btn_text'] = _("Update")
            extra_context['page_title'] = _("Update Service")
        else:
            for field in form.fields.values():
                field.disabled = True
            extra_context['btn_text'] = None
            extra_context['page_title'] = _("View Service")
            extra_context['service'] = service
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
@require_user_authenticated
@require_superuser
def remove_staff_member(request, staff_user_id):
    staff_member = get_object_or_404(StaffMember, user_id=staff_user_id)
    staff_member.delete()
    user = get_user_model().objects.get(pk=staff_user_id)
    if not user.is_superuser and user.is_staff:
        user.is_staff = False
        user.save()
    messages.success(request, _("Staff member deleted successfully!"))
    return redirect('appointment:user_profile')


@require_user_authenticated
@require_staff_or_superuser
def get_service_list(request, response_type='html'):
    services = Service.objects.all()
    if response_type == 'json':
        service_data = []
        for service in services:
            service_data.append({
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'duration': service.get_duration(),
                'price': service.get_price_text(),
                'down_payment': service.get_down_payment_text(),
                'image': service.get_image_url(),
                'background_color': service.background_color
            })
        return json_response("Successfully fetched services.", custom_data={'services': service_data}, safe=False)
    context = get_generic_context_with_extra(request=request, extra={'services': services})
    return render(request, 'administration/service_list.html', context=context)


@require_user_authenticated
@require_staff_or_superuser
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if not has_permission_to_delete_appointment(request.user, appointment):
        message = _("You can only delete your own appointments.")
        return handle_unauthorized_response(request, message, 'html')
    appointment.delete()
    messages.success(request, _("Appointment deleted successfully!"))
    return redirect('appointment:get_user_appointments')


@require_user_authenticated
@require_staff_or_superuser
def delete_appointment_ajax(request):
    data = json.loads(request.body)
    appointment_id = data.get("appointment_id")
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if not has_permission_to_delete_appointment(request.user, appointment):
        message = _("You can only delete your own appointments.")
        return json_response(message, status=403, success=False, error_code=ErrorCode.NOT_AUTHORIZED)
    appointment.delete()
    return json_response(_("Appointment deleted successfully."))


@require_user_authenticated
@require_staff_or_superuser
def is_user_staff_admin(request):
    user = request.user
    try:
        StaffMember.objects.get(user=user)
        return json_response(_("User is a staff member."), custom_data={'is_staff_admin': True})
    except StaffMember.DoesNotExist:
        # if superuser, all rights are granted even if not a staff member
        if not user.is_superuser:
            return json_response(_("User is not a staff member."), custom_data={'is_staff_admin': False})
        return json_response(_("User is a superuser."), custom_data={'is_staff_admin': True})
