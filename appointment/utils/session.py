# session.py
# Path: appointment/utils/session.py

"""
Author: Adams Pierre David
Since: 1.1.0
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from phonenumber_field.phonenumber import PhoneNumber

from appointment.logger_config import logger
from appointment.utils.db_helpers import get_user_by_email
from appointment.utils.email_ops import send_verification_email


def handle_existing_email(request, client_data, appointment_data, appointment_request_id, id_request):
    """
    Handle the case where the email already exists in the database.

    Sends a verification email to the existing user and redirects the client to enter the verification code.

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
    logger.info("Email already in database, saving info in session and redirecting to enter verification code")
    user = get_user_by_email(client_data['email'])
    send_verification_email(user=user, email=client_data['email'])

    # clean the session variables
    session_keys = ['email', 'phone', 'want_reminder', 'address', 'additional_info']
    phone = appointment_data['phone']

    for key in session_keys:
        if key in request.session:
            del request.session[key]

    request.session['email'] = client_data['email']
    request.session['phone'] = str(phone)
    request.session['want_reminder'] = appointment_data['want_reminder']
    request.session['address'] = appointment_data['address']
    request.session['additional_info'] = appointment_data['additional_info']

    # request.session['BASE_TEMPLATE'] = get_generic_context(request, admin=False)['BASE_TEMPLATE']
    request.session.modified = True
    message = _("Email '{email}' already exists. Login to your account.").format(email=client_data['email'])
    messages.error(request, message)
    return redirect('appointment:enter_verification_code', appointment_request_id=appointment_request_id,
                    id_request=id_request)


def handle_email_change(request, user, email):
    send_verification_email(user=user, email=email)
    # clean the session variables
    session_keys = ['email', 'old_email']
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    request.session['email'] = email
    request.session['old_email'] = user.email
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
    want_reminder = request.session.get('want_reminder') == 'on'
    address = request.session.get('address')
    additional_info = request.session.get('additional_info')

    return {
        'phone': phone_obj,
        'want_reminder': want_reminder,
        'address': address,
        'additional_info': additional_info,
    }
