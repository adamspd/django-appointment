# views.py
# Path: appointment/views.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from datetime import date, datetime, timedelta

import pytz
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from appointment.email_sender import notify_admin
from appointment.forms import AppointmentForm, AppointmentRequestForm
from appointment.logger_config import logger
from appointment.models import Appointment, AppointmentRequest, Config, DayOff, EmailVerificationCode, Service, \
    StaffMember
from appointment.utils.db_helpers import check_day_off_for_staff, create_and_save_appointment, create_new_user, \
    create_payment_info_and_get_url, get_non_working_days_for_staff, get_user_by_email, get_user_model, \
    get_website_name, get_weekday_num_from_date, is_working_day, username_in_user_model
from appointment.utils.email_ops import send_thank_you_email
from appointment.utils.session import get_appointment_data_from_session, handle_existing_email
from appointment.utils.view_helpers import get_locale, get_timezone_txt
from .decorators import require_ajax
from .services import get_appointments_and_slots, get_available_slots_for_staff
from .settings import (APPOINTMENT_PAYMENT_URL, APPOINTMENT_THANK_YOU_URL, APP_TIME_ZONE)
from .utils.date_time import convert_str_to_date, convert_str_to_time, get_current_year
from .utils.error_codes import ErrorCode
from .utils.json_context import get_generic_context_with_extra, json_response

CLIENT_MODEL = get_user_model()


@require_ajax
def get_available_slots_ajax(request):
    """This view function handles AJAX requests to get available slots for a selected date.

    :param request: The request instance.
    :return: A JSON response containing available slots, selected date, an error flag, and an optional error message.
    """
    selected_date = convert_str_to_date(request.GET.get('selected_date'))
    staff_id = request.GET.get('staff_id')

    if selected_date < date.today():
        custom_data = {'error': True, 'available_slots': [], 'date_chosen': ''}
        message = _('Date is in the past')
        return json_response(message=message, custom_data=custom_data, success=False,
                             error_code=ErrorCode.PAST_DATE)

    date_chosen = selected_date.strftime("%a, %B %d, %Y")
    custom_data = {'date_chosen': date_chosen}

    # If no staff_id provided, return an empty list of slots
    if not staff_id or staff_id == 'none':
        custom_data['available_slots'] = []
        custom_data['error'] = False
        message = _('No staff member selected')
        return json_response(message=message, custom_data=custom_data, success=False,
                             error_code=ErrorCode.STAFF_ID_REQUIRED)

    sm = get_object_or_404(StaffMember, pk=staff_id)
    custom_data['staff_member'] = sm.get_staff_member_name()
    days_off_exist = check_day_off_for_staff(staff_member=sm, date=selected_date)
    if days_off_exist:
        message = _("Day off. Please select another date!")
        custom_data['available_slots'] = []
        return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
    # if selected_date is not a working day for the staff, return an empty list of slots and 'message' is Day Off
    weekday_num = get_weekday_num_from_date(selected_date)
    is_working_day_ = is_working_day(staff_member=sm, day=weekday_num)
    if not is_working_day_:
        message = _("Not a working day for {staff_member}. Please select another date!").format(
            staff_member=sm.get_staff_member_first_name())
        custom_data['available_slots'] = []
        return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
    available_slots = get_available_slots_for_staff(selected_date, sm)

    # Check if the selected_date is today and filter out past slots
    if selected_date == date.today():
        # Get the current time in EDT timezone
        current_time_edt = datetime.now(pytz.timezone(APP_TIME_ZONE)).time()
        available_slots = [slot for slot in available_slots if convert_str_to_time(slot) > current_time_edt]

    custom_data['available_slots'] = available_slots
    if len(available_slots) == 0:
        custom_data['error'] = True
        message = _('No availability')
        return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
    custom_data['error'] = False
    return json_response(message='Successfully retrieved available slots', custom_data=custom_data, success=True)


