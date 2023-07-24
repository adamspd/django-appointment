import datetime
import logging
import sys
from datetime import date, timedelta

from django.apps import apps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from appointment.email_sender import send_email, notify_admin
from appointment.forms import AppointmentRequestForm
from appointment.models import Service, Appointment, AppointmentRequest, PaymentInfo, EmailVerificationCode
from appointment.utils import Utility
from . import email_messages
from .settings import (APPOINTMENT_CLIENT_MODEL, APPOINTMENT_BASE_TEMPLATE, APPOINTMENT_WEBSITE_NAME,
                       APPOINTMENT_PAYMENT_URL, APPOINTMENT_THANK_YOU_URL)

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# configure basicConfig with the formatter, log level, and handlers
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG,
                    handlers=[logging.StreamHandler(sys.stdout)])

CLIENT_MODEL = apps.get_model(APPOINTMENT_CLIENT_MODEL)


def get_available_slots_ajax(request):
    if Utility.is_ajax(request=request):
        # Get the selected date from the AJAX request
        today = date.today()
        selected_date = request.GET.get('selected_date')

        # Convert the selected date string to a datetime object
        selected_date = datetime.datetime.strptime(selected_date, '%Y-%m-%d').date()

        # Get the appointments for the selected date
        if selected_date < today:
            return JsonResponse(
                {
                    'available_slots': [],
                    'date_chosen': '',
                    'error': True,
                    'message': 'Date is in the past',
                })
        appointments = Appointment.objects.filter(appointment_request__date=selected_date)

        # Get the available slots for the selected date
        available_slots = Utility.get_available_slots(selected_date, appointments)
        date_chosen = selected_date.strftime("%A, %B %d, %Y")
        # Return the available slots as a JSON response
        if len(available_slots) == 0:
            return JsonResponse(
                {'available_slots': available_slots, 'date_chosen': date_chosen, 'message': 'No availability',
                 'error': False})
        return JsonResponse(
            {'available_slots': available_slots, 'date_chosen': date_chosen, 'message': '', 'error': False})


def get_next_available_date_ajax(request, service_id):
    if Utility.is_ajax(request=request):
        # Get the service and the current date
        service = get_object_or_404(Service, pk=service_id)
        current_date = date.today()

        # Find the next date with available slots
        next_available_date = None
        day_offset = 0
        while next_available_date is None:
            potential_date = current_date + timedelta(days=day_offset)
            appointments = Appointment.objects.filter(appointment_request__service=service,
                                                      appointment_request__date=potential_date)
            available_slots = Utility.get_available_slots(potential_date, appointments)
            if available_slots:
                next_available_date = potential_date
            day_offset += 1

        # Return the next available date as a JSON response
        return JsonResponse({'next_available_date': next_available_date.isoformat()})


