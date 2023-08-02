# appointment/operations/database_operations.py

from django.contrib.auth.hashers import make_password
from django.urls import reverse

from appointment.logger_config import logger
from appointment.models import Appointment, PaymentInfo
from appointment.settings import APPOINTMENT_PAYMENT_URL
from appointment.utils import Utility

CLIENT_MODEL = Utility.get_user_model()


def get_appointments_and_slots(date_, service=None):
    """
    Get appointments and available slots for a given date and service.

    If a service is provided, the function retrieves appointments for that service on the given date.
    Otherwise, it retrieves all appointments for the given date.

    Args:
        date_ (datetime.date): The date for which to retrieve appointments and available slots.
        service (Service, optional): The service for which to retrieve appointments.

    Returns:
        tuple: A tuple containing two elements:
            - A queryset of appointments for the given date and service (if provided).
            - A list of available time slots on the given date, excluding booked appointments.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    if service:
        appointments = Appointment.objects.filter(appointment_request__service=service,
                                                  appointment_request__date=date_)
    else:
        appointments = Appointment.objects.filter(appointment_request__date=date_)
    available_slots = Utility.get_available_slots(date_, appointments)
    return appointments, available_slots


def get_user_by_email(email: str):
    """
    Get a user by their email address.

    Args:
        email (str): The email address of the user.

    Returns:
        AppointmentClientModel: The user with the specified email address, if found; otherwise, None.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    return CLIENT_MODEL.objects.filter(email=email).first()


def create_new_user(client_data):
    """
    Create a new user and save it to the database.

    Args:
        client_data (dict): The data of the new user, including name and email.

    Returns:
        AppointmentClientModel: The newly created user.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    username = client_data['email'].split('@')[0]
    user = CLIENT_MODEL.objects.create_user(first_name=client_data['name'], email=client_data['email'],
                                            username=username)
    password = f"{Utility.get_website_name()}{Utility.get_current_year()}"
    user.password = make_password(password=password)
    user.save()
    return user


def create_and_save_appointment(ar, client_data, appointment_data):
    """
    Create and save a new appointment based on the provided appointment request and client data.

    Args:
        ar (AppointmentRequest): The appointment request associated with the new appointment.
        client_data (dict): The data of the client making the appointment.
        appointment_data (dict): Additional data for the appointment, including phone number, address, etc.

    Returns:
        Appointment: The newly created appointment.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    user = get_user_by_email(client_data['email'])
    appointment = Appointment.objects.create(
        client=user, appointment_request=ar,
        **appointment_data
    )
    appointment.save()
    logger.info(f"New appointment created: {appointment}")
    return appointment


def create_payment_info_and_get_url(appointment):
    """
    Create a new payment information entry for the appointment and return the payment URL.

    Args:
        appointment (Appointment): The appointment for which to create payment information.

    Returns:
        str: The payment URL for the appointment.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    payment_info = PaymentInfo(appointment=appointment)
    payment_info.save()
    payment_url = reverse(
        APPOINTMENT_PAYMENT_URL,
        kwargs={'object_id': payment_info.id, 'id_request': payment_info.get_id_request()}
    )
    return payment_url
