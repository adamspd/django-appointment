# settings.py
# Path: appointment/settings.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from django.conf import settings
from django.conf.global_settings import DEFAULT_FROM_EMAIL

from appointment.logger_config import logger

APPOINTMENT_BASE_TEMPLATE = getattr(settings, 'APPOINTMENT_BASE_TEMPLATE', 'base_templates/base.html')
APPOINTMENT_ADMIN_BASE_TEMPLATE = getattr(settings, 'APPOINTMENT_ADMIN_BASE_TEMPLATE', 'base_templates/base.html')
APPOINTMENT_WEBSITE_NAME = getattr(settings, 'APPOINTMENT_WEBSITE_NAME', 'Website')
APPOINTMENT_PAYMENT_URL = getattr(settings, 'APPOINTMENT_PAYMENT_URL', None)
APPOINTMENT_THANK_YOU_URL = getattr(settings, 'APPOINTMENT_THANK_YOU_URL', None)
APPOINTMENT_SLOT_DURATION = getattr(settings, 'APPOINTMENT_SLOT_DURATION', 30)
APPOINTMENT_BUFFER_TIME = getattr(settings, 'APPOINTMENT_BUFFER_TIME', 0)
APPOINTMENT_LEAD_TIME = getattr(settings, 'APPOINTMENT_LEAD_TIME', (9, 0))
APPOINTMENT_FINISH_TIME = getattr(settings, 'APPOINTMENT_FINISH_TIME', (18, 30))
APP_DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)


def check_q_cluster():
    """
    Checks if Django Q is properly installed and configured in the Django settings.
    If 'django_q' is not in INSTALLED_APPS, it warns about both 'django_q' not being installed
    and 'Q_CLUSTER' likely not being configured.
    If 'django_q' is installed but 'Q_CLUSTER' is not configured, it only warns about 'Q_CLUSTER'.
    Returns True if configurations are correct, otherwise False.
    """
    missing_conf = []

    # Check if Django Q is installed
    if 'django_q' not in settings.INSTALLED_APPS:
        missing_conf.append("Django Q is not in settings.INSTALLED_APPS. Please add it to the list.\n"
                            "Example: \n\n"
                            "INSTALLED_APPS = [\n"
                            "    ...\n"
                            "    'appointment',\n"
                            "    'django_q',\n"
                            "]\n")

    # Check if Q_CLUSTER configuration is defined
    if not hasattr(settings, 'Q_CLUSTER'):
        missing_conf.append("Q_CLUSTER is not defined in settings. Please define it.\n"
                            "Example: \n\n"
                            "Q_CLUSTER = {\n"
                            "    'name': 'DjangORM',\n"
                            "    'workers': 4,\n"
                            "    'timeout': 90,\n"
                            "    'retry': 120,\n"
                            "    'queue_limit': 50,\n"
                            "    'bulk': 10,\n"
                            "    'orm': 'default',\n"
                            "}\n"
                            "Then run 'python manage.py qcluster' to start the worker.\n"
                            "See https://django-q.readthedocs.io/en/latest/configure.html for more information.")

    # Log warnings if any configurations are missing
    if missing_conf:
        for warning in missing_conf:
            logger.warning(warning)
        return False
    print(f"Missing conf: {missing_conf}")
    # Both 'django_q' is installed and 'Q_CLUSTER' is configured
    return True
