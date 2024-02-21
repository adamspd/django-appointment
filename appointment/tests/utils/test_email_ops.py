from unittest import mock
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import timezone
from django.utils.translation import gettext as _

from appointment.messages_ import thank_you_no_payment, thank_you_payment, thank_you_payment_plus_down
from appointment.models import AppointmentRescheduleHistory
from appointment.tests.base.base_test import BaseTest
from appointment.utils.email_ops import (
    get_thank_you_message, notify_admin_about_appointment, send_reschedule_confirmation_email, send_thank_you_email,
    send_verification_email
)


class GetThankYouMessageTests(TestCase):
    def test_thank_you_no_payment(self):
        with patch('appointment.utils.email_ops.APPOINTMENT_PAYMENT_URL', None):
            ar = MagicMock()
            message = get_thank_you_message(ar)
            self.assertIn(thank_you_no_payment, message)

    def test_thank_you_payment_plus_down(self):
        with patch('appointment.utils.email_ops.APPOINTMENT_PAYMENT_URL', "http://payment.url"):
            ar = MagicMock()
            ar.accepts_down_payment.return_value = True
            message = get_thank_you_message(ar)
            self.assertIn(thank_you_payment_plus_down, message)

    def test_thank_you_payment(self):
        with patch('appointment.utils.email_ops.APPOINTMENT_PAYMENT_URL', "http://payment.url"):
            ar = MagicMock()
            ar.accepts_down_payment.return_value = False
            message = get_thank_you_message(ar)
            self.assertIn(thank_you_payment, message)


class SendThankYouEmailTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    @patch('appointment.utils.email_ops.send_email')
    @patch('appointment.utils.email_ops.get_thank_you_message')
    def test_send_thank_you_email(self, mock_get_thank_you_message, mock_send_email):
        ar = self.create_appt_request_for_sm1()
        email = "test@example.com"
        appointment_details = "Details about the appointment"
        account_details = "Details about the account"

        mock_get_thank_you_message.return_value = "Thank you message"

        send_thank_you_email(ar, self.user1, self.request, email, appointment_details, account_details)

        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertIn(email, kwargs['recipient_list'])
        self.assertIn("Thank you message", kwargs['context']['message_1'])


class NotifyAdminAboutAppointmentTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = self.create_appointment_for_user1()

    @patch('appointment.utils.email_ops.notify_admin')
    @patch('appointment.utils.email_ops.send_email')
    def test_notify_admin_about_appointment(self, mock_send_email, mock_notify_admin):
        client_name = "John Doe"

        notify_admin_about_appointment(self.appointment, client_name)

        mock_notify_admin.assert_called_once()
        mock_send_email.assert_called_once()


class SendVerificationEmailTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = self.create_appointment_for_user1()

    @patch('appointment.utils.email_ops.send_email')
    @patch('appointment.models.EmailVerificationCode.generate_code', return_value="123456")
    def test_send_verification_email(self, mock_generate_code, mock_send_email):
        user = MagicMock()
        email = "test@example.com"

        send_verification_email(user, email)

        mock_send_email.assert_called_once_with(
            recipient_list=[email],
            subject=_("Email Verification"),
            message=mock.ANY
        )
        self.assertIn("123456", mock_send_email.call_args[1]['message'])


class SendRescheduleConfirmationEmailTests(BaseTest):
    def setUp(self):
        # Setup test data
        super().setUp()
        self.user = self.user1
        self.appointment_request = self.create_appt_request_for_sm1()
        self.reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.appointment_request,
            date=self.appointment_request.date + timezone.timedelta(days=1),
            start_time=self.appointment_request.start_time,
            end_time=self.appointment_request.end_time,
            staff_member=self.staff_member1,
            reason_for_rescheduling="Test reason"
        )
        self.first_name = "Test"
        self.email = "test@example.com"

    @mock.patch('appointment.utils.email_ops.get_absolute_url_')
    @mock.patch('appointment.utils.email_ops.send_email')
    def test_send_reschedule_confirmation_email(self, mock_send_email, mock_get_absolute_url):
        request = mock.MagicMock()
        mock_get_absolute_url.return_value = "http://testserver/confirmation_link"

        send_reschedule_confirmation_email(request, self.reschedule_history, self.appointment_request, self.first_name,
                                           self.email)

        # Check if `send_email` was called correctly
        mock_send_email.assert_called_once()
        call_args, call_kwargs = mock_send_email.call_args

        self.assertEqual(call_kwargs['recipient_list'], [self.email])
        self.assertEqual(call_kwargs['subject'], _("Confirm Your Appointment Rescheduling"))
        self.assertIn('reschedule_date', call_kwargs['context'])
        self.assertIn('confirmation_link', call_kwargs['context'])
        self.assertEqual(call_kwargs['context']['confirmation_link'], "http://testserver/confirmation_link")
