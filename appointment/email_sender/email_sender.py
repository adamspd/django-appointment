# email_sender.py
# Path: appointment/email_sender/email_sender.py
import os

from django.core.mail import mail_admins, send_mail
from django.template import loader

from appointment.logger_config import get_logger
from appointment.settings import APP_DEFAULT_FROM_EMAIL, check_q_cluster

logger = get_logger(__name__)

try:
    from django_q.tasks import async_task

    DJANGO_Q_AVAILABLE = True
except ImportError:
    async_task = None
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
               message: str = None):
    if not has_required_email_settings():
        return

    from_email = from_email or APP_DEFAULT_FROM_EMAIL
    html_message = render_email_template(template_url, context)

    if get_use_django_q_for_emails() and check_q_cluster() and DJANGO_Q_AVAILABLE:
        # Asynchronously send the email using Django-Q
        async_task(
                "appointment.tasks.send_email_task", recipient_list=recipient_list, subject=subject,
                message=message, html_message=html_message if template_url else None, from_email=from_email
        )
    else:
        # Synchronously send the email
        try:
            send_mail(
                    subject=subject, message=message if not template_url else "",
                    html_message=html_message if template_url else None, from_email=from_email,
                    recipient_list=recipient_list, fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")


def notify_admin(subject: str, template_url: str = None, context: dict = None, message: str = None):
    if not has_required_email_settings():
        return

    html_message = render_email_template(template_url, context)

    if get_use_django_q_for_emails() and check_q_cluster() and DJANGO_Q_AVAILABLE:
        # Enqueue the task to send admin email asynchronously
        async_task('appointment.tasks.notify_admin_task', subject=subject, message=message, html_message=html_message)
    else:
        # Synchronously send admin email
        try:
            mail_admins(
                    subject=subject, message=message if not template_url else "",
                    html_message=html_message if template_url else None
            )
        except Exception as e:
            logger.error(f"Error sending email to admin: {e}")


def get_use_django_q_for_emails():
    """Get the value of the USE_DJANGO_Q_FOR_EMAILS setting."""
    try:
        from django.conf import settings
        return getattr(settings, 'USE_DJANGO_Q_FOR_EMAILS', False)
    except AttributeError:
        logger.error("Error accessing USE_DJANGO_Q_FOR_EMAILS. Defaulting to False.")
        return False
