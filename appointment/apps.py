# apps.py
# Path: appointment/apps.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

from appointment.logger_config import get_logger
from appointment.settings import initialize_django_q

logger = get_logger(__name__)


def schedule_cleanup_task(**kwargs):
    """Register the daily cleanup task with Django-Q.

    Connected to post_migrate rather than called from ready(): ready() runs before migrations have
    been applied, so querying django_q_schedule there fails with "no such table" on a fresh database
    and on every test run.
    """
    # Initialize Django-Q and get the necessary parts
    django_q_available, _, schedule_task, schedule_model = initialize_django_q()

    # Only schedule if Django-Q is available
    if not django_q_available:
        return

    try:
        # Check if the schedule already exists to avoid duplicates
        schedule_name = 'cleanup_old_appointment_requests'
        if not schedule_model.objects.filter(name=schedule_name).exists():
            schedule_task(
                'appointment.tasks.cleanup_old_appointment_requests',
                name=schedule_name,
                schedule_type=schedule_model.DAILY,  # Run daily
                repeats=-1,  # Repeat indefinitely
            )
            logger.info(
                f"Scheduled daily cleanup task for old appointment requests "
                f"(older than {getattr(settings, 'APPOINTMENT_CLEANUP_DAYS', 7)} days)"
            )
        else:
            logger.debug(f"Cleanup task schedule '{schedule_name}' already exists")
    except Exception as e:
        logger.error(f"Error scheduling cleanup task: {e}", exc_info=True)


class AppointmentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "appointment"

    def ready(self):
        """
        Schedule the cleanup task once this app's migrations have run.
        This method is called when Django starts up.
        """
        post_migrate.connect(schedule_cleanup_task, sender=self)
