# tasks.py
# Path: appointment/tasks.py

"""
Author: Adams Pierre David
Since: 3.1.0
"""
from datetime import timedelta

from django.utils import timezone

from appointment.email_sender import notify_admin, send_email
from appointment.email_sender.email_sender import html_to_text, send_email_now
from appointment.logger_config import get_logger
from appointment.models import Appointment, AppointmentRequest
from appointment.settings import APPOINTMENT_CLEANUP_DAYS

logger = get_logger(__name__)


def send_email_reminder(to_email, first_name, reschedule_link, appointment_id, site_url=None):
    """
    Send a reminder email to the client about the upcoming appointment.

    ``site_url`` is the site's address when the reminder was scheduled, for the email's links. Reminders queued before
    3.13.0 don't pass it, and get relative links.
    """

    from appointment.utils.email_ops import build_reminder_email

    logger.info(f"Sending reminder to {to_email} for appointment {appointment_id}")
    appointment = Appointment.objects.get(id=appointment_id)
    email_parts = build_reminder_email(appointment, first_name, reschedule_link, site_url=site_url)
    send_email(recipient_list=[to_email], subject=email_parts['subject'], template_url=email_parts['template'],
               context=email_parts['context'])

    logger.info("Sending admin reminder also")
    admin_parts = build_reminder_email(appointment, first_name, reschedule_link, 'admin', site_url=site_url)
    notify_admin(subject=admin_parts['subject'], template_url=admin_parts['template'], context=admin_parts['context'])


def send_email_task(recipient_list, subject, message, html_message, from_email, attachments=None):
    try:
        # Tasks queued before the text part existed carry an empty or missing message; derive it from the HTML
        if html_message and not message:
            message = html_to_text(html_message)
        send_email_now(recipient_list, subject, message or "", html_message, from_email, attachments)
    except Exception as e:
        logger.error(f"Error sending email from task: {e}")


def notify_admin_task(subject, message, html_message):
    """
    Task function to send an admin email asynchronously.
    """
    try:
        from django.core.mail import mail_admins
        logger.info(f"Sending admin email with subject: {subject}")
        mail_admins(subject=subject, message=message, html_message=html_message, fail_silently=False)
    except Exception as e:
        logger.error(f"Error sending admin email from task: {e}")


def cleanup_old_appointment_requests():
    """
    Clean up AppointmentRequest objects that are not associated with any appointments
    and are older than the specified period (APPOINTMENT_CLEANUP_DAYS).
    
    This task should be scheduled to run periodically using Django-Q.
    """
    try:
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=APPOINTMENT_CLEANUP_DAYS)

        # Find AppointmentRequests that:
        # 1. Don't have an associated Appointment (using the reverse OneToOne relationship)
        # 2. Were created before the cutoff date
        old_unassociated_requests = AppointmentRequest.objects.filter(
            created_at__lt=cutoff_date,
            appointment__isnull=True  # Only those without an associated Appointment
        )

        # Count before deletion for logging
        count = old_unassociated_requests.count()

        if count > 0:
            # Delete the old unassociated appointment requests
            # not `_`: this module imports gettext as _ (issue #455)
            deleted_count = old_unassociated_requests.delete()[0]
            logger.info(
                f"Cleaned up {deleted_count} old unassociated AppointmentRequest(s) "
                f"older than {APPOINTMENT_CLEANUP_DAYS} days"
            )
        else:
            logger.debug(
                f"No old unassociated AppointmentRequest(s) found to clean up "
                f"(older than {APPOINTMENT_CLEANUP_DAYS} days)"
            )

        return {
            'deleted_count': count,
            'cutoff_date': cutoff_date.isoformat(),
            'cleanup_days': APPOINTMENT_CLEANUP_DAYS
        }
    except Exception as e:
        logger.error(f"Error during cleanup of old appointment requests: {e}", exc_info=True)
        raise
