# utils/template_helpers.py

from django.conf import settings
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template

from appointment.logger_config import get_logger

logger = get_logger(__name__)


def _first_usable_template(directory, template_names, default_template):
    """
    Return the first template in ``template_names`` that exists in ``directory`` and compiles.

    A template that is missing is skipped silently; one that exists but fails to compile is
    skipped with a warning so a broken override never takes a page (or an email) down.

    :param directory: The directory the user puts their overrides in.
    :param template_names: A single name, or an iterable of accepted names tried in order.
    :param default_template: Our default template path, returned when no override is usable.
    :return: Template path to use.
    """
    if isinstance(template_names, str):
        template_names = (template_names,)

    for template_name in template_names:
        custom_template_path = f"{directory}/{template_name}"
        try:
            get_template(custom_template_path)
            return custom_template_path
        except TemplateDoesNotExist:
            continue
        except TemplateSyntaxError:
            logger.warning(
                    "Custom template override could not be compiled due to syntax error. "
                    "Falling back to default template."
            )
            continue
        except Exception:  # noqa: BLE001 - a broken override must never break the response
            logger.error(
                    "Unexpected error loading custom template override. "
                    "Falling back to default template.",
                    exc_info=True
            )
            continue

    return default_template


def get_custom_template(template_name, default_template):
    """
    Look for the user's custom template first, fall back to default.

    :param template_name: Fixed name the user must use (e.g., 'password_reset.html'), or an
                          iterable of accepted names tried in order.
    :param default_template: Our default "template path"
    :return: Template path to use
    """
    # Get user's custom directory from settings (default: 'custom')
    custom_dir = getattr(settings, 'APPOINTMENT_CUSTOM_TEMPLATES_DIR', 'custom')
    return _first_usable_template(custom_dir, template_name, default_template)


def get_email_template(template_name, default_template):
    """
    Look for the user's custom email template first, fall back to default.

    :param template_name: Fixed name the user must use (e.g., 'password_reset.html'), or an
                          iterable of accepted names tried in order.
    :param default_template: Our default email 'template path'
    :return: Template path to use
    """
    # Get user's custom email directory from settings (default: 'emails')
    email_dir = getattr(settings, 'APPOINTMENT_CUSTOM_EMAILS_DIR', 'emails')
    return _first_usable_template(email_dir, template_name, default_template)


_JSON_SCRIPT_ESCAPES = {
    ord('<'): '\\u003C',
    ord('>'): '\\u003E',
    ord('&'): '\\u0026',
}


def escape_json_for_script(json_string):
    """
    Make a JSON string safe to print inside a ``<script>`` tag with ``|safe``.

    ``<``, ``>`` and ``&`` become JSON unicode escapes, so a value such as ``</script>`` can't close
    the tag. The result is still valid JSON and parses to the same data.

    :param json_string: The output of ``json.dumps``.
    :return: The escaped JSON string.
    """
    return json_string.translate(_JSON_SCRIPT_ESCAPES)
