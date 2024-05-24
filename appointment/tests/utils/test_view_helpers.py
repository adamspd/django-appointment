# test_view_helpers.py
# Path: appointment/tests/test_view_helpers.py

from django.http import HttpRequest
from django.test import TestCase

from appointment.utils.view_helpers import generate_random_id, get_locale, is_ajax


class GetLocaleTests(TestCase):
    """Test cases for get_locale"""

    def test_get_locale_en(self):
        with self.settings(LANGUAGE_CODE='en'):
            self.assertEqual(get_locale(), 'en')

    def test_get_locale_en_us(self):
        with self.settings(LANGUAGE_CODE='en_US'):
            self.assertEqual(get_locale(), 'en')

    def test_get_locale_fr(self):
        # Set the local to French
        with self.settings(LANGUAGE_CODE='fr'):
            self.assertEqual(get_locale(), 'fr')

    def test_get_locale_fr_France(self):
        # Set the local to French
        with self.settings(LANGUAGE_CODE='fr_FR'):
            self.assertEqual(get_locale(), 'fr')

    def test_get_locale_others(self):
        with self.settings(LANGUAGE_CODE='de'):
            self.assertEqual(get_locale(), 'de')


class IsAjaxTests(TestCase):
    """Test cases for is_ajax"""

    def test_is_ajax_true(self):
        request = HttpRequest()
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.assertTrue(is_ajax(request))

    def test_is_ajax_false(self):
        request = HttpRequest()
        self.assertFalse(is_ajax(request))


class GenerateRandomIdTests(TestCase):
    """Test cases for generate_random_id"""

    def test_generate_random_id(self):
        id1 = generate_random_id()
        id2 = generate_random_id()
        self.assertNotEqual(id1, id2)
