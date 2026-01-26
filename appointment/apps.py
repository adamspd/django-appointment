# apps.py
# Path: appointment/apps.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from django.apps import AppConfig
from django.conf import settings

from appointment.logger_config import get_logger

logger = get_logger(__name__)


class AppointmentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "appointment"

    def ready(self):
        """
        Schedule the cleanup task when the app is ready.
        This method is called when Django starts up.
        """
        # Only schedule if Django-Q is available
        if 'django_q' in settings.INSTALLED_APPS:
            try:
                from django_q.models import Schedule
                from django_q.tasks import schedule as schedule_task

                # Check if the schedule already exists to avoid duplicates
                schedule_name = 'cleanup_old_appointment_requests'
                if not Schedule.objects.filter(name=schedule_name).exists():
                    schedule_task(
                        'appointment.tasks.cleanup_old_appointment_requests',
                        name=schedule_name,
                        schedule_type=Schedule.DAILY,  # Run daily
                        repeats=-1,  # Repeat indefinitely
                    )
                    logger.info(
                        f"Scheduled daily cleanup task for old appointment requests "
                        f"(older than {getattr(settings, 'APPOINTMENT_CLEANUP_DAYS', 7)} days)"
                    )
                else:
                    logger.debug(f"Cleanup task schedule '{schedule_name}' already exists")
            except ImportError:
                logger.warning(
                    "Django-Q is in INSTALLED_APPS but not properly installed. "
                    "Cleanup task will not be scheduled."
                )
            except Exception as e:
                logger.error(f"Error scheduling cleanup task: {e}", exc_info=True)
