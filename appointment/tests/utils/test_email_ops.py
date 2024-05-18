from copy import deepcopy
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, patch

from django.test.client import RequestFactory
from django.utils import timezone
from django.utils.translation import gettext as _

from appointment.messages_ import thank_you_no_payment, thank_you_payment, thank_you_payment_plus_down
from appointment.models import AppointmentRescheduleHistory
from appointment.tests.base.base_test import BaseTest
from appointment.utils.email_ops import (
    get_thank_you_message, notify_admin_about_appointment, notify_admin_about_reschedule,
    send_reschedule_confirmation_email,
    send_reset_link_to_staff_member, send_thank_you_email,
    send_verification_email
)


class SendResetLinkToStaffMemberTests(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = deepcopy(self.users['staff1'])
        self.user.is_staff = True
        self.user.save()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.email = 'daniel.jackson@django-appointment.com'

    @mock.patch('appointment.utils.email_ops.send_email')
    @mock.patch('appointment.models.PasswordResetToken.create_token')
    @mock.patch('appointment.utils.email_ops.get_absolute_url_')
    @mock.patch('appointment.utils.email_ops.get_website_name')
    def test_send_reset_link(self, mock_get_website_name, mock_get_absolute_url, mock_create_token, mock_send_email):
        # Set up the token
        mock_token = mock.Mock()
        mock_token.token = "Colonel_Samantha_Carter_a_Tau_ri_Scientist"
        mock_create_token.return_value = mock_token

        mock_get_absolute_url.return_value = f"http://gateroomserver/reset_password/{mock_token.token}"
        mock_get_website_name.return_value = 'Gate Room Server'

        send_reset_link_to_staff_member(self.user, self.request, self.email)

        # Check send_email was called with correct parameters
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertEqual(kwargs['recipient_list'], [self.email])
        self.assertIn('Gate Room Server', kwargs['message'])
        self.assertIn('http://gateroomserver/reset_password', kwargs['message'])
        self.assertIn('Colonel_Samantha_Carter_a_Tau_ri_Scientist', kwargs['message'])

        # Additional assertions to verify more parts of the message content
        self.assertIn('Hello', kwargs['message'])
        self.assertIn(self.user.first_name, kwargs['message'])
        self.assertIn(str(datetime.now().year), kwargs['message'])
        self.assertIn('No additional details provided.', kwargs['message'])
        self.assertIn(self.user.username, kwargs['message'])


class GetThankYouMessageTests(BaseTest):

    def setUp(self):
        super().setUp()
        self.ar = MagicMock()

    def test_thank_you_no_payment(self):
        with patch('appointment.utils.email_ops.APPOINTMENT_PAYMENT_URL', None):
            message = get_thank_you_message(self.ar)
            self.assertIn(thank_you_no_payment, message)

    def test_thank_you_payment_plus_down(self):
        with patch('appointment.utils.email_ops.APPOINTMENT_PAYMENT_URL', "http://payment.url"):
            self.ar.accepts_down_payment.return_value = True
            message = get_thank_you_message(self.ar)
            self.assertIn(thank_you_payment_plus_down, message)

    def test_thank_you_payment(self):
        with patch('appointment.utils.email_ops.APPOINTMENT_PAYMENT_URL', "http://payment.url"):
            self.ar.accepts_down_payment.return_value = False
            message = get_thank_you_message(self.ar)
            self.assertIn(thank_you_payment, message)


class SendThankYouEmailTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.ar = self.create_appt_request_for_sm1()
        self.email = "georges.s.hammond@django-appointment.com"
        self.appointment_details = "Details about the appointment"
        self.account_details = "Details about the account"

    @patch('appointment.utils.email_ops.send_email')
    @patch('appointment.utils.email_ops.get_thank_you_message')
    def test_send_thank_you_email(self, mock_get_thank_you_message, mock_send_email):
        mock_get_thank_you_message.return_value = "Thank you message"

        send_thank_you_email(self.ar, self.users['client1'], self.request, self.email, self.appointment_details,
                             self.account_details)

        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertIn(self.email, kwargs['recipient_list'])
        self.assertIn("Thank you message", kwargs['context']['message_1'])


class NotifyAdminAboutAppointmentTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = self.create_appt_for_sm1()
        self.client_name = "Oma Desala"

    @patch('appointment.utils.email_ops.notify_admin')
    @patch('appointment.utils.email_ops.send_email')
    def test_notify_admin_about_appointment(self, mock_send_email, mock_notify_admin):
        notify_admin_about_appointment(self.appointment, self.client_name)
        mock_notify_admin.assert_called_once()
        mock_send_email.assert_called_once()


class SendVerificationEmailTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = self.create_appt_for_sm1()
        self.email = "richard.woolsey@django-appointment.com"

    @patch('appointment.utils.email_ops.send_email')
    @patch('appointment.models.EmailVerificationCode.generate_code', return_value="123456")
    def test_send_verification_email(self, mock_generate_code, mock_send_email):
        user = MagicMock()

        send_verification_email(user, self.email)

        mock_send_email.assert_called_once_with(
                recipient_list=[self.email],
                subject=_("Email Verification"),
                message=mock.ANY
        )
        self.assertIn("123456", mock_send_email.call_args[1]['message'])


class SendRescheduleConfirmationEmailTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment_request = self.create_appt_request_for_sm1()
        self.reschedule_history = AppointmentRescheduleHistory.objects.create(
                appointment_request=self.appointment_request,
                date=self.appointment_request.date + timezone.timedelta(days=1),
                start_time=self.appointment_request.start_time,
                end_time=self.appointment_request.end_time,
                staff_member=self.staff_member1,
                reason_for_rescheduling="Had to reschedule because I got stuck in a time loop. Again"
        )
        self.first_name = "Jack"
        self.email = "jack.oneill@django-appointment.com"

    @mock.patch('appointment.utils.email_ops.get_absolute_url_')
    @mock.patch('appointment.utils.email_ops.send_email')
    def test_send_reschedule_confirmation_email(self, mock_send_email, mock_get_absolute_url):
        request = mock.MagicMock()
        mock_get_absolute_url.return_value = "http://gateroomserver/confirmation_link"

        send_reschedule_confirmation_email(request, self.reschedule_history, self.appointment_request, self.first_name,
                                           self.email)

        # Check if `send_email` was called correctly
        mock_send_email.assert_called_once()
        call_args, call_kwargs = mock_send_email.call_args

        self.assertEqual(call_kwargs['recipient_list'], [self.email])
        self.assertEqual(call_kwargs['subject'], _("Confirm Your Appointment Rescheduling"))
        self.assertIn('reschedule_date', call_kwargs['context'])
        self.assertIn('confirmation_link', call_kwargs['context'])
        self.assertEqual(call_kwargs['context']['confirmation_link'], "http://gateroomserver/confirmation_link")


class NotifyAdminAboutRescheduleTests(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.appointment_request = self.create_appt_request_for_sm1()
        self.reschedule_history = AppointmentRescheduleHistory.objects.create(
                appointment_request=self.appointment_request,
                date=self.appointment_request.date + timezone.timedelta(days=1),
                start_time=self.appointment_request.start_time,
                end_time=self.appointment_request.end_time,
                staff_member=self.staff_member1,
                reason_for_rescheduling="Captured by Anubis"
        )
        self.client_name = "Jonas Quinn"

    @patch('appointment.utils.email_ops.notify_admin')
    @patch('appointment.utils.email_ops.send_email')
    @patch('appointment.utils.email_ops.get_website_name', return_value="Stargate Command")
    @patch('appointment.utils.email_ops.convert_24_hour_time_to_12_hour_time',
           side_effect=lambda x: x.strftime("%I:%M %p"))
    def test_notify_admin_about_reschedule(self, mock_convert_time, mock_get_website_name, mock_send_email,
                                           mock_notify_admin):
        notify_admin_about_reschedule(self.reschedule_history, self.appointment_request, self.client_name)

        # Check if notify_admin was called correctly
        mock_notify_admin.assert_called_once()
        notify_admin_args, notify_admin_kwargs = mock_notify_admin.call_args
        self.assertIn(self.client_name, notify_admin_kwargs['subject'])
        self.assertEqual(notify_admin_kwargs['context']['client_name'], self.client_name)
        self.assertEqual(notify_admin_kwargs['context']['service_name'], self.appointment_request.service.name)
        self.assertEqual(notify_admin_kwargs['context']['reason_for_rescheduling'],
                         self.reschedule_history.reason_for_rescheduling)
        self.assertEqual(notify_admin_kwargs['context']['old_date'],
                         self.appointment_request.date.strftime("%A, %d %B %Y"))
        self.assertEqual(notify_admin_kwargs['context']['reschedule_date'],
                         self.reschedule_history.date.strftime("%A, %d %B %Y"))
        self.assertEqual(notify_admin_kwargs['context']['company'], "Stargate Command")
