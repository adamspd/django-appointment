import json
from datetime import date, timedelta, time

from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.urls import reverse

from appointment.models import Service, AppointmentRequest, Appointment, EmailVerificationCode
from appointment.utils import Utility
from appointment.views import verify_user_and_login


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100)
        self.ar = AppointmentRequest.objects.create(date=date.today(), start_time=time(9, 0),
                                                    end_time=time(10, 0), service=self.service)
        self.user_model = Utility.get_user_model()
        self.user = self.user_model.objects.create_user(first_name="Tester",
                                                        email="testemail@gmail.com",
                                                        username="test_user", password="Kfdqi3!?n")
        self.request = self.factory.get('/')  # Create a GET request object
        self.request.user = self.user
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()

        middleware = MessageMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()

    def test_get_available_slots_ajax(self):
        url = reverse('appointment:available_slots_ajax')
        response = self.client.get(url, {'selected_date': date.today().isoformat()},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        # Add assertions to check the content of the response, e.g., available_slots, date_chosen, etc.

    def test_get_available_slots_ajax_past_date(self):
        url = reverse('appointment:available_slots_ajax')
        past_date = (date.today() - timedelta(days=1)).isoformat()
        response = self.client.get(url, {'selected_date': past_date}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['error'], True)
        self.assertEqual(response.json()['message'], 'Date is in the past')

    def test_get_next_available_date_ajax(self):
        response = self.client.get(reverse('appointment:request_next_available_slot', args=[self.service.id]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data)
        self.assertIsNotNone(response_data['next_available_date'])

    def test_appointment_request(self):
        url = reverse('appointment:appointment_request', args=[self.service.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Add assertions to check the content of the response, such as service details, available_slots, etc.

    def test_appointment_client_information_post(self):
        url = reverse('appointment:appointment_client_information', args=[self.ar.id, self.ar.id_request])
        post_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'want_reminder': 'on',
            'address': 'Address',
            'additional_info': 'Additional Info',
            'payment_type': 'full'
        }
        response = self.client.post(url, post_data)
        # Add assertions to check the redirection, creation of objects, etc.

    def test_appointment_request_submit_valid(self):
        url = reverse('appointment:appointment_request_submit')
        post_data = {
            'date': date.today().isoformat(),
            'start_time': time(9, 0),
            'end_time': time(10, 0),
            'service': self.service.id
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)  # Redirect status
        # Add assertions to check the creation of AppointmentRequest object and redirection URL

    def test_appointment_request_submit_invalid(self):
        url = reverse('appointment:appointment_request_submit')
        post_data = {}  # Missing required data
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)  # Rendering the form with errors
        # Add assertions to check for form errors

    def test_verify_user_and_login_valid(self):
        code = EmailVerificationCode.generate_code(user=self.user)
        result = verify_user_and_login(self.request, self.user, code)
        self.assertTrue(result)

    def test_verify_user_and_login_invalid(self):
        invalid_code = '000000'  # An invalid code
        result = verify_user_and_login(self.request, self.user, invalid_code)
        self.assertFalse(result)

    def test_enter_verification_code_valid(self):
        code = EmailVerificationCode.generate_code(user=self.user)
        url = reverse('appointment:enter_verification_code', args=[self.ar.id, self.ar.id_request])
        post_data = {'code': code}  # Assuming a valid code for the test setup
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        # Add assertions to check for successful email verification and redirection URL

    def test_enter_verification_code_invalid(self):
        url = reverse('appointment:enter_verification_code', args=[self.ar.id, self.ar.id_request])
        post_data = {'code': '000000'}  # Invalid code
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)  # Stay on the same page
        # Add assertions to check for an error message

    def test_default_thank_you(self):
        appointment = Appointment.objects.create(client=self.user, appointment_request=self.ar)
        url = reverse('appointment:default_thank_you', args=[appointment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Add assertions to check the content of the response, e.g., appointment details, email sent, etc.
