# test_tasks.py
# Path: appointment/tests/test_tasks.py

from unittest.mock import patch

from django.utils.translation import gettext as _

from appointment.tasks import send_email_reminder
from appointment.tests.base.base_test import BaseTest


class SendEmailReminderTest(BaseTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    @patch('appointment.tasks.send_email')
    @patch('appointment.tasks.notify_admin')
    def test_send_email_reminder(self, mock_notify_admin, mock_send_email):
        # Use BaseTest setup to create an appointment
        appointment_request = self.create_appt_request_for_sm1()
        appointment = self.create_appt_for_sm1(appointment_request=appointment_request)

        # Extract necessary data for the test
        to_email = appointment.client.email
        first_name = appointment.client.first_name
        appointment_id = appointment.id

        # Call the function under test
        send_email_reminder(to_email, first_name, "", appointment_id)

        # Verify send_email was called with correct parameters
        mock_send_email.assert_called_once_with(
            recipient_list=[to_email],
            subject=_("Reminder: Upcoming Appointment"),
            template_url='email_sender/reminder_email.html',
            context={'first_name': first_name, 'appointment': appointment, 'reschedule_link': "",
                     'recipient_type': 'admin'}
        )

        # Verify notify_admin was called with correct parameters
        mock_notify_admin.assert_called_once_with(
            subject=_("Admin Reminder: Upcoming Appointment"),
            template_url='email_sender/reminder_email.html',
            context={'first_name': first_name, 'appointment': appointment, 'reschedule_link': "",
                     'recipient_type': 'admin'}
        )
