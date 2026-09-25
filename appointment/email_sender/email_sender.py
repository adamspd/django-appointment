# email_sender.py
# Path: appointment/email_sender/email_sender.py

import os
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from typing import Optional, Tuple, Union

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist, loader
from django.utils import timezone

from appointment.logger_config import get_logger
from appointment.settings import APP_DEFAULT_FROM_EMAIL, check_q_cluster, initialize_django_q

logger = get_logger(__name__)

# These helpers accept either a datetime or an ISO-8601 string, which they parse.
DateTimeInput = Union[datetime, str]

DJANGO_Q_AVAILABLE, async_task, schedule, Schedule = initialize_django_q()


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


def render_email_template(template_url, context, request=None):
    if template_url:
        return loader.render_to_string(template_url, context, request=request)
    return ""


class _TextExtractor(HTMLParser):
    """Collect the visible text of an HTML document, skipping what isn't body text (<head>, <style>, <script>)."""
    skipped_tags = {'head', 'style', 'script'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skipped_tags:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.skipped_tags and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(html_message: str) -> str:
    """Turn an HTML email into a readable plain-text body: no tags, no runs of blank lines."""
    extractor = _TextExtractor()
    extractor.feed(html_message)
    extractor.close()
    text = ''.join(extractor.parts)
    lines = [line.strip() for line in text.splitlines()]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()


def render_text_body(template_url, context, html_message, request=None) -> str:
    """Plain-text part of a templated email.

    A ``.txt`` template next to the HTML one (``emails/thank_you.txt`` for ``emails/thank_you.html``) is used when it
    exists; otherwise the text is derived from the HTML, so the email is never sent with an empty text part.
    """
    if template_url.endswith('.html'):
        try:
            return loader.render_to_string(template_url[:-len('.html')] + '.txt', context, request=request)
        except TemplateDoesNotExist:
            pass
    return html_to_text(html_message)


def send_email_now(recipient_list, subject, message, html_message, from_email, attachments=None):
    """Send an email synchronously, with its text part, optional HTML alternative and attachments."""
    email = EmailMultiAlternatives(subject=subject, body=message, from_email=from_email, to=recipient_list)
    if html_message:
        email.attach_alternative(html_message, "text/html")
    for attachment in attachments or []:
        email.attach(*attachment)
    email.send(fail_silently=False)


def send_email(recipient_list, subject: str, template_url: str = "", context: Optional[dict] = None,
               from_email=None, message: str = "", attachments=None, request=None):
    if context is None:
        context = {}
    if not has_required_email_settings():
        return

    from_email = from_email or APP_DEFAULT_FROM_EMAIL
    html_message = render_email_template(template_url, context, request)
    if template_url:
        message = render_text_body(template_url, context, html_message, request)

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
            send_email_now(recipient_list, subject, message, html_message, from_email, attachments)
        except Exception as e:
            logger.error(f"Error sending email: {e}")


def validate_required_fields(recipient_list: list, subject: str) -> Tuple[bool, str]:
    if not recipient_list or not subject:
        return False, "Recipient list and subject are required."
    return True, ""


def validate_and_process_datetime(dt: Optional[DateTimeInput], field_name: str) -> Tuple[bool, str, Optional[datetime]]:
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


def validate_send_at(send_at: Optional[DateTimeInput]) -> Tuple[bool, str, Optional[datetime]]:
    success, message, processed_send_at = validate_and_process_datetime(send_at, "send_at")
    if not success:
        return success, message, None

    if processed_send_at and processed_send_at <= timezone.now():
        return False, "send_at must be in the future.", None

    return True, "", processed_send_at or (timezone.now() + timedelta(minutes=1))


def validate_repeat_until(repeat_until: Optional[DateTimeInput], send_at: datetime) -> Tuple[
    bool, str, Optional[datetime]]:
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
        from_email: Optional[str],
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
        template_url: str = "",
        context: Optional[dict] = None,
        from_email: Optional[str] = None,
        attachments: Optional[list] = None,
        send_at: Optional[DateTimeInput] = None,
        name: Optional[str] = None,
        repeat: Optional[str] = None,
        repeat_until: Optional[DateTimeInput] = None,
        request=None
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
    if processed_send_at is None:
        # validate_send_at always resolves a datetime when it succeeds; this guards that invariant
        # rather than letting a None reach validate_repeat_until and schedule_email_task below.
        return False, "Could not resolve send_at."

    # Validate repeat option
    success, message, validated_repeat = validate_repeat_option(repeat)
    if not success:
        return success, message

    # Validate repeat_until
    success, message, processed_repeat_until = validate_repeat_until(repeat_until, processed_send_at)
    if not success:
        return success, message

    from_email = from_email or APP_DEFAULT_FROM_EMAIL
    html_message = render_email_template(template_url, context, request)

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


def notify_admin(subject: str, template_url: str = "", context: Optional[dict] = None, message: str = "",
                 recipient_email: str = "", attachments=None, request=None):
    """Email the admins using either a template by providing its URL or using a custom message.

    :param subject: The subject of the email.
    :param template_url: The URL of the template to use for the email content.
    :param context: The context to pass to the template.
    :param message: The message of the email.
    :param recipient_email: The email address of the recipient.
    :param attachments: A list of attachments to include in the email.
    :param request: The HTTP request object.
    """
    if context is None:
        context = {}
    if not has_required_email_settings():
        return

    html_message = render_email_template(template_url, context, request)
    if template_url:
        message = render_text_body(template_url, context, html_message, request)

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
            send_email_now(recipients, subject, message, html_message, settings.DEFAULT_FROM_EMAIL, attachments)
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
