# utils/template_helpers.py

from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


def get_custom_template(template_name, default_template):
    """
    Look for the user's custom template first, fall back to default.

    :param template_name: Fixed name the user must use (e.g., 'password_reset.html')
    :param default_template: Our default template path
    :return: Template path to use
    """
    # Get user's custom directory from settings (default: 'custom')
    custom_dir = getattr(settings, 'APPOINTMENT_CUSTOM_TEMPLATE_DIR', 'custom')
    custom_template_path = f"{custom_dir}/{template_name}"

    try:
        get_template(custom_template_path)
        return custom_template_path
    except TemplateDoesNotExist:
        return default_template


def get_email_template(template_name, default_template):
    """
    Look for the user's custom email template first, fall back to default.

    :param template_name: Fixed name the user must use (e.g., 'password_reset.html')
    :param default_template: Our default email template path
    :return: Template path to use
    """
    # Get user's custom email directory from settings (default: 'emails')
    email_dir = getattr(settings, 'APPOINTMENT_CUSTOM_EMAIL_DIR', 'emails')
    custom_template_path = f"{email_dir}/{template_name}"

    try:
        get_template(custom_template_path)
        return custom_template_path
    except TemplateDoesNotExist:
        return default_template
