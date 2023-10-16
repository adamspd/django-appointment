from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client
from django.test import override_settings
from django.test.client import RequestFactory

from appointment.tests.base.base_test import BaseTest
from appointment.utils.session import get_appointment_data_from_session, handle_email_change, handle_existing_email


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SessionTests(BaseTest):

    def setUp(self):
        super().setUp()
        self.ar = self.create_appt_request_for_sm1()
        self.client = Client()
        self.factory = RequestFactory()

        # Setup request object
        self.request = self.factory.post('/')
        self.request.user = self.user1

        # Setup session for the request
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()

        # Setup messages for the request
        middleware = MessageMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()

    def test_handle_existing_email(self):
        """Test if an existing email can be handled."""
        client_data = {
            'email': self.client1.email,
            'name': 'John Doe'
        }
        appointment_data = {
            'phone': '+1234567890',
            'want_reminder': True,
            'address': '123 Main St, City, Country',
            'additional_info': 'Some additional info'
        }

        response = handle_existing_email(self.request, client_data, appointment_data, self.ar.id, self.ar.id_request)

        # Assert session data
        session = self.request.session
        self.assertEqual(session['email'], client_data['email'])
        self.assertEqual(session['phone'], appointment_data['phone'])
        self.assertTrue(session['want_reminder'])
        self.assertEqual(session['address'], appointment_data['address'])
        self.assertEqual(session['additional_info'], appointment_data['additional_info'])

        # Assert redirect
        self.assertEqual(response.status_code, 302)

    def test_handle_email_change(self):
        """Test if an email change can be handled."""
        new_email = "new_email@example.com"

        response = handle_email_change(self.request, self.user1, new_email)

        # Assert session data
        session = self.request.session
        self.assertEqual(session['email'], new_email)
        self.assertEqual(session['old_email'], self.user1.email)

        # Assert redirect
        self.assertEqual(response.status_code, 302)

    def test_get_appointment_data_from_session(self):
        """Test if appointment data can be retrieved from the session."""
        # Populate session with test data
        session_data = {
            'phone': '+1234567890',
            'want_reminder': 'on',
            'address': '123 Main St, City, Country',
            'additional_info': 'Some additional info'
        }
        for key, value in session_data.items():
            self.request.session[key] = value
        self.request.session.save()

        # Retrieve data using the function
        appointment_data = get_appointment_data_from_session(self.request)
        self.assertEqual(str(appointment_data['phone']), session_data['phone'])
        self.assertTrue(appointment_data['want_reminder'])
        self.assertEqual(appointment_data['address'], session_data['address'])
        self.assertEqual(appointment_data['additional_info'], session_data['additional_info'])
