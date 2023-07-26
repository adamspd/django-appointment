# appointment/operations/email_operations.py

import datetime

from appointment import email_messages
from appointment.email_sender import send_email
from appointment.models import EmailVerificationCode
from appointment.settings import APPOINTMENT_PAYMENT_URL
from appointment.utils import Utility


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
        'company': Utility.get_website_name(),
    }
    send_email(
        recipient_list=[email], subject="Thank you for booking us.",
        template_url='email_sender/thank_you_email.html', context=email_context
    )


def send_verification_email(user, email):
    code = EmailVerificationCode.generate_code(user=user)
    message = f"Your verification code is {code}."
    send_email(recipient_list=[email], subject="Email Verification", message=message)
