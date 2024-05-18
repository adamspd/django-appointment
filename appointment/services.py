# services.py
# Path: appointment/services.py

"""
Author: Adams Pierre David
Since: 2.0.0
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy as _

from appointment.forms import PersonalInformationForm, ServiceForm, StaffDaysOffForm, StaffWorkingHoursForm
from appointment.messages_ import appt_updated_successfully
from appointment.settings import APPOINTMENT_PAYMENT_URL
from appointment.utils.date_time import (
    convert_12_hour_time_to_24_hour_time, convert_str_to_date, convert_str_to_time, get_ar_end_time)
from appointment.utils.db_helpers import (
    Appointment, AppointmentRequest, EmailVerificationCode, Service, StaffMember, WorkingHours, calculate_slots,
    calculate_staff_slots, check_day_off_for_staff, create_and_save_appointment, create_new_user,
    day_off_exists_for_date_range, exclude_booked_slots, exclude_pending_reschedules, get_all_appointments,
    get_all_staff_members,
    get_appointment_by_id, get_appointments_for_date_and_time, get_staff_member_appointment_list,
    get_staff_member_from_user_id_or_logged_in, get_times_from_config, get_user_by_email,
    get_weekday_num_from_date, get_working_hours_for_staff_and_day, parse_name, update_appointment_reminder,
    working_hours_exist)
from appointment.utils.email_ops import send_reset_link_to_staff_member
from appointment.utils.error_codes import ErrorCode
from appointment.utils.json_context import convert_appointment_to_json, get_generic_context, json_response
from appointment.utils.permissions import check_entity_ownership
from appointment.utils.session import handle_email_change


def fetch_user_appointments(user):
    """Fetch the appointments for a given user.

    :param user: The user instance.
    :return: A list of appointments.
    """
    if user.is_superuser:
        return get_all_appointments()
    try:
        staff_member_instance = user.staffmember
        return get_staff_member_appointment_list(staff_member_instance)
    except ObjectDoesNotExist:
        if user.is_staff:
            return []

    raise ValueError("User is not a staff member or a superuser")


def prepare_appointment_display_data(user, appointment_id):
    """Prepare the data for the appointment details page.

    :param user: The user instance.
    :param appointment_id: The appointment id.
    :return: A tuple containing the appointment instance, page title, error message, and status code.
    """
    appointment = get_appointment_by_id(appointment_id)

    # If the appointment doesn't exist
    if not appointment:
        return None, None, _("Appointment does not exist."), 404

    # Check if the user is authorized to view the appointment
    if not check_entity_ownership(user, appointment):
        return None, None, _("You are not authorized to view this appointment."), 403

    # Prepare the data for display
    page_title = _("Appointment details") + _(": {client_name}").format(client_name=appointment.get_client_name())
    if user.is_superuser:
        page_title += f' (by: {appointment.get_staff_member_name()})'

    return appointment, page_title, None, 200


def prepare_user_profile_data(user, staff_user_id):
    """Prepare the data for the user profile page.

    :param user: The user instance.
    :param staff_user_id: The staff user id.
    :return: A dictionary containing the data for the user profile page.
    """
    if user.is_superuser and staff_user_id is None:
        staff_members = get_all_staff_members()
        btn_staff_me = "Staff me"
        btn_staff_me_link = reverse('appointment:make_superuser_staff_member')
        if StaffMember.objects.filter(user=user).exists():
            btn_staff_me = "Remove me"
            btn_staff_me_link = reverse('appointment:remove_superuser_staff_member')
        data = {
            'error': False,
            'template': 'administration/staff_list.html',
            'extra_context': {
                'staff_members': staff_members,
                'btn_staff_me': btn_staff_me,
                'btn_staff_me_link': btn_staff_me_link
            }
        }
        return data

    if staff_user_id and staff_user_id != user.pk and not user.is_superuser:
        return {
            'error': True,
            'extra_context': {'message': _("You can only view your own profile"),
                              'back_url': reverse('appointment:user_profile')},
            'status_code': 403
        }
    staff_member = get_staff_member_from_user_id_or_logged_in(user, staff_user_id)

    if not staff_member:
        return {
            'error': True,
            'extra_context': {'message': _("Not authorized."), 'back_url': reverse('appointment:user_profile')},
            'status_code': 403
        }

    bt_help = StaffMember._meta.get_field('appointment_buffer_time')
    bt_help_text = bt_help.help_text

    sd_help = StaffMember._meta.get_field('slot_duration')
    sd_help_text = sd_help.help_text
    if user.is_superuser:
        service_msg = _("Here you can add/remove services offered by this staff member by modifying this section.")
    else:
        service_msg = _("Here you can add/remove services offered by you by modifying this section.")
    return {
        'error': False,
        'template': 'administration/user_profile.html',
        'extra_context': {
            'superuser': user if user.is_superuser else None,
            'user': staff_member.user if staff_member else user,
            'staff_member': staff_member,
            'days_off': staff_member.get_days_off().order_by('start_date') if staff_member else [],
            'working_hours': staff_member.get_working_hours() if staff_member else [],
            'services_offered': staff_member.get_services_offered() if staff_member else [],
            'staff_member_not_found': not bool(staff_member),
            'buffer_time_help_text': bt_help_text,
            'slot_duration_help_text': sd_help_text,
            'service_msg': service_msg,
        }
    }


###############################################################
# handler for adding, updating, and deleting day off and working hours

def handle_entity_management_request(request, staff_member, entity_type, instance=None, staff_user_id=None,
                                     instance_id=None, add=True):
    """Handle the request to add, update, or delete a day off or working hours.

    :param request: The request object.
    :param staff_member: The staff member instance.
    :param entity_type: The type of entity to add or update, either 'day_off' or 'working_hours'.
    :param instance: The instance of the entity to update.
    :param staff_user_id: The staff user id.
    :param instance_id: The id of the instance to update.
    :param add: If True, add a new entity, otherwise, update an existing one.
    :return: A JsonResponse instance.
    """
    if not staff_member:
        return json_response("Not authorized", status=403, success=False,
                             error_code=ErrorCode.NOT_AUTHORIZED)

    button_text = _('Update') if instance else _('Add')
    if entity_type == 'day_off':
        form = StaffDaysOffForm(instance=instance)
        context = get_working_hours_and_days_off_context(request, button_text, 'day_off_form', form)
        template = 'administration/manage_day_off.html'
    else:
        form = StaffWorkingHoursForm(instance=instance)
        context = get_working_hours_and_days_off_context(request, button_text, 'working_hours_form', form,
                                                         staff_user_id, instance,
                                                         instance_id)
        template = 'administration/manage_working_hours.html'

    if request.method == 'POST' and entity_type == 'day_off':
        day_off_form = StaffDaysOffForm(request.POST, instance=instance)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if day_off_exists_for_date_range(staff_member, start_date, end_date, getattr(instance, 'id', None)):
            return json_response(_("Days off for this date range already exist."), status=400, success=False,
                                 error_code=ErrorCode.DAY_OFF_CONFLICT)

        return handle_day_off_form(day_off_form, staff_member)
    elif request.method == 'POST' and entity_type == 'working_hours':
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        return handle_working_hours_form(staff_member, day_of_week, start_time, end_time, add, instance_id)

    return render(request, template, context, status=200)


def handle_day_off_form(day_off_form, staff_member):
    """Handle the day off form.

    :param day_off_form: The day off form instance.
    :param staff_member: The staff member instance.
    :return: A JsonResponse instance.
    """
    if day_off_form.is_valid():
        day_off = day_off_form.save(commit=False)
        day_off.staff_member = staff_member
        day_off.save()
        redirect_url = reverse('appointment:user_profile',
                               kwargs={'staff_user_id': staff_member.user_id}) if staff_member else reverse(
            'appointment:user_profile')
        return json_response(_("Day off saved successfully."), custom_data={'redirect_url': redirect_url})
    else:
        message = "Invalid data:"
        message += get_error_message_in_form(form=day_off_form)
        return json_response(message, status=400, success=False, error_code=ErrorCode.INVALID_DATA)


def handle_working_hours_form(staff_member, day_of_week, start_time, end_time, add, wh_id=None):
    """Handle the working hours form.

    :param staff_member: The staff member instance.
    :param day_of_week: The day of the week.
    :param start_time: The start time.
    :param end_time: The end time.
    :param add: If True, add a new working hours instance. Otherwise, update an existing one.
    :param wh_id: The working hours' id.
    :return: A JsonResponse instance.
    """
    # Validate inputs
    if not (staff_member and day_of_week and start_time and end_time):
        return json_response(_("Invalid data."), status=400, success=False, error_code=ErrorCode.INVALID_DATA)

    # Convert start time and end time to 24-hour format
    start_time = convert_12_hour_time_to_24_hour_time(start_time)
    end_time = convert_12_hour_time_to_24_hour_time(end_time)

    # Ensure start time is before end time
    if start_time >= end_time:
        return json_response(_("Start time must be before end time."), status=400, success=False,
                             error_code=ErrorCode.INVALID_DATA)

    if add:
        # Create new working hours
        if working_hours_exist(day_of_week=day_of_week, staff_member=staff_member):
            return json_response(_("Working hours already exist for this day."), status=400, success=False,
                                 error_code=ErrorCode.WORKING_HOURS_CONFLICT)
        wk = WorkingHours(staff_member=staff_member, day_of_week=day_of_week, start_time=start_time, end_time=end_time)
    else:
        # Ensure working_hours_id is provided
        if not wh_id:
            return json_response(_("Invalid or no working_hours_id provided."), status=400, success=False,
                                 error_code=ErrorCode.INVALID_DATA)

        # Get the working hours instance to update
        try:
            wk = WorkingHours.objects.get(pk=wh_id)
            wk.day_of_week = day_of_week
            wk.start_time = start_time
            wk.end_time = end_time
        except WorkingHours.DoesNotExist:
            return json_response(_("Working hours does not exist."), status=400, success=False,
                                 error_code=ErrorCode.WORKING_HOURS_NOT_FOUND)

        # Save working hours
    wk.save()

    # Return success with redirect URL
    redirect_url = reverse('appointment:user_profile', kwargs={'staff_user_id': staff_member.user.id}) \
        if staff_member.user.id else reverse('appointment:user_profile')
    return json_response(_("Working hours saved successfully."), custom_data={'redirect_url': redirect_url})


def get_working_hours_and_days_off_context(request, btn_txt, form_name, form, user_id=None, instance=None, wh_id=None):
    """Get the context for the working hours and days off forms.

    :param request: The request object.
    :param btn_txt: The text to display on the submit button.
    :param form_name: The name of the form which depends on if it's a working hours or days off form.
    :param form: The form instance itself.
    :param user_id: The staff user id.
    :param instance: The working hour form instance.
    :param wh_id: The working hour id.
    :return: A dictionary containing the context.
    """
    context = get_generic_context(request)
    context.update({
        'button_text': btn_txt,
        form_name: form,
    })
    if user_id:
        context.update({
            'staff_user_id': user_id,
        })
    if instance:
        context.update({
            'working_hours_instance': instance,
        })
    if wh_id:
        context.update({
            'working_hours_id': wh_id,
        })
    return context


def save_appointment(appt, client_name, client_email, start_time, phone_number, client_address, service_id, request,
                     staff_member_id=None, want_reminder=False, additional_info=None):
    """Save an appointment's details.
    :return: The modified appointment.
    """
    service = Service.objects.get(id=service_id)
    if staff_member_id:
        staff_member = StaffMember.objects.get(id=staff_member_id)
        if not staff_member.get_service_is_offered(service_id):
            return None
    # Modify and save client details
    first_name, last_name = parse_name(client_name)
    client = appt.client
    client.first_name = first_name
    client.last_name = last_name
    client.email = client_email
    client.save()
    # convert start time to a time object if it is a string
    if isinstance(start_time, str):
        start_time = convert_str_to_time(start_time)
    # calculate end time from start time and service duration
    end_time = get_ar_end_time(start_time, service.duration)

    # Modify and save appointment request details
    appt_request = appt.appointment_request

    # Update reminder here
    update_appointment_reminder(appointment=appt, new_date=appt_request.date, new_start_time=start_time,
                                want_reminder=want_reminder, request=request)

    appt_request.service = service
    appt_request.start_time = start_time
    appt_request.end_time = end_time
    appt_request.staff_member = staff_member
    appt_request.save()

    # Modify and save appointment details
    appt.phone = phone_number
    appt.address = client_address
    appt.want_reminder = want_reminder
    appt.additional_info = additional_info
    appt.save()
    return appt


def save_appt_date_time(appt_start_time, appt_date, appt_id, request):
    """Save the date and time of an appointment request.

    :param appt_start_time: The start time of the appointment request.
    :param appt_date: The date of the appointment request.
    :param appt_id: The ID of the appointment to modify.
    :param request: The request object.
    :return: The modified appointment.
    """
    appt = Appointment.objects.get(id=appt_id)
    service = appt.get_service()

    # Convert start time to a time object if it is a string
    if isinstance(appt_start_time, str):
        time_format = "%H:%M:%S.%fZ"
        appt_start_time_obj = datetime.datetime.strptime(appt_start_time, time_format).time()
    else:
        appt_start_time_obj = appt_start_time

    # Calculate end time from start time and service duration
    end_time_obj = get_ar_end_time(appt_start_time_obj, service.duration)

    # Convert the appt_date from string to a date object if it's a string
    if isinstance(appt_date, str):
        appt_date_obj = datetime.datetime.strptime(appt_date, "%Y-%m-%d").date()
    else:
        appt_date_obj = appt_date

    # Update reminder here
    update_appointment_reminder(appointment=appt, new_date=appt_date_obj, new_start_time=appt_start_time_obj,
                                request=request)

    # Modify and save appointment request details
    appt_request = appt.appointment_request
    appt_request.date = appt_date_obj
    appt_request.start_time = appt_start_time_obj
    appt_request.end_time = end_time_obj
    appt_request.save()
    appt.save()

    return appt


def get_available_slots(date, appointments):
    """Calculate the available time slots for a given date and a list of appointments.

    :param date: The date for which to calculate the available slot
    :param appointments: A list of Appointment objects
    :return: A list of available time slots as strings in the format '%I:%M %p' like ['10:00 AM', '10:30 AM']
    """

    start_time, end_time, slot_duration, buff_time = get_times_from_config(date)
    now = timezone.now()
    buffer_time = now + buff_time if date == now.date() else now
    slots = calculate_slots(start_time, end_time, buffer_time, slot_duration)
    slots = exclude_booked_slots(appointments, slots, slot_duration)
    return [slot.strftime('%I:%M %p') for slot in slots]


def get_available_slots_for_staff(date, staff_member):
    """Calculate the available time slots for a given date and a staff member.

    :param date: The date for which to calculate the available slots
    :param staff_member: The staff member for which to calculate the available slots
    :return: A list of available time slots as strings in the format '%I:%M %p' like ['10:00 AM', '10:30 AM']
    """
    # Check if the provided date is a day off for the staff member
    days_off_exist = check_day_off_for_staff(staff_member=staff_member, date=date)
    if days_off_exist:
        return []

    # Check if the staff member works on the provided date
    day_of_week = get_weekday_num_from_date()  # Python's weekday starts from Monday (0) to Sunday (6)
    working_hours_dict = get_working_hours_for_staff_and_day(staff_member, day_of_week)
    if not working_hours_dict:
        return []

    slot_duration = datetime.timedelta(minutes=staff_member.get_slot_duration())
    slots = calculate_staff_slots(date, staff_member)
    slots = exclude_pending_reschedules(slots, staff_member, date)
    appointments = get_appointments_for_date_and_time(date, working_hours_dict['start_time'],
                                                      working_hours_dict['end_time'], staff_member)
    return exclude_booked_slots(appointments, slots, slot_duration)


def get_finish_button_text(service) -> str:
    """
    Check if a service is free.

    :param service: Service, the service to check
    :return: bool, True if the service is free, False otherwise
    """
    if service.is_a_paid_service() and APPOINTMENT_PAYMENT_URL:
        return _("Pay Now")
    return _("Finish")


def get_appointments_and_slots(date_, service=None):
    """
    Get appointments and available slots for a given date and service.

    If a service is provided, the function retrieves appointments for that service on the given date.
    Otherwise, it retrieves all appointments for the given date.

    :param date_: datetime.date, the date for which to retrieve appointments and available slots
    :param service: Service, the service for which to retrieve appointments
    :return: tuple, a tuple containing two elements:
        - A queryset of appointments for the given date and service (if provided).
        - A list of available time slots on the given date, excluding booked appointments.
    """
    if service:
        appointments = Appointment.objects.filter(appointment_request__service=service,
                                                  appointment_request__date=date_)
    else:
        appointments = Appointment.objects.filter(appointment_request__date=date_)
    available_slots = get_available_slots(date_, appointments)
    return appointments, available_slots


def get_error_message_in_form(form):
    """
    Get the error message in a form.

    :param form: Form, the form to check
    :return: str, the error message
    """
    error_messages = []
    for field, errors in form.errors.items():
        error_messages.append(f"{field}: {','.join(errors)}")
    if len(error_messages) == 3:
        return _("Empty fields are not allowed.")
    return " ".join(error_messages)


def update_personal_info_service(staff_user_id, post_data, current_user):
    try:
        user = get_user_model().objects.get(pk=staff_user_id) if staff_user_id else current_user
    except get_user_model().DoesNotExist:
        return None, False, _("User not found.")

    form = PersonalInformationForm(post_data, user=user)
    if form.is_valid():
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        if form.cleaned_data['email'] != user.email:
            handle_email_change(current_user, user, form.cleaned_data['email'])
        user.save()
        return user, True, None
    else:
        return None, False, get_error_message_in_form(form=form)


def email_change_verification_service(code, email, old_email):
    user = get_user_by_email(old_email)
    code_obj = EmailVerificationCode.objects.filter(code=code).first()

    if user and code_obj and code_obj.check_code(code):
        user.email = email
        user.save()
        code_obj.delete()
        return True
    return False


def create_staff_member_service(post_data, request):
    form = PersonalInformationForm(post_data)
    if form.is_valid():
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data["email"]

        if get_user_by_email(email):
            return None, False, _("A user with this email already exists.")

        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        }
        user = create_new_user(client_data=user_data)
        StaffMember.objects.create(user=user)
        if not user.is_superuser:
            user.is_staff = True
            user.save()
        send_reset_link_to_staff_member(user, request, user.email)
        return user, True, None
    else:
        return None, False, get_error_message_in_form(form=form)


def handle_service_management_request(post_data, files_data=None, service_id=None):
    try:
        if service_id:
            service = Service.objects.get(pk=service_id)
            form = ServiceForm(post_data, files_data, instance=service)
        else:
            form = ServiceForm(post_data, files_data)

        if form.is_valid():
            form.save()
            return form.instance, True, _("Service saved successfully.")
        else:
            return None, False, get_error_message_in_form(form=form)
    except Exception as e:
        return None, False, str(e)


def create_new_appointment(data, request):
    service = Service.objects.get(id=data.get("service_id"))
    staff_id = data.get("staff_member")
    if staff_id:
        staff_member = StaffMember.objects.get(id=staff_id)
    else:
        staff_member = StaffMember.objects.get(user=request.user)

    # Convert date and start time strings to datetime objects
    date = convert_str_to_date(data.get("date"))
    start_time = convert_str_to_time(data.get("start_time"))
    start_datetime = datetime.datetime.combine(date, start_time)

    appointment_request = AppointmentRequest(
        date=start_datetime.date(),
        start_time=start_datetime.time(),
        end_time=(start_datetime + service.duration).time(),
        service=service,
        staff_member=staff_member,
    )
    appointment_request.full_clean()  # Validates the model
    appointment_request.save()

    # Prepare client data
    email = data.get("client_email", "")
    name_parts = data.get("client_name", "").split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""  # Use an empty string if no last name

    client_data = {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
    }

    # Use your custom user creation logic
    user = get_user_by_email(email)
    if not user:
        create_new_user(client_data)

    # Create and save the new appointment
    appointment_data = {
        'phone': data.get("client_phone", ""),
        'address': data.get("client_address", ""),
        'want_reminder': data.get("want_reminder") == 'true',
        'additional_info': data.get("additional_info", ""),
        'paid': False
    }
    appointment = create_and_save_appointment(appointment_request, client_data, appointment_data, request)
    appointment_list = convert_appointment_to_json(request, [appointment])

    return json_response("Appointment created successfully.", custom_data={'appt': appointment_list})


def update_existing_appointment(data, request):
    try:
        appt = Appointment.objects.get(id=data.get("appointment_id"))
        staff_id = data.get("staff_member")
        want_reminder = data.get("want_reminder") == 'true'
        appt = save_appointment(
            appt,
            client_name=data.get("client_name"),
            client_email=data.get("client_email"),
            start_time=data.get("start_time"),
            phone_number=data.get("client_phone"),
            client_address=data.get("client_address"),
            service_id=data.get("service_id"),
            want_reminder=want_reminder,
            additional_info=data.get("additional_info"),
            staff_member_id=staff_id,
            request=request,
        )
        if not appt:
            return json_response("Service not offered by staff member.", status=400, success=False,
                                 error_code=ErrorCode.SERVICE_NOT_FOUND)
        appointments_json = convert_appointment_to_json(request, [appt])[0]
        return json_response(appt_updated_successfully, custom_data={'appt': appointments_json})
    except Appointment.DoesNotExist:
        return json_response("Appointment does not exist.", status=404, success=False,
                             error_code=ErrorCode.APPOINTMENT_NOT_FOUND)
    except Service.DoesNotExist:
        return json_response("Service does not exist.", status=404, success=False,
                             error_code=ErrorCode.SERVICE_NOT_FOUND)
    except Exception as e:
        return json_response(str(e.args[0]), status=400, success=False)
