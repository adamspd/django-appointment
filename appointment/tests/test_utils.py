import datetime
import logging
from unittest.mock import patch

from django.apps import apps
from django.http import HttpRequest
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from appointment.models import Appointment, Service, AppointmentRequest, Config
from appointment.settings import APPOINTMENT_WEBSITE_NAME, APPOINTMENT_SLOT_DURATION, APPOINTMENT_LEAD_TIME, \
    APPOINTMENT_FINISH_TIME, APPOINTMENT_BUFFER_TIME, APPOINTMENT_CLIENT_MODEL
from appointment.utils import Utility


class UtilityTestCase(TestCase):
    # Test cases for generate_random_id

    def setUp(self) -> None:
        self.test_service = Service.objects.create(name="Test Service", duration=datetime.timedelta(hours=1), price=100)
        self.user_model = Utility.get_user_model()
        self.user = self.user_model.objects.create_user(first_name="Tester",
                                                        email="testemail@gmail.com",
                                                        username="test_user", password="Kfdqi3!?n")

    def test_generate_random_id(self):
        id1 = Utility.generate_random_id()
        id2 = Utility.generate_random_id()
        self.assertNotEqual(id1, id2)

    # Test cases for get_timestamp
    def test_get_timestamp(self):
        ts = Utility.get_timestamp()
        self.assertIsNotNone(ts)
        self.assertIsInstance(ts, str)

    # Test cases for is_ajax
    def test_is_ajax_true(self):
        request = HttpRequest()
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.assertTrue(Utility.is_ajax(request))

    def test_is_ajax_false(self):
        request = HttpRequest()
        self.assertFalse(Utility.is_ajax(request))

    # Test cases for get_available_slots
    def test_get_available_slots(self):
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        date = Utility.convert_str_to_date(date_str)
        ar = AppointmentRequest.objects.create(
            date=date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            service=self.test_service
        )
        appointment = Appointment.objects.create(appointment_request=ar, client=self.user)
        slots = Utility.get_available_slots(date, [appointment])
        self.assertIsInstance(slots, list)
        logging.info(slots)
        self.assertNotIn('09:00 AM', slots)

    def test_get_available_slots_with_config(self):
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        date = Utility.convert_str_to_date(date_str)
        lead_time = datetime.time(8, 0)
        finish_time = datetime.time(17, 0)
        slot_duration = 30
        appointment_buffer_time = 2.0
        Config.objects.create(
            lead_time=lead_time,
            finish_time=finish_time,
            slot_duration=slot_duration,
            appointment_buffer_time=appointment_buffer_time
        )
        ar = AppointmentRequest.objects.create(
            date=date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            service=self.test_service
        )
        appointment = Appointment.objects.create(appointment_request=ar, client=self.user)
        slots = Utility.get_available_slots(date, [appointment])
        self.assertIsInstance(slots, list)
        logging.info(slots)
        self.assertNotIn('09:00 AM', slots)
        # Additional assertions to verify that the slots are calculated correctly

    # Test cases for get_locale
    def test_get_locale_en(self):
        with self.settings(LANGUAGE_CODE='en'):
            self.assertEqual(Utility.get_locale(), 'en')

    def test_get_locale_en_us(self):
        with self.settings(LANGUAGE_CODE='en_US'):
            self.assertEqual(Utility.get_locale(), 'en')

    def test_get_locale_fr(self):
        # Set the local to French
        with self.settings(LANGUAGE_CODE='fr'):
            self.assertEqual(Utility.get_locale(), 'fr')

    def test_get_locale_fr_France(self):
        # Set the local to French
        with self.settings(LANGUAGE_CODE='fr_FR'):
            self.assertEqual(Utility.get_locale(), 'fr')

    def test_get_locale_others(self):
        with self.settings(LANGUAGE_CODE='de'):
            self.assertEqual(Utility.get_locale(), 'en')

    # Test cases for get_current_year
    def test_get_current_year(self):
        self.assertEqual(Utility.get_current_year(), datetime.datetime.now().year)

    def test_get_timezone_txt(self):
        self.assertIn(Utility.get_timezone_txt(), [
            'Universal Time Coordinated (UTC)',
            'Eastern Daylight Time (US & Canada)',
            # Add other valid timezone strings here
        ])

    # Test cases for get_timezone
    def test_get_timezone(self):
        self.assertIsNotNone(Utility.get_timezone())

    # Test cases for convert_str_to_date
    def test_convert_str_to_date_valid(self):
        date_str = '2023-07-31'
        date_obj = Utility.convert_str_to_date(date_str)
        self.assertEqual(date_obj, datetime.date(2023, 7, 31))

    def test_convert_str_to_date_invalid(self):
        date_str = 'invalid-date'
        with self.assertRaises(ValueError):
            Utility.convert_str_to_date(date_str)

    def test_get_website_name_no_config(self):
        website_name = Utility.get_website_name()
        self.assertEqual(website_name, APPOINTMENT_WEBSITE_NAME)

    def test_get_website_name_with_config(self):
        Config.objects.create(website_name="Test Website")
        website_name = Utility.get_website_name()
        self.assertEqual(website_name, "Test Website")

    def test_get_appointment_slot_duration_no_config(self):
        slot_duration = Utility.get_appointment_slot_duration()
        self.assertEqual(slot_duration, APPOINTMENT_SLOT_DURATION)

    def test_get_appointment_slot_duration_with_config(self):
        Config.objects.create(slot_duration=45)
        slot_duration = Utility.get_appointment_slot_duration()
        self.assertEqual(slot_duration, 45)

    # Test cases for get_appointment_lead_time
    def test_get_appointment_lead_time_no_config(self):
        lead_time = Utility.get_appointment_lead_time()
        self.assertEqual(lead_time, APPOINTMENT_LEAD_TIME)

    def test_get_appointment_lead_time_with_config(self):
        config_lead_time = datetime.time(hour=7, minute=30)
        Config.objects.create(lead_time=config_lead_time)
        lead_time = Utility.get_appointment_lead_time()
        self.assertEqual(lead_time, config_lead_time)

    # Test cases for get_appointment_finish_time
    def test_get_appointment_finish_time_no_config(self):
        finish_time = Utility.get_appointment_finish_time()
        self.assertEqual(finish_time, APPOINTMENT_FINISH_TIME)

    def test_get_appointment_finish_time_with_config(self):
        config_finish_time = datetime.time(hour=18, minute=30)
        Config.objects.create(finish_time=config_finish_time)
        finish_time = Utility.get_appointment_finish_time()
        self.assertEqual(finish_time, config_finish_time)

    # Test cases for get_appointment_buffer_time
    def test_get_appointment_buffer_time_no_config(self):
        buffer_time = Utility.get_appointment_buffer_time()
        self.assertEqual(buffer_time, APPOINTMENT_BUFFER_TIME)

    def test_get_appointment_buffer_time_with_config(self):
        config_buffer_time = 0.5  # 30 minutes
        Config.objects.create(appointment_buffer_time=config_buffer_time)
        buffer_time = Utility.get_appointment_buffer_time()
        self.assertEqual(buffer_time, config_buffer_time)

    # Test cases for get_finish_button_text
    def test_get_finish_button_text_free_service(self):
        service = Service(price=0)
        button_text = Utility.get_finish_button_text(service)
        self.assertEqual(button_text, _("Finish"))

    def test_get_finish_button_text_paid_service(self):
        with patch('appointment.utils.APPOINTMENT_PAYMENT_URL', 'https://payment.com'):
            service = Service(price=100)
            button_text = Utility.get_finish_button_text(service)
            self.assertEqual(button_text, _("Pay Now"))

    # Test cases for get_user_model
    def test_get_client_model(self):
        client_model = Utility.get_user_model()
        self.assertEqual(client_model, apps.get_model(APPOINTMENT_CLIENT_MODEL))
