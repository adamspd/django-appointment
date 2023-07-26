# appointment/operations/database_operations.py

from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.urls import reverse

from appointment.models import Appointment, PaymentInfo
from logger_config import logger
from appointment.settings import APPOINTMENT_CLIENT_MODEL, APPOINTMENT_PAYMENT_URL
from appointment.utils import Utility

CLIENT_MODEL = apps.get_model(APPOINTMENT_CLIENT_MODEL)


def get_appointments_and_slots(date_, service=None):
    if service:
        appointments = Appointment.objects.filter(appointment_request__service=service,
                                                  appointment_request__date=date_)
    else:
        appointments = Appointment.objects.filter(appointment_request__date=date_)
    available_slots = Utility.get_available_slots(date_, appointments)
    return appointments, available_slots


def get_user_by_email(email):
    return CLIENT_MODEL.objects.filter(email=email).first()


def create_new_user(client_data):
    username = client_data['email'].split('@')[0]
    user = CLIENT_MODEL.objects.create_user(first_name=client_data['name'], email=client_data['email'],
                                            username=username)
    password = f"{Utility.get_website_name()}{Utility.get_current_year()}"
    user.password = make_password(password=password)
    user.save()
    return user


def create_and_save_appointment(ar, client_data, appointment_data):
    user = get_user_by_email(client_data['email'])
    appointment = Appointment.objects.create(
        client=user, appointment_request=ar,
        **appointment_data
    )
    appointment.save()
    logger.info(f"New appointment created: {appointment}")
    return appointment


def create_payment_info_and_get_url(appointment):
    payment_info = PaymentInfo(appointment=appointment)
    payment_info.save()
    payment_url = reverse(
        APPOINTMENT_PAYMENT_URL,
        kwargs={'object_id': payment_info.id, 'id_request': payment_info.get_id_request()}
    )
    return payment_url
