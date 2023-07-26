# appointment/operations/session_operations.py

from django.contrib import messages
from django.shortcuts import redirect

from appointment.operations.database_operations import get_user_by_email
from appointment.operations.email_operations import send_verification_email
from logger_config import logger
from appointment.settings import APPOINTMENT_BASE_TEMPLATE


def handle_existing_email(request, client_data, appointment_data, appointment_request_id, id_request):
    logger.info("Email already in database, saving info in session and redirecting to enter verification code")
    user = get_user_by_email(client_data['email'])
    send_verification_email(user=user, email=client_data['email'])

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


def get_appointment_data_from_session(request):
    phone = request.session.get('phone')
    want_reminder = request.session.get('want_reminder') == 'on'
    address = request.session.get('address')
    additional_info = request.session.get('additional_info')

    return {
        'phone': phone,
        'want_reminder': want_reminder,
        'address': address,
        'additional_info': additional_info,
    }
