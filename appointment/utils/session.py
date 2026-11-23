# session.py
# Path: appointment/utils/session.py

"""
Author: Adams Pierre David
Since: 1.1.0
"""

import hashlib

from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from phonenumber_field.phonenumber import PhoneNumber

from appointment.logger_config import get_logger
from appointment.utils.db_helpers import get_user_by_email, get_user_model, parse_name
from appointment.utils.email_ops import send_verification_email

CLIENT_MODEL = get_user_model()

logger = get_logger(__name__)

VERIFICATION_EMAILS_PER_HOUR = 3


def can_send_verification_email(email) -> bool:
    """Count the codes sent to an address. At most VERIFICATION_EMAILS_PER_HOUR are sent in an hour."""
    key = 'appointment_verification_emails_' + hashlib.sha256(email.lower().encode()).hexdigest()
    cache.add(key, 0, timeout=3600)
    try:
        count = cache.incr(key)
    except ValueError:  # the key expired in between
        cache.set(key, 1, timeout=3600)
        count = 1
    return count <= VERIFICATION_EMAILS_PER_HOUR


def login_or_create_user_by_mail(request, client_data, appointment_data, appointment_request_id, id_request):
    """
    Handle the case where an appointment request is submitted by an unauthenticated user.

    Sends a verification email to the provided email and redirects the client to enter the verification code.

    If the email is already in the session variables, clean the session variables for email, phone, want_reminder,
    address, and additional_info. Then, store the current email, phone, want_reminder, address, and additional_info
    in the session.

    :param request: The Django HttpRequest object.
    :param client_data: The data of the client for the appointment.
    :param appointment_data: The data of the appointment.
    :param appointment_request_id: The ID of the appointment request.
    :param id_request: The unique ID for the appointment request.
    :return: The redirect response to enter the verification code.
    """
    email = client_data['email']
    if not can_send_verification_email(email):
        messages.error(request, _("Too many codes were sent to this address. Please try again later."))
        return redirect('appointment:appointment_client_information', appointment_request_id=appointment_request_id,
                        id_request=id_request)

    # The same message whether the address has an account or not. A new client's account is only created once they
    # enter the code (see enter_verification_code).
    user = get_user_by_email(email)
    send_verification_email(user=user, email=email, request=request,
                            first_name=parse_name(client_data.get('name', ''))[0])
    messages.info(request, _("We sent a code to {email}. Enter it below to confirm your booking.").format(
        email=email))

    # clean the session variables
    session_keys = ['email', 'name', 'phone', 'want_reminder', 'address', 'additional_info']
    phone = appointment_data['phone']

    for key in session_keys:
        if key in request.session:
            del request.session[key]

    request.session['email'] = client_data['email']
    request.session['name'] = client_data.get('name', '')
    request.session['phone'] = str(phone)
    request.session['want_reminder'] = appointment_data['want_reminder']
    request.session['address'] = appointment_data['address']
    request.session['additional_info'] = appointment_data['additional_info']

    # request.session['BASE_TEMPLATE'] = get_generic_context(request, admin=False)['BASE_TEMPLATE']
    request.session.modified = True
    return redirect('appointment:enter_verification_code', appointment_request_id=appointment_request_id,
                    id_request=id_request)


def handle_email_change(request, user, email):
    """Send a code to the new address. The email changes once the code is entered."""
    send_verification_email(user=user, email=email, request=request)
    request.session['email_change'] = {'user_id': user.pk, 'email': email}
    request.session.modified = True
    return redirect('appointment:email_change_verification_code')


def get_appointment_data_from_session(request):
    """
    Get the appointment data from the session variables.
    Retrieves the phone, want_reminder, address, and additional_info stored in the session.

    :param request: The Django HttpRequest object.
    :return: The appointment data retrieved from the session.
    """
    phone = request.session.get('phone')
    phone_obj = PhoneNumber.from_string(phone)
    want_reminder = request.session.get('want_reminder', False)
    address = request.session.get('address')
    additional_info = request.session.get('additional_info')

    return {
        'phone': phone_obj,
        'want_reminder': want_reminder,
        'address': address,
        'additional_info': additional_info,
    }