@require_ajax
def get_next_available_date_ajax(request, service_id):
    """This view function handles AJAX requests to get the next available date for a service.

    :param request: The request instance.
    :param service_id: The ID of the service.
    :return: A JSON response containing the next available date.
    """
    staff_id = request.GET.get('staff_id')

    # If staff_id is not provided, you should handle it accordingly.
    if staff_id and staff_id != 'none':
        staff_member = get_object_or_404(StaffMember, pk=staff_id)
        service = get_object_or_404(Service, pk=service_id)

        # Fetch the days off for the staff
        days_off = DayOff.objects.filter(staff_member=staff_member).filter(
            Q(start_date__lte=date.today(), end_date__gte=date.today()) |
            Q(start_date__gte=date.today())
        )

        current_date = date.today()
        next_available_date = None
        day_offset = 0

        while next_available_date is None:
            potential_date = current_date + timedelta(days=day_offset)

            # Check if the potential date is a day off for the staff
            is_day_off = any([day_off.start_date <= potential_date <= day_off.end_date for day_off in days_off])
            # Check if the potential date is a working day for the staff
            weekday_num = get_weekday_num_from_date(potential_date)
            is_working_day_ = is_working_day(staff_member=staff_member, day=weekday_num)

            if not is_day_off and is_working_day_:
                x, available_slots = get_appointments_and_slots(potential_date, service)
                if available_slots:
                    next_available_date = potential_date

            day_offset += 1
        message = _('Successfully retrieved next available date')
        data = {'next_available_date': next_available_date.isoformat()}
        return json_response(message=message, custom_data=data, success=True)
    else:
        data = {'error': True}
        message = _('No staff member selected')
        return json_response(message=message, custom_data=data, success=False, error_code=ErrorCode.STAFF_ID_REQUIRED)


def get_non_working_days_ajax(request):
    staff_id = request.GET.get('staff_id')
    error = False
    message = _('Successfully retrieved non-working days')

    if not staff_id or staff_id == 'none':
        message = _('No staff member selected')
        error_code = ErrorCode.STAFF_ID_REQUIRED
        error = True
    else:
        non_working_days = get_non_working_days_for_staff(staff_id)
        custom_data = {"non_working_days": non_working_days}
        return json_response(message=message, custom_data=custom_data, success=not error)

    custom_data = {'error': error}
    return json_response(message=message, custom_data=custom_data, success=not error, error_code=error_code)


