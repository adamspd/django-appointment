# apps.py
# Path: appointment/apps.py

"""
Author: Adams Pierre David
Version: 2.0.0
Since: 1.0.0
"""

from django.apps import AppConfig


class AppointmentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "appointment"
