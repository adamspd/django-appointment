import json

from django.test import RequestFactory

from appointment.tests.base.base_test import BaseTest
from appointment.utils.json_context import (
    convert_appointment_to_json,
    json_response,
    get_generic_context,
    get_generic_context_with_extra,
    handle_unauthorized_response
)


class JsonContextTests(BaseTest):

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.appointment = self.create_appointment_for_user1()

    def test_convert_appointment_to_json(self):
        """Test if an appointment can be converted to JSON."""
        request = self.factory.get('/')
        request.user = self.user1
        appointments = [self.appointment]
        data = convert_appointment_to_json(request, appointments)
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 1)
        self.assertTrue("id" in data[0])

    def test_json_response(self):
        """Test if a JSON response can be created."""
        message = "Test Message"
        response = json_response(message=message)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['message'], message)

    def test_get_generic_context(self):
        """Test if a generic context can be created."""
        request = self.factory.get('/')
        request.user = self.user1
        context = get_generic_context(request)
        self.assertEqual(context['user'], self.user1)

    def test_get_generic_context_with_extra(self):
        """Test if a generic context with extra data can be created."""
        request = self.factory.get('/')
        request.user = self.user1
        extra = {"key": "value"}
        context = get_generic_context_with_extra(request, extra)
        self.assertEqual(context['user'], self.user1)
        self.assertEqual(context['key'], "value")

    def test_handle_unauthorized_response_json(self):
        """Test if an unauthorized response can be created when the response type is JSON."""
        request = self.factory.get('/')
        message = "Unauthorized"
        response = handle_unauthorized_response(request=request, message=message, response_type='json')
        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['message'], message)

    def test_handle_unauthorized_response_html(self):
        """Test if an unauthorized response can be created when the response type is HTML."""
        request = self.factory.get('/app-admin/user-events/')
        message = "Unauthorized"
        response = handle_unauthorized_response(request, message, 'html')
        self.assertEqual(response.status_code, 403)
