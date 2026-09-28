# test_management.py
# Path: appointment/tests/test_management.py

from io import StringIO

from django.core.management import call_command, get_commands
from django.test import TestCase


class ManagementCommandTests(TestCase):
    def test_cleanup_command_is_found(self):
        """The command's folders are Python packages, so Django (and the wheel) find it."""
        self.assertEqual(get_commands().get('cleanup_appointment_requests'), 'appointment')

    def test_cleanup_command_dry_run(self):
        out = StringIO()
        call_command('cleanup_appointment_requests', '--dry-run', stdout=out)
        self.assertIn('Cleanup Appointment Requests', out.getvalue())
