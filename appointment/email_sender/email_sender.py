from django.core.mail import mail_admins, send_mail
from django.template import loader
from django.conf import settings

from appointment.settings import APP_DEFAULT_FROM_EMAIL


def has_required_email_settings():
    required_settings = [
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'EMAIL_USE_TLS',
        'EMAIL_USE_LOCALTIME',
        'ADMINS',
    ]

    for setting_name in required_settings:
        if not hasattr(settings, setting_name):
            print(f"Warning: '{setting_name}' not found in settings. Email functionality will be disabled.")
            return False

    return True

def send_email(recipient_list, subject: str, template_url: str = None, context: dict = None, from_email=None,
               message: str = None):
    if not has_required_email_settings():
        return

    if from_email is None:
        from_email = APP_DEFAULT_FROM_EMAIL

    html_message = ""

    if template_url:
        html_message = loader.render_to_string(
            template_name=template_url,
            context=context
        )

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
        print(f"Error sending email: {e}")

def notify_admin(subject: str, template_url: str = None, context: dict = None, message: str = None):
    if not has_required_email_settings():
        return

    html_message = ""
    if template_url:
        html_message = loader.render_to_string(
            template_name=template_url,
            context=context
        )
    try:
        mail_admins(
            subject=subject,
            message=message if not template_url else "",
            html_message=html_message if template_url else None
        )
    except Exception as e:
        print(f"Error sending email to admin: {e}")
