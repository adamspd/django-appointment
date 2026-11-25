# signals.py
# Path: appointment/signals.py

"""
Author: Adams Pierre David
Since: 3.16.0
"""

from django.dispatch import Signal

# Sent after a client's booking form creates an AppointmentRequest. Kwargs: appointment_request, request.
appointment_request_created = Signal()