def appointment_request(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    page_title = f"{service.name} - {APPOINTMENT_WEBSITE_NAME}"
    page_description = f"Book an appointment for {service.name} at {APPOINTMENT_WEBSITE_NAME}."

    # get available slots for the day
    appointments = Appointment.objects.filter(appointment_request__service=service,
                                              appointment_request__date=date.today())
    available_slots = Utility.get_available_slots(date.today(), appointments)
    date_chosen = date.today().strftime("%A, %B %d, %Y")
    context = {
        'service': service,
        'page_title': page_title,
        'page_description': page_description,
        'available_slots': available_slots,
        'date_chosen': date_chosen,
        'locale': Utility.get_locale(),
        'timezone': Utility.get_timezone(),
        'APPOINTMENT_BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
    }
    return render(request, 'appointment/appointments.html', context=context)


def appointment_request_submit(request):
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
        logger.info("else")
        form = AppointmentRequestForm()

    return render(request, 'appointment/appointments.html', {'form': form})


def get_email_message(ar):
    if APPOINTMENT_PAYMENT_URL is None:
        message = email_messages.thank_you_no_payment
    elif ar.accepts_down_payment():
        message = email_messages.thank_you_payment_plus_down
    else:
        message = email_messages.thank_you_payment
    return message


def send_email_to_client(ar, first_name, email):
    email_context = {
        'first_name': first_name,
        'message': get_email_message(ar),
        'current_year': datetime.datetime.now().year,
        'company': APPOINTMENT_WEBSITE_NAME
    }
    send_email(
        recipient_list=[email], subject="Thank you for booking us.",
        template_url='email_sender/thank_you_email.html', context=email_context
    )


def create_appointment(request, appointment_request_obj, client_data, appointment_data):
    user = CLIENT_MODEL.objects.filter(email=client_data['email']).first()
    appointment = Appointment.objects.create(
        client=user, appointment_request=appointment_request_obj,
        **appointment_data
    )
    appointment.save()
    logger.info(f"New appointment created: {appointment}")
    if APPOINTMENT_PAYMENT_URL:
        payment_info = PaymentInfo(appointment=appointment)
        payment_info.save()
        payment_url = reverse(
            APPOINTMENT_PAYMENT_URL,
            kwargs={'object_id': payment_info.id, 'id_request': payment_info.get_id_request()}
        )
        return HttpResponseRedirect(payment_url)
    elif APPOINTMENT_THANK_YOU_URL:
        thank_you_url = reverse(APPOINTMENT_THANK_YOU_URL, kwargs={'appointment_id': appointment.id})
        return HttpResponseRedirect(thank_you_url)
    else:
        # Redirect to your default thank you page and pass the appointment object ID
        return HttpResponseRedirect(
            reverse('appointment:default_thank_you', kwargs={'appointment_id': appointment.id})
        )


def appointment_client_information(request, appointment_request_id, id_request):
    ar = get_object_or_404(AppointmentRequest, pk=appointment_request_id)
    if request.method == 'POST':
        appointment_data = {
            'phone': request.POST.get('phone'),
            'want_reminder': request.POST.get('want_reminder') == 'on',
            'address': request.POST.get('address'),
            'additional_info': request.POST.get('additional_info'),
        }
        client_data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
        }
        payment_type = request.POST.get('payment_type')

        ar.payment_type = payment_type
        ar.save()
        logger.info(
            f"Information received: \nappointment data : {appointment_data}\nclient data : {client_data}\npayment type : {payment_type}")

        # Check if email is already in the database
        is_email_in_db = CLIENT_MODEL.objects.filter(email__exact=client_data['email']).exists()
        if is_email_in_db:
            logger.info("Email already in database, saving info in session and redirecting to enter verification code")
            user = CLIENT_MODEL.objects.filter(email=client_data['email']).first()
            code = EmailVerificationCode.generate_code(user=user)
            # send the verification email
            message = f"Your verification code is {code}."
            send_email(recipient_list=[client_data['email']], subject="Email Verification", message=message)

            # clean the session variables
            session_keys = ['email', 'phone', 'want_reminder', 'address', 'additional_info']
            for key in session_keys:
                if key in request.session:
                    del request.session[key]

            request.session['email'] = client_data['email']
            request.session['phone'] = appointment_data['phone']
            request.session['want_reminder'] = appointment_data['want_reminder']
            request.session['address'] = appointment_data['address']
            request.session['additional_info'] = appointment_data['additional_info']

            request.session['APPOINTMENT_BASE_TEMPLATE'] = APPOINTMENT_BASE_TEMPLATE

            messages.error(request, f"Email '{client_data['email']}' already exists. Login to your account.")
            return redirect('appointment:enter_verification_code', appointment_request_id=appointment_request_id,
                            id_request=id_request)

        # Create a new user
        logger.info("Creating a new user with the given information {client_data}")
        username = client_data['email'].split('@')[0]
        user = CLIENT_MODEL.objects.create_user(first_name=client_data['name'], email=client_data['email'],
                                                username=username)
        password = f"{APPOINTMENT_WEBSITE_NAME}{Utility.get_current_year()}"
        user.password = make_password(password=password)
        user.save()

        # Email the user
        message = email_messages.thank_you_no_payment if APPOINTMENT_PAYMENT_URL is None else email_messages.thank_you_payment
        email_context = {
            'first_name': user.first_name,
            'message': message,
            'current_year': datetime.datetime.now().year,
            'company': APPOINTMENT_WEBSITE_NAME
        }
        send_email(
            recipient_list=[client_data['email']], subject="Thank you for booking us.",
            template_url='email_sender/thank_you_email.html', context=email_context
        )
        notify_admin(subject="New Appointment Request",
                     message=f"New appointment request from {client_data['email']} for {appointment_data}")
        messages.success(request, _("An account was created for you."))

        # Create a new appointment
        response = create_appointment(request, ar, client_data, appointment_data)
        return response

    context = {
        'ar': ar,
        'APPOINTMENT_BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
        'buttonNext': _("Pay Now") if APPOINTMENT_PAYMENT_URL else _("Finish"),
    }
    return render(request, 'appointment/appointment_client_information.html', context=context)


def enter_verification_code(request, appointment_request_id, id_request):
    if request.method == 'POST':
        email = request.session.get('email')
        code = request.POST.get('code')
        user = CLIENT_MODEL.objects.filter(email=email).first()

        if user and EmailVerificationCode.objects.filter(user=user, code=code).exists():
            logger.info(f"Email verified successfully for user {user}")
            login(request, user)
            messages.success(request, "Email verified successfully.")
            appointment_request_object = AppointmentRequest.objects.get(pk=appointment_request_id)

            phone = request.session.get('phone')
            want_reminder = request.session.get('want_reminder') == 'on'
            address = request.session.get('address')
            additional_info = request.session.get('additional_info')

            appointment_data = {
                'phone': phone,
                'want_reminder': want_reminder,
                'address': address,
                'additional_info': additional_info,
            }

            response = create_appointment(request=request, appointment_request_obj=appointment_request_object,
                                          client_data={'email': email}, appointment_data=appointment_data)
            return response
        else:
            messages.error(request, "Invalid verification code.")

    base_template = request.session.get('APPOINTMENT_BASE_TEMPLATE', '')
    context = {
        'appointment_request_id': appointment_request_id,
        'id_request': id_request,
        'APPOINTMENT_BASE_TEMPLATE': base_template,
    }
    return render(request, 'appointment/enter_verification_code.html', context)


def default_thank_you(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    context = {
        'appointment': appointment,
        'APPOINTMENT_BASE_TEMPLATE': APPOINTMENT_BASE_TEMPLATE,
    }
    return render(request, 'appointment/default_thank_you.html', context=context)
