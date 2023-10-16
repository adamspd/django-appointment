import datetime
import json
from datetime import date, timedelta, time

from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext as _

from appointment.models import AppointmentRequest, Appointment, EmailVerificationCode
from appointment.tests.base.base_test import BaseTest
from appointment.utils.db_helpers import WorkingHours
from appointment.views import verify_user_and_login


class ViewsTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.factory = RequestFactory()
        self.staff_member = self.staff_member1
        WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=0,
                                    start_time=datetime.time(8, 0), end_time=datetime.time(12, 0))
        WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=2,
                                    start_time=datetime.time(8, 0), end_time=datetime.time(12, 0))
        self.ar = self.create_appt_request_for_sm1()
        self.request = self.factory.get('/')
        self.request.user = self.user1
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()

        middleware = MessageMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()

    def test_get_available_slots_ajax(self):
        """get_available_slots_ajax view should return a JSON response with available slots for the selected date."""
        url = reverse('appointment:available_slots_ajax')
        response = self.client.get(url, {'selected_date': date.today().isoformat()},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('date_chosen', response_data)
        self.assertIn('available_slots', response_data)
        self.assertFalse(response_data.get('error'))

    def test_get_available_slots_ajax_past_date(self):
        """get_available_slots_ajax view should return an error if the selected date is in the past."""
        url = reverse('appointment:available_slots_ajax')
        past_date = (date.today() - timedelta(days=1)).isoformat()
        response = self.client.get(url, {'selected_date': past_date}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['error'], True)
        self.assertEqual(response.json()['message'], 'Date is in the past')

    def test_get_next_available_date_ajax(self):
        """get_next_available_date_ajax view should return a JSON response with the next available date."""
        data = {'staff_id': self.staff_member.id}
        url = reverse('appointment:request_next_available_slot', args=[self.service1.id])
        response = self.client.get(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data)
        self.assertIsNotNone(response_data['next_available_date'])

    def test_appointment_request(self):
        """Test if the appointment request form can be rendered."""
        url = reverse('appointment:appointment_request', args=[self.service1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.service1.name, str(response.content))
        self.assertIn('all_staff_members', response.context)
        self.assertIn('service', response.context)

    def test_appointment_request_submit_valid(self):
        """Test if a valid appointment request can be submitted."""
        url = reverse('appointment:appointment_request_submit')
        post_data = {
            'date': date.today().isoformat(),
            'start_time': time(9, 0),
            'end_time': time(10, 0),
            'service': self.service1.id,
            'staff_member': self.staff_member.id,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)  # Redirect status
        # Check if an AppointmentRequest object was created
        self.assertTrue(AppointmentRequest.objects.filter(service=self.service1).exists())

    def test_appointment_request_submit_invalid(self):
        """Test if an invalid appointment request can be submitted."""
        url = reverse('appointment:appointment_request_submit')
        post_data = {}  # Missing required data
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)  # Rendering the form with errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)  # Ensure there are form errors

    def test_verify_user_and_login_valid(self):
        """Test if a user can be verified and logged in."""
        code = EmailVerificationCode.generate_code(user=self.user1)
        result = verify_user_and_login(self.request, self.user1, code)
        self.assertTrue(result)

    def test_verify_user_and_login_invalid(self):
        """Test if a user cannot be verified and logged in with an invalid code."""
        invalid_code = '000000'  # An invalid code
        result = verify_user_and_login(self.request, self.user1, invalid_code)
        self.assertFalse(result)

    def test_enter_verification_code_valid(self):
        """Test if a valid verification code can be entered."""
        code = EmailVerificationCode.generate_code(user=self.user1)
        url = reverse('appointment:enter_verification_code', args=[self.ar.id, self.ar.id_request])
        post_data = {'code': code}  # Assuming a valid code for the test setup
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_enter_verification_code_invalid(self):
        """Test if an invalid verification code can be entered."""
        url = reverse('appointment:enter_verification_code', args=[self.ar.id, self.ar.id_request])
        post_data = {'code': '000000'}  # Invalid code
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)  # Stay on the same page
        # Check for an error message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertIn(_("Invalid verification code."), [str(msg) for msg in messages_list])

    def test_default_thank_you(self):
        """Test if the default thank you page can be rendered."""
        appointment = Appointment.objects.create(client=self.user1, appointment_request=self.ar)
        url = reverse('appointment:default_thank_you', args=[appointment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(appointment.get_service_name(), str(response.content))
