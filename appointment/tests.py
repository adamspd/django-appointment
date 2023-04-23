import json
from datetime import date, time, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from appointment.models import Service, AppointmentRequest
from appointment.utils import Utility


class UtilityTestCase(TestCase):
    def test_generate_random_id(self):
        id1 = Utility.generate_random_id()
        id2 = Utility.generate_random_id()
        self.assertNotEqual(id1, id2)

    def test_get_timestamp(self):
        ts = Utility.get_timestamp()
        self.assertIsNotNone(ts)
        self.assertIsInstance(ts, str)


class ServiceModelTestCase(TestCase):
    def setUp(self):
        Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100)

    def test_service_creation(self):
        service = Service.objects.get(name="Test Service")
        self.assertIsNotNone(service)
        self.assertEqual(service.duration, timedelta(hours=1))
        self.assertEqual(service.price, 100)


class AppointmentRequestModelTestCase(TestCase):
    def setUp(self):
        service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100)
        AppointmentRequest.objects.create(date=date.today(), start_time=time(9, 0), end_time=time(10, 0),
                                          service=service)

    def test_appointment_request_creation(self):
        ar = AppointmentRequest.objects.get(service__name="Test Service")
        self.assertIsNotNone(ar)
        self.assertEqual(ar.start_time, time(9, 0))
        self.assertEqual(ar.end_time, time(10, 0))


class AppointmentViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.service = Service.objects.create(name="Test Service", duration=timedelta(hours=1), price=100)
        self.appointment_request = AppointmentRequest.objects.create(date=date.today(), start_time=time(9, 0),
                                                                     end_time=time(10, 0), service=self.service)

    def test_get_available_slots_ajax(self):
        response = self.client.get(reverse('appointment:available_slots_ajax'),
                                   {'selected_date': date.today().isoformat()}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data)
        self.assertEqual(response_data['error'], False)

    def test_get_next_available_date_ajax(self):
        response = self.client.get(reverse('appointment:request_next_available_slot', args=[self.service.id]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data)
        self.assertIsNotNone(response_data['next_available_date'])
