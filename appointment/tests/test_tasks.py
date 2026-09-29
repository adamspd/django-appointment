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

        # The client gets their own context, addressed to them
        mock_send_email.assert_called_once()
        kwargs = mock_send_email.call_args[1]
        self.assertEqual(kwargs['recipient_list'], [to_email])
        self.assertEqual(kwargs['subject'], _("Reminder: Upcoming Appointment"))
        self.assertEqual(kwargs['template_url'], 'email_sender/reminder_email.html')
        client_context = kwargs['context']
        self.assertEqual(client_context['recipient_type'], 'client')
        self.assertEqual(client_context['first_name'], first_name)
        self.assertEqual(client_context['appointment'], appointment)
        self.assertEqual(client_context['service'], appointment.get_service())
        self.assertIn('company', client_context)
        self.assertIn(f'/{appointment.id}/', client_context['appointment_url'])

        # The admin copy isn't addressed to the client
        mock_notify_admin.assert_called_once()
        kwargs = mock_notify_admin.call_args[1]
        self.assertEqual(kwargs['subject'], _("Admin Reminder: Upcoming Appointment"))
        admin_context = kwargs['context']
        self.assertEqual(admin_context['recipient_type'], 'admin')
        self.assertEqual(admin_context['first_name'], '')
        self.assertEqual(admin_context['client_first_name'], first_name)
        self.assertEqual(admin_context['appointment'], appointment)
