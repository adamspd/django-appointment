# test_json_context.py
# Path: appointment/tests/utils/test_json_context.py

import json

from django.test import RequestFactory

from appointment.tests.base.base_test import BaseTest
from appointment.utils.json_context import (
    convert_appointment_to_json, get_generic_context, get_generic_context_with_extra, handle_unauthorized_response,
    json_response
)


class ConvertAppointmentToJsonTests(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.appointments = [self.create_appt_for_sm1()]
        self.request = self.factory.get('/')
        self.request.user = self.users['client1']

    def test_convert_appointment_to_json(self):
        """Test if an appointment can be converted to JSON."""
        data = convert_appointment_to_json(self.request, self.appointments)
        self.assertIsInstance(data, list, "Data should be a list")
        self.assertEqual(len(data), 1, "Data list should have one appointment")
        self.assertIn("id", data[0], "Data should contain 'id' field")


class JsonResponseTests(BaseTest):
    def test_json_response(self):
        """Test if a JSON response can be created."""
        message = "Gate Room Under Attack"
        response = json_response(message=message)
        self.assertEqual(response.status_code, 200, "Response status should be 200")
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['message'], message, "Response content should match the message")


class GetGenericContextTests(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user1 = self.users['client1']
        self.request = self.factory.get('/')
        self.request.user = self.user1

    def test_get_generic_context(self):
        """Test if a generic context can be created."""
        context = get_generic_context(self.request)
        self.assertEqual(context['user'], self.user1, "Context user should match the request user")
        self.assertIn('BASE_TEMPLATE', context, "Context should contain 'BASE_TEMPLATE'")
        self.assertIn('is_superuser', context, "Context should contain 'is_superuser'")


class GetGenericContextWithExtraTests(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user1 = self.users['client1']
        self.request = self.factory.get('/')
        self.request.user = self.user1
        self.extra = {"key": "value"}

    def test_get_generic_context_with_extra(self):
        """Test if a generic context with extra data can be created."""
        context = get_generic_context_with_extra(self.request, self.extra)
        self.assertEqual(context['user'], self.user1, "Context user should match the request user")
        self.assertEqual(context['key'], "value", "Context should include extra data")
        self.assertIn('BASE_TEMPLATE', context, "Context should contain 'BASE_TEMPLATE'")
        self.assertIn('is_superuser', context, "Context should contain 'is_superuser'")


class HandleUnauthorizedResponseTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.message = "Unauthorized"

    def test_handle_unauthorized_response_json(self):
        """Test if an unauthorized response can be created when the response type is JSON."""
        request = self.factory.get('/')
        response = handle_unauthorized_response(request=request, message=self.message, response_type='json')
        self.assertEqual(response.status_code, 403, "Response status should be 403")
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['message'], self.message, "Response content should match the message")

    def test_handle_unauthorized_response_html(self):
        """Test if an unauthorized response can be created when the response type is HTML."""
        request = self.factory.get('/app-admin/user-events/')
        response = handle_unauthorized_response(request, self.message, 'html')
        self.assertEqual(response.status_code, 403, "Response status should be 403")
