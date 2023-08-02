# appointment/views.py

from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from appointment.email_sender import notify_admin
from appointment.forms import AppointmentRequestForm
from appointment.logger_config import logger
from appointment.models import Service, Appointment, AppointmentRequest, EmailVerificationCode
from appointment.utils import Utility
from .operations.database_operations import get_appointments_and_slots, create_payment_info_and_get_url, \
    create_and_save_appointment, create_new_user, get_user_by_email
from .operations.email_operations import send_thank_you_email
from .operations.session_operations import handle_existing_email, get_appointment_data_from_session
from .settings import (APPOINTMENT_BASE_TEMPLATE,
                       APPOINTMENT_PAYMENT_URL, APPOINTMENT_THANK_YOU_URL)

CLIENT_MODEL = Utility.get_user_model()


def get_available_slots_ajax(request):
    """
    This view function handles AJAX requests to get available slots for a selected date.

    Args:
        request (HttpRequest): The request instance.

    Returns:
        JsonResponse: A JSON response containing available slots, selected date,
        an error flag, and an optional error message.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    if Utility.is_ajax(request=request):
        selected_date = Utility.convert_str_to_date(request.GET.get('selected_date'))

        if selected_date < date.today():
            return JsonResponse(
                {
                    'available_slots': [],
                    'date_chosen': '',
                    'error': True,
                    'message': 'Date is in the past',
                })

        _, available_slots = get_appointments_and_slots(selected_date)
        date_chosen = selected_date.strftime("%a, %B %d, %Y")

        if len(available_slots) == 0:
            return JsonResponse(
                {'available_slots': available_slots, 'date_chosen': date_chosen, 'message': 'No availability',
                 'error': False})
        return JsonResponse(
            {'available_slots': available_slots, 'date_chosen': date_chosen, 'message': '', 'error': False})


def get_next_available_date_ajax(request, service_id):
    """
    This view function handles AJAX requests to get the next available date for a service.

    Args:
        request (HttpRequest): The request instance.
        service_id (int): The ID of the service.

    Returns:
        JsonResponse: A JSON response containing the next available date.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    if Utility.is_ajax(request=request):
        service = get_object_or_404(Service, pk=service_id)
        current_date = date.today()
        next_available_date = None
        day_offset = 0
        while next_available_date is None:
            potential_date = current_date + timedelta(days=day_offset)
            _, available_slots = get_appointments_and_slots(potential_date, service)
            if available_slots:
                next_available_date = potential_date
            day_offset += 1
        return JsonResponse({'next_available_date': next_available_date.isoformat()})


def appointment_request(request, service_id):
    """
    This view function handles requests to book an appointment for a service.

    Args:
        request (HttpRequest): The request instance.
        service_id (int): The ID of the service.

    Returns:
        HttpResponse: The rendered HTML page.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    service = get_object_or_404(Service, pk=service_id)
    page_title = f"{service.name} - {Utility.get_website_name()}"
    page_description = f"Book an appointment for {service.name} at {Utility.get_website_name()}."

    _, available_slots = get_appointments_and_slots(date.today(), service)
    date_chosen = date.today().strftime("%a, %B %d, %Y")
    context = {
        'service': service,
        'page_title': page_title,
        'page_description': page_description,
        'available_slots': available_slots,
        'date_chosen': date_chosen,
        'locale': Utility.get_locale(),
        'timezoneTxt': Utility.get_timezone_txt(),
        'timezone': Utility.get_timezone(),
        'APPOINTMENT_BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
    }
    return render(request, 'appointment/appointments.html', context=context)


def appointment_request_submit(request):
    """
    This view function handles the submission of the appointment request form.

    Args:
        request (HttpRequest): The request instance.

    Returns:
        HttpResponse: The rendered HTML page.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        date_f = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        service = request.POST.get('service')

        logger.info(f"date_f {date_f} start_time {start_time} end_time {end_time} service {service}")
        if form.is_valid():
            ar = form.save()

            # Redirect the user to the account creation page
            return redirect('appointment:appointment_client_information', appointment_request_id=ar.id,
                            id_request=ar.id_request)
    else:
        form = AppointmentRequestForm()
    context = {
        'form': form,
        'APPOINTMENT_BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
    }

    return render(request, 'appointment/appointments.html', context=context)


def redirect_to_payment_or_thank_you_page(appointment):
    """
    This function redirects to the payment page or the thank-you page based on the configuration.

    Args:
        appointment (Appointment): The Appointment instance.

    Returns:
        HttpResponseRedirect: The redirect response.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
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
    """
    This function creates a new appointment and redirects to the payment page or the thank you page.

    Args:
        request (HttpRequest): The request instance.
        appointment_request_obj (AppointmentRequest): The AppointmentRequest instance.
        client_data (dict): The client data.
        appointment_data (dict): The appointment data.

    Returns:
        HttpResponseRedirect: The redirect response.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    appointment = create_and_save_appointment(appointment_request_obj, client_data, appointment_data)
    return redirect_to_payment_or_thank_you_page(appointment)


