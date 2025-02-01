# email_sender.py
# Path: appointment/email_sender/email_sender.py
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from appointment.logger_config import get_logger
from appointment.settings import APP_DEFAULT_FROM_EMAIL, check_q_cluster

logger = get_logger(__name__)

try:
    from django_q.tasks import async_task, schedule
    from django_q.models import Schedule


    DJANGO_Q_AVAILABLE = True
except ImportError:
    async_task = None
    schedule = None
    Schedule = None

    DJANGO_Q_AVAILABLE = False
    logger.warning("django-q is not installed. Email will be sent synchronously.")


def has_required_email_settings():
    """Check if all required email settings are configured and warn if any are missing."""
    from django.conf import settings as s
    required_settings = [
        'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'EMAIL_USE_TLS'
    ]
    missing_settings = [
        setting_name for setting_name in required_settings if not hasattr(s, setting_name)
    ]

    if missing_settings:
        missing_settings_str = ", ".join(missing_settings)
        logger.warning(f"Warning: The following settings are missing in settings.py: {missing_settings_str}. "
                       "Email functionality will be disabled.")
        return False

    # Check if EMAIL_HOST is not the default value
    if os.environ.get('EMAIL_HOST') == 'smtp.example.com':
        logger.warning(
                "EMAIL_HOST is set to the default value 'smtp.example.com'. "
                "Please update it with your actual SMTP server in the .env file."
        )
        return False
    return True


def render_email_template(template_url, context):
    if template_url:
        return loader.render_to_string(template_url, context)
    return ""


def send_email(recipient_list, subject: str, template_url: str = None, context: dict = None, from_email=None,
               message: str = None, attachments=None):
    if not has_required_email_settings():
        return

    from_email = from_email or APP_DEFAULT_FROM_EMAIL
    html_message = render_email_template(template_url, context)

    if get_use_django_q_for_emails() and check_q_cluster() and DJANGO_Q_AVAILABLE:
        # Pass only the necessary data to construct the email
        async_task(
                'appointment.tasks.send_email_task',
                recipient_list=recipient_list,
                subject=subject,
                message=message,
                html_message=html_message,
                from_email=from_email,
                attachments=attachments
        )
    else:
        # Synchronously send the email
        try:
            send_mail(
                    subject=subject,
                    message=message if not template_url else "",
                    html_message=html_message if template_url else None,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")


def validate_required_fields(recipient_list: list, subject: str) -> Tuple[bool, str]:
    if not recipient_list or not subject:
        return False, "Recipient list and subject are required."
    return True, ""


def validate_and_process_datetime(dt: Optional[datetime], field_name: str) -> Tuple[bool, str, Optional[datetime]]:
    if not dt:
        return True, "", None

    if not isinstance(dt, datetime):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return False, f"Invalid {field_name} format. Use ISO format or datetime object.", None

    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)

    return True, "", dt


def validate_send_at(send_at: Optional[datetime]) -> tuple[bool, str, None] | tuple[
    bool, str, datetime | None | timedelta | Any]:
    success, message, processed_send_at = validate_and_process_datetime(send_at, "send_at")
    if not success:
        return success, message, None

    if processed_send_at and processed_send_at <= timezone.now():
        return False, "send_at must be in the future.", None

    return True, "", processed_send_at or (timezone.now() + timedelta(minutes=1))


def validate_repeat_until(repeat_until: Optional[datetime], send_at: datetime) -> Tuple[bool, str, Optional[datetime]]:
    success, message, processed_repeat_until = validate_and_process_datetime(repeat_until, "repeat_until")
    if not success:
        return success, message, None

    if processed_repeat_until and processed_repeat_until <= send_at:
        return False, "repeat_until must be after send_at.", None

    return True, "", processed_repeat_until


def validate_repeat_option(repeat: Optional[str]) -> Tuple[bool, str, Optional[str]]:
    valid_options = ['HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY']
    if repeat and repeat not in valid_options:
        return False, f"Invalid repeat option. Choose from {', '.join(valid_options)}.", None
    return True, "", repeat


def schedule_email_task(
        recipient_list: list,
        subject: str,
        html_message: str,
        from_email: str,
        attachments: Optional[list],
        schedule_type: str,
        send_at: datetime,
        name: Optional[str],
        repeat_until: Optional[datetime]
) -> Tuple[bool, str]:
    try:
        schedule(
                'appointment.tasks.send_email_task',
                recipient_list=recipient_list,
                subject=subject,
                message=None,
                html_message=html_message,
                from_email=from_email,
                attachments=attachments,
                schedule_type=schedule_type,
                next_run=send_at,
                name=name,
                repeats=-1 if schedule_type != Schedule.ONCE and not repeat_until else None,
                end_date=repeat_until
        )
        return True, "Email scheduled successfully."
    except Exception as e:
        logger.error(f"Error scheduling email: {e}")
        return False, f"Error scheduling email: {str(e)}"


def schedule_email_sending(
        recipient_list: list,
        subject: str,
        template_url: Optional[str] = None,
        context: Optional[dict] = None,
        from_email: Optional[str] = None,
        attachments: Optional[list] = None,
        send_at: Optional[datetime] = None,
        name: Optional[str] = None,
        repeat: Optional[str] = None,
        repeat_until: Optional[datetime] = None
) -> Tuple[bool, str]:
    if not has_required_email_settings():
        return False, "Email settings are not configured."

    if not check_q_cluster() or not DJANGO_Q_AVAILABLE:
        return False, "Django-Q is not available."

    # Validate required fields
    success, message = validate_required_fields(recipient_list, subject)
    if not success:
        return success, message

    # Validate and process send_at
    success, message, processed_send_at = validate_send_at(send_at)
    if not success:
        return success, message

    # Validate repeat option
    success, message, validated_repeat = validate_repeat_option(repeat)
    if not success:
        return success, message

    # Validate repeat_until
    success, message, processed_repeat_until = validate_repeat_until(repeat_until, processed_send_at)
    if not success:
        return success, message

    from_email = from_email or APP_DEFAULT_FROM_EMAIL
    html_message = render_email_template(template_url, context)

    schedule_type = getattr(Schedule, validated_repeat or 'ONCE')

    return schedule_email_task(
            recipient_list,
            subject,
            html_message,
            from_email,
            attachments,
            schedule_type,
            processed_send_at,
            name,
            processed_repeat_until
    )


def notify_admin(subject: str, template_url: str = None, context: dict = None, message: str = None,
                 recipient_email: str = None, attachments=None):
    if not has_required_email_settings():
        return

    html_message = render_email_template(template_url, context)

    recipients = [recipient_email] if recipient_email else [email for name, email in settings.ADMINS]

    if get_use_django_q_for_emails() and check_q_cluster() and DJANGO_Q_AVAILABLE:
        # Asynchronously send the email using Django-Q
        async_task("appointment.tasks.send_email_task",
                   subject=subject,
                   message=message,
                   html_message=html_message,
                   from_email=settings.DEFAULT_FROM_EMAIL,
                   recipient_list=recipients,
                   attachments=attachments)
    else:
        # Synchronously send the email
        try:
            send_mail(
                    subject=subject,
                    message=message if not template_url else "",
                    html_message=html_message if template_url else None,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")


def get_use_django_q_for_emails():
    """Get the value of the USE_DJANGO_Q_FOR_EMAILS setting."""
    try:
        from django.conf import settings
        return getattr(settings, 'USE_DJANGO_Q_FOR_EMAILS', False)
    except AttributeError:
        logger.error("Error accessing USE_DJANGO_Q_FOR_EMAILS. Defaulting to False.")
        return False
