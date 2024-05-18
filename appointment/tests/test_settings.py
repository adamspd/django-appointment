# test_settings.py
# Path: appointment/tests/test_settings.py

from unittest.mock import patch

from django.test import TestCase

from appointment.settings import check_q_cluster


class CheckQClusterTest(TestCase):
    @patch('appointment.settings.settings')
    @patch('appointment.settings.logger')
    def test_check_q_cluster_with_django_q_missing(self, mock_logger, mock_settings):
        # Simulate 'django_q' not being in INSTALLED_APPS
        mock_settings.INSTALLED_APPS = []

        # Call the function under test
        result = check_q_cluster()

        # Check the result
        self.assertFalse(result)
        # Verify logger was called with the expected warning about 'django_q' not being installed
        mock_logger.warning.assert_called_with(
            "Django Q is not in settings.INSTALLED_APPS. Please add it to the list.\n"
            "Example: \n\n"
            "INSTALLED_APPS = [\n"
            "    ...\n"
            "    'appointment',\n"
            "    'django_q',\n"
            "]\n")

    @patch('appointment.settings.settings')
    @patch('appointment.settings.logger')
    def test_check_q_cluster_with_all_configurations_present(self, mock_logger, mock_settings):
        # Simulate both 'django_q' being in INSTALLED_APPS and 'Q_CLUSTER' configuration present
        mock_settings.INSTALLED_APPS = ['django_q']
        mock_settings.Q_CLUSTER = {'name': 'DjangORM'}

        # Call the function under test
        result = check_q_cluster()

        # Check the result and ensure no warnings are logged
        self.assertTrue(result)
        mock_logger.warning.assert_not_called()