def appointment_request(request, service_id=None, staff_member_id=None):
    """This view function handles requests to book an appointment for a service.

    :param request: The request instance.
    :param service_id: The ID of the service.
    :param staff_member_id: The ID of the staff member.
    :return: The rendered HTML page.
    """

    service = None
    staff_member = None
    all_staff_members = None
    available_slots = []
    config = Config.objects.first()
    label = config.app_offered_by_label if config else _("Offered by")

    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        all_staff_members = StaffMember.objects.filter(services_offered=service)

        # If only one staff member for a service, choose them by default and fetch their slots.
        if all_staff_members.count() == 1:
            staff_member = all_staff_members.first()
            x, available_slots = get_appointments_and_slots(date.today(), service)

    # If a specific staff member is selected, fetch their slots.
    if staff_member_id:
        staff_member = get_object_or_404(StaffMember, pk=staff_member_id)
        y, available_slots = get_appointments_and_slots(date.today(), service)

    page_title = f"{service.name} - {get_website_name()}"
    page_description = _("Book an appointment for {s} at {wn}.").format(s=service.name, wn=get_website_name())

    date_chosen = date.today().strftime("%a, %B %d, %Y")
    extra_context = {
        'service': service,
        'staff_member': staff_member,
        'all_staff_members': all_staff_members,
        'page_title': page_title,
        'page_description': page_description,
        'available_slots': available_slots,
        'date_chosen': date_chosen,
        'locale': get_locale(),
        'timezoneTxt': get_timezone_txt(),
        'label': label
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/appointments.html', context=context)


def appointment_request_submit(request):
    """This view function handles the submission of the appointment request form.

    :param request: The request instance.
    :return: The rendered HTML page.
    """
    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        if form.is_valid():
            # Use form.cleaned_data to get the cleaned and validated data
            staff_member = form.cleaned_data['staff_member']

            staff_exists = StaffMember.objects.filter(id=staff_member.id).exists()
            if not staff_exists:
                messages.error(request, _("Selected staff member does not exist."))
            else:
                logger.info(
                    f"date_f {form.cleaned_data['date']} start_time {form.cleaned_data['start_time']} end_time "
                    f"{form.cleaned_data['end_time']} service {form.cleaned_data['service']} staff {staff_member}")
                ar = form.save()
                # Redirect the user to the account creation page
                return redirect('appointment:appointment_client_information', appointment_request_id=ar.id,
                                id_request=ar.id_request)
        else:
            # Handle the case if the form is not valid
            messages.error(request, _('There was an error in your submission. Please check the form and try again.'))
    else:
        form = AppointmentRequestForm()

    context = get_generic_context_with_extra(request, {'form': form}, admin=False)
    return render(request, 'appointment/appointments.html', context=context)


def redirect_to_payment_or_thank_you_page(appointment):
    """This function redirects to the payment page or the thank-you page based on the configuration.

    :param appointment: The Appointment instance.
    :return: The redirect response.
    """
    if APPOINTMENT_PAYMENT_URL is not None and APPOINTMENT_PAYMENT_URL != '':
        payment_url = create_payment_info_and_get_url(appointment)
        return HttpResponseRedirect(payment_url)
    elif APPOINTMENT_THANK_YOU_URL is not None and APPOINTMENT_THANK_YOU_URL != '':
        thank_you_url = reverse(APPOINTMENT_THANK_YOU_URL, kwargs={'appointment_id': appointment.id})
        return HttpResponseRedirect(thank_you_url)
    else:
        # Redirect to your default thank you page and pass the appointment object ID
        return HttpResponseRedirect(
            reverse('appointment:default_thank_you', kwargs={'appointment_id': appointment.id})
        )


def create_appointment(request, appointment_request_obj, client_data, appointment_data):
    """This function creates a new appointment and redirects to the payment page or the thank-you page.

    :param request: The request instance.
    :param appointment_request_obj: The AppointmentRequest instance.
    :param client_data: The client data.
    :param appointment_data: The appointment data.
    :return: The redirect response.
    """
    appointment = create_and_save_appointment(appointment_request_obj, client_data, appointment_data)
    return redirect_to_payment_or_thank_you_page(appointment)


def get_client_data_from_post(request):
    """This function retrieves client data from the POST request.

    :param request: The request instance.
    :return: The client data.
    """
    return {
        'name': request.POST.get('name'),
        'email': request.POST.get('email'),
    }


def get_appointment_data_from_post_request(request):
    """This function retrieves appointment data from the POST request.

    :param request: The request instance.
    :return: The appointment data.
    """
    return {
        'phone': request.POST.get('phone'),
        'want_reminder': request.POST.get('want_reminder') == 'on',
        'address': request.POST.get('address'),
        'additional_info': request.POST.get('additional_info'),
    }


def create_user_and_notify_admin(request, client_data, appointment_data):
    """This function creates a new user, sends a thank-you email, and notifies the admin.

    :param request: The request instance.
    :param client_data: The client data.
    :param appointment_data: The appointment data.
    :return: The newly created user.
    """
    logger.info("Creating a new user with the given information {client_data}")
    user = create_new_user(client_data)

    notify_admin(subject="New Appointment Request",
                 message=f"New appointment request from {client_data['email']} for {appointment_data}")
    messages.success(request, _("An account was created for you."))
    return user


def appointment_client_information(request, appointment_request_id, id_request):
    """This view function handles client information submission for an appointment.

    :param request: The request instance.
    :param appointment_request_id: The ID of the appointment request.
    :param id_request: The unique ID of the appointment request.
    :return: The rendered HTML page.
    """
    ar = get_object_or_404(AppointmentRequest, pk=appointment_request_id)

    if request.method == 'POST':
        appointment_form = AppointmentForm(request.POST)

        if appointment_form.is_valid():
            appointment_data = appointment_form.cleaned_data
            client_data = get_client_data_from_post(request)
            payment_type = request.POST.get('payment_type')
            ar.payment_type = payment_type
            ar.save()

            # Check if email is already in the database
            is_email_in_db = CLIENT_MODEL.objects.filter(email__exact=client_data['email']).exists()
            if is_email_in_db:
                return handle_existing_email(request, client_data, appointment_data, appointment_request_id, id_request)

            create_user_and_notify_admin(request, client_data, appointment_data)

            # Create a new appointment
            response = create_appointment(request, ar, client_data, appointment_data)
            return response
    else:
        appointment_form = AppointmentForm()

    extra_context = {
        'ar': ar,
        'APPOINTMENT_PAYMENT_URL': APPOINTMENT_PAYMENT_URL,
        'form': appointment_form,
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/appointment_client_information.html', context=context)


def verify_user_and_login(request, user, code):
    """This function verifies the user's email and logs the user in.

    :param request: The request instance.
    :param user: The User instance.
    :param code: The verification code.
    """
    if user and EmailVerificationCode.objects.filter(user=user, code=code).exists():
        logger.info(f"Email verified successfully for user {user}")
        login(request, user)
        messages.success(request, _("Email verified successfully."))
        return True
    else:
        messages.error(request, _("Invalid verification code."))
        return False


def enter_verification_code(request, appointment_request_id, id_request):
    """This view function handles the submission of the email verification code.

    :param request: The request instance.
    :param appointment_request_id: The ID of the appointment request.
    :param id_request: The unique ID of the appointment request.
    :return: The rendered HTML page.
    """
    if request.method == 'POST':
        email = request.session.get('email')
        code = request.POST.get('code')
        user = get_user_by_email(email)

        if verify_user_and_login(request, user, code):
            appointment_request_object = AppointmentRequest.objects.get(pk=appointment_request_id)
            appointment_data = get_appointment_data_from_session(request)
            response = create_appointment(request=request, appointment_request_obj=appointment_request_object,
                                          client_data={'email': email}, appointment_data=appointment_data)
            appointment = Appointment.objects.get(appointment_request=appointment_request_object)
            appointment_details = {
                'Service': appointment.get_service_name(),
                'Appointment ID': appointment.id_request,
                'Appointment Date': appointment.get_appointment_date(),
                'Appointment Time': appointment.appointment_request.start_time,
                'Duration': appointment.get_service_duration()
            }
            send_thank_you_email(ar=appointment_request_object, first_name=user.first_name, email=email,
                                 appointment_details=appointment_details)
            return response
        else:
            messages.error(request, _("Invalid verification code."))

    # base_template = request.session.get('BASE_TEMPLATE', '')
    # if base_template == '':
    #     base_template = APPOINTMENT_BASE_TEMPLATE
    extra_context = {
        'appointment_request_id': appointment_request_id,
        'id_request': id_request,
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/enter_verification_code.html', context)


def default_thank_you(request, appointment_id):
    """This view function handles the default thank you page.

    :param request: The request instance.
    :param appointment_id: The ID of the appointment.
    :return: The rendered HTML page.
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    ar = appointment.appointment_request
    first_name = appointment.client.first_name
    email = appointment.client.email
    appointment_details = {
        _('Service'): appointment.get_service_name(),
        _('Appointment ID'): appointment.id_request,
        _('Appointment Date'): appointment.get_appointment_date(),
        _('Appointment Time'): appointment.appointment_request.start_time,
        _('Duration'): appointment.get_service_duration()
    }
    account_details = {
        _('The email address linked to this account'): email,
        _('Your temporary password'): f"{get_website_name()}{get_current_year()}",
    }
    if username_in_user_model():
        account_details[_('Your username')] = appointment.client.username
    send_thank_you_email(ar=ar, first_name=first_name, email=email, appointment_details=appointment_details,
                         account_details=account_details)
    extra_context = {
        'appointment': appointment,
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/default_thank_you.html', context=context)
