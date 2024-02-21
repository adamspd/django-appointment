# tasks.py
# Path: appointment/tasks.py

"""
Author: Adams Pierre David
Since: 3.1.0
"""
from django.utils.translation import gettext as _

from appointment.email_sender import notify_admin, send_email
from appointment.logger_config import logger
from appointment.models import Appointment


def send_email_reminder(to_email, first_name, reschedule_link, appointment_id):
    """
    Send a reminder email to the client about the upcoming appointment.
    """

    # Fetch the appointment using appointment_id
    logger.info(f"Sending reminder to {to_email} for appointment {appointment_id}")
    appointment = Appointment.objects.get(id=appointment_id)
    recipient_type = 'client'
    email_context = {
        'first_name': first_name,
        'appointment': appointment,
        'reschedule_link': reschedule_link,
        'recipient_type': recipient_type,
    }
    send_email(
        recipient_list=[to_email], subject=_("Reminder: Upcoming Appointment"),
        template_url='email_sender/reminder_email.html', context=email_context
    )
    # Notify the admin
    email_context['recipient_type'] = 'admin'
    notify_admin(
        subject=_("Admin Reminder: Upcoming Appointment"),
        template_url='email_sender/reminder_email.html', context=email_context
    )