def get_client_data_from_post(request):
    """
    This function retrieves client data from the POST request.

    Args:
        request (HttpRequest): The request instance.

    Returns:
        dict: The client data.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    return {
        'name': request.POST.get('name'),
        'email': request.POST.get('email'),
    }


def get_appointment_data_from_post_request(request):
    """
    This function retrieves appointment data from the POST request.

    Args:
        request (HttpRequest): The request instance.

    Returns:
        dict: The appointment data.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    return {
        'phone': request.POST.get('phone'),
        'want_reminder': request.POST.get('want_reminder') == 'on',
        'address': request.POST.get('address'),
        'additional_info': request.POST.get('additional_info'),
    }


def create_user_and_send_email(request, ar, client_data, appointment_data):
    """
    This function creates a new user, sends a thank-you email, and notifies the admin.

    Args:
        request (HttpRequest): The request instance.
        ar (AppointmentRequest): The AppointmentRequest instance.
        client_data (dict): The client data.
        appointment_data (dict): The appointment data.

    Returns:
        django.contrib.auth.models.User: The newly created user.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    logger.info("Creating a new user with the given information {client_data}")
    user = create_new_user(client_data)

    # Email the user
    send_thank_you_email(ar, user.first_name, user.email)
    notify_admin(subject="New Appointment Request",
                 message=f"New appointment request from {client_data['email']} for {appointment_data}")
    messages.success(request, _("An account was created for you."))
    return user


def appointment_client_information(request, appointment_request_id, id_request):
    """
    This view function handles client information submission for an appointment.

    Args:
        request (HttpRequest): The request instance.
        appointment_request_id (int): The ID of the appointment request.
        id_request (str): The unique ID of the appointment request.

    Returns:
        HttpResponse: The rendered HTML page.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    ar = get_object_or_404(AppointmentRequest, pk=appointment_request_id)
    if request.method == 'POST':
        appointment_data = get_appointment_data_from_post_request(request)
        client_data = get_client_data_from_post(request)
        payment_type = request.POST.get('payment_type')
        ar.payment_type = payment_type
        ar.save()
        logger.info(
            f"Information received: \nappointment data : {appointment_data}\nclient data : {client_data}\n"
            f"payment type : {payment_type}")

        # Check if email is already in the database
        is_email_in_db = CLIENT_MODEL.objects.filter(email__exact=client_data['email']).exists()
        if is_email_in_db:
            return handle_existing_email(request, client_data, appointment_data, appointment_request_id, id_request)

        create_user_and_send_email(request, ar, client_data, appointment_data)

        # Create a new appointment
        response = create_appointment(request, ar, client_data, appointment_data)
        return response

    context = {
        'ar': ar,
        'APPOINTMENT_BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
        'buttonNext': Utility.get_finish_button_text(ar),
    }
    return render(request, 'appointment/appointment_client_information.html', context=context)


def verify_user_and_login(request, user, code):
    """
    This function verifies the user's email and logs the user in.

    Args:
        request (HttpRequest): The request instance.
        user: The User instance.
        code (str): The verification code.

    Returns:
        bool: True if the user is verified and logged in, False otherwise.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    if user and EmailVerificationCode.objects.filter(user=user, code=code).exists():
        logger.info(f"Email verified successfully for user {user}")
        login(request, user)
        messages.success(request, "Email verified successfully.")
        return True
    else:
        messages.error(request, "Invalid verification code.")
        return False


def enter_verification_code(request, appointment_request_id, id_request):
    """
    This view function handles the submission of the email verification code.

    Args:
        request (HttpRequest): The request instance.
        appointment_request_id (int): The ID of the appointment request.
        id_request (str): The unique ID of the appointment request.

    Returns:
        HttpResponse: The rendered HTML page.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
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
            return response
        else:
            messages.error(request, "Invalid verification code.")

    base_template = request.session.get('APPOINTMENT_BASE_TEMPLATE', '')
    if base_template == '':
        base_template = APPOINTMENT_BASE_TEMPLATE
    context = {
        'appointment_request_id': appointment_request_id,
        'id_request': id_request,
        'APPOINTMENT_BASE_TEMPLATE': base_template,
    }
    return render(request, 'appointment/enter_verification_code.html', context)


def default_thank_you(request, appointment_id):
    """
    This view function handles the default thank you page.

    Args:
        request (HttpRequest): The request instance.
        appointment_id (int): The ID of the appointment.

    Returns:
        HttpResponse: The rendered HTML page.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    ar = appointment.appointment_request
    first_name = appointment.client.first_name
    email = appointment.client.email
    appointment_details = {
        'Service': appointment.get_service_name(),
        'Appointment ID': appointment.id_request,
        'Appointment Date': appointment.get_appointment_date(),
        'Appointment Time': appointment.appointment_request.get_start_time(),
        'Duration': appointment.appointment_request.get_service_duration()
    }
    send_thank_you_email(ar=ar, first_name=first_name, email=email, appointment_details=appointment_details)
    context = {
        'appointment': appointment,
        'APPOINTMENT_BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
    }
    return render(request, 'appointment/default_thank_you.html', context=context)
