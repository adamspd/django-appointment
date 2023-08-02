# appointment/operations/email_operations.py

import datetime

from appointment import email_messages
from appointment.email_sender import send_email
from appointment.models import EmailVerificationCode, AppointmentRequest
from appointment.settings import APPOINTMENT_PAYMENT_URL
from appointment.utils import Utility


def get_thank_you_message(ar: AppointmentRequest) -> str:
    """
    Get the appropriate email message based on the appointment request.

    If the payment URL is not set (APPOINTMENT_PAYMENT_URL is None), it returns the thank_you_no_payment message.
    If the appointment request accepts down payment, it returns the thank_you_payment_plus_down message.
    Otherwise, it returns the thank_you_payment message.

    Args:
        ar (AppointmentRequest): The appointment request.

    Returns:
        str: The appropriate email message.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    if APPOINTMENT_PAYMENT_URL is None:
        message = email_messages.thank_you_no_payment
    elif ar.accepts_down_payment():
        message = email_messages.thank_you_payment_plus_down
    else:
        message = email_messages.thank_you_payment
    return message


def send_thank_you_email(ar: AppointmentRequest, first_name: str, email: str, appointment_details=None):
    """
    Send a thank-you email to the client for booking an appointment.

    Args:
        ar (AppointmentRequest): The appointment request associated with the booking.
        first_name (str): The first name of the client.
        email (str): The email address of the client.
        appointment_details (str, optional): Additional details about the appointment (default None).

    Returns: None

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    email_context = {
        'first_name': first_name,
        'message': get_thank_you_message(ar),
        'current_year': datetime.datetime.now().year,
        'company': Utility.get_website_name(),
        'appointment_details': appointment_details,
    }
    send_email(
        recipient_list=[email], subject="Thank you for booking us.",
        template_url='email_sender/thank_you_email.html', context=email_context
    )


def send_verification_email(user, email: str):
    """
    Send an email with a verification code to the user for email verification.

    Generates a verification code using the EmailVerificationCode model and sends it to the user's email.

    Args:
        user (AppointmentClientModel): The user to verify the email address.
        email (str): The email address of the user.

    Returns: None

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    code = EmailVerificationCode.generate_code(user=user)
    message = f"Your verification code is {code}."
    send_email(recipient_list=[email], subject="Email Verification", message=message)
