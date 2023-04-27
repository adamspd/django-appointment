from django.core.mail import mail_admins, send_mail
from django.template import loader


def send_email(recipient_list, subject: str, template_url: str = None, context: dict = None, from_email=None,
               message: str = None):
    if from_email is None:
        from_email = 'crueltouch.photo.web@gmail.com'

    html_message = ""

    if template_url:
        html_message = loader.render_to_string(
            template_name=template_url,
            context=context
        )

    send_mail(
        subject=subject,
        message=message if not template_url else "",
        html_message=html_message if template_url else None,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def notify_admin(subject: str, template_url: str = None, context: dict = None, message: str = None):
    html_message = ""
    if template_url:
        html_message = loader.render_to_string(
            template_name=template_url,
            context=context
        )
    mail_admins(
        subject=subject,
        message=message if not template_url else "",
        html_message=html_message if template_url else None
    )
