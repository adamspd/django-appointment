# test_email_sender.py
# Path: appointment/tests/test_email_sender.py

import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings
from django.utils import translation

from appointment.email_sender import get_admins, notify_admin, send_email
from appointment.email_sender.email_sender import html_to_text, render_text_body
from appointment.tasks import send_email_task

ICS = ('appointment.ics', 'BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n', 'text/calendar')
HTML = "<html><body><h1>Hello Jack</h1>\n\n\n<p>Your appointment is <b>confirmed</b>.</p></body></html>"


def render_html(template_name, context=None, request=None):
    if template_name.endswith('.txt'):
        raise TemplateDoesNotExist(template_name)
    return HTML


@patch('appointment.email_sender.email_sender.get_use_django_q_for_emails', return_value=False)
@patch('appointment.email_sender.email_sender.loader.render_to_string', side_effect=render_html)
class SynchronousEmailTests(SimpleTestCase):
    """Without Django-Q, emails must carry the same parts they carry when sent from the task."""

    def test_send_email_keeps_attachments(self, *_):
        send_email(recipient_list=['jack@sgc.mil'], subject='Hi', template_url='emails/x.html', attachments=[ICS])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0][0], 'appointment.ics')

    def test_templated_email_has_text_and_html_parts(self, *_):
        send_email(recipient_list=['jack@sgc.mil'], subject='Hi', template_url='emails/x.html')
        email = mail.outbox[0]
        self.assertEqual(email.body, "Hello Jack\n\nYour appointment is confirmed.")
        self.assertEqual(email.alternatives[0][0], HTML)
        self.assertEqual(email.alternatives[0][1], 'text/html')

    def test_plain_message_is_sent_as_is(self, *_):
        send_email(recipient_list=['jack@sgc.mil'], subject='Hi', message='Plain text')
        self.assertEqual(mail.outbox[0].body, 'Plain text')
        self.assertEqual(mail.outbox[0].alternatives, [])

    @override_settings(ADMINS=[('George', 'george@sgc.mil')])
    def test_notify_admin_keeps_attachments(self, *_):
        notify_admin(subject='New', template_url='emails/x.html', attachments=[ICS])
        email = mail.outbox[0]
        self.assertEqual(email.to, ['george@sgc.mil'])
        self.assertEqual(email.attachments[0][0], 'appointment.ics')
        self.assertTrue(email.body)


class TextBodyTests(SimpleTestCase):
    def test_head_and_styles_are_not_part_of_the_text(self):
        html = ("<html><head><title>Booking</title><style>p { color: red; }</style></head>"
                "<body><STYLE type='text/css'>.x {}</STYLE><p>Hello</p><script>var a;</script></body></html>")
        self.assertEqual(html_to_text(html), "Hello")

    def test_entities_are_decoded(self):
        self.assertEqual(html_to_text("<p>&copy; 2026 SG&amp;C</p>"), "© 2026 SG&C")

    def test_txt_template_next_to_html_is_preferred(self):
        with patch('appointment.email_sender.email_sender.loader.render_to_string', return_value='From txt') as render:
            self.assertEqual(render_text_body('emails/x.html', {}, HTML), 'From txt')
            self.assertEqual(render.call_args[0][0], 'emails/x.txt')

    def test_falls_back_to_the_html(self):
        with patch('appointment.email_sender.email_sender.loader.render_to_string', side_effect=render_html):
            self.assertEqual(render_text_body('emails/x.html', {}, HTML), html_to_text(HTML))


class SendEmailTaskTests(SimpleTestCase):
    def test_task_sends_text_html_and_attachments(self):
        send_email_task(['jack@sgc.mil'], 'Hi', '', HTML, 'noreply@sgc.mil', attachments=[ICS])
        email = mail.outbox[0]
        self.assertEqual(email.body, html_to_text(HTML))
        self.assertEqual(email.alternatives[0][0], HTML)
        self.assertEqual(email.attachments[0][0], 'appointment.ics')

    def test_task_without_html_sends_plain_text(self):
        send_email_task(['jack@sgc.mil'], 'Hi', 'Plain text', None, 'noreply@sgc.mil')
        self.assertEqual(mail.outbox[0].body, 'Plain text')
        self.assertEqual(mail.outbox[0].alternatives, [])


class PackageEmailTemplatesTests(SimpleTestCase):
    """The package's own email templates render in HTML and text, with whole sentences translated."""

    def render_all(self, lang):
        ar = SimpleNamespace(date=datetime.date(2030, 10, 14), start_time=datetime.time(10, 30),
                             end_time=datetime.time(11, 30))
        appointment = SimpleNamespace(get_service_name='Stargate Diagnostics', appointment_request=ar, phone='',
                                      client=SimpleNamespace(email='jack@sgc.mil'), additional_info='',
                                      address='')
        contexts = {
            'thank_you_email': {'first_name': 'Jack', 'company': 'SGC', 'more_details': {'Service': 'Gate'},
                                'month_year': 'OCT 2030', 'day': '14', 'main_title': 'Booked',
                                'reschedule_link': 'https://sgc.mil/r/1'},
            'admin_new_appointment_email': {'recipient_name': 'George', 'client_name': 'Jack',
                                            'appointment': appointment, 'staff_member_name': 'Sam'},
            'reminder_email': {'first_name': 'Jack', 'appointment': appointment, 'recipient_type': 'client'},
            'reschedule_email': {'is_confirmation': False, 'client_name': 'Jack', 'service_name': 'Gate',
                                 'old_date': ar.date, 'reschedule_date': ar.date, 'old_start_time': ar.start_time,
                                 'start_time': ar.start_time, 'old_end_time': ar.end_time,
                                 'end_time': ar.end_time, 'company': 'SGC'},
        }
        rendered = {}
        with translation.override(lang):
            for name, context in contexts.items():
                for ext in ('html', 'txt'):
                    rendered[f'{name}.{ext}'] = render_to_string(f'email_sender/{name}.{ext}', context)
        return rendered

    def test_every_template_renders_in_html_and_text(self):
        for name, text in self.render_all('en').items():
            self.assertTrue(text.strip(), name)
            if name.endswith('.txt'):
                self.assertNotIn('<', text, name)

    def test_sentences_with_names_are_translated_whole(self):
        rendered = self.render_all('fr')
        self.assertIn('Bonjour Jack,', rendered['reminder_email.txt'])
        self.assertIn('Bonjour George,', rendered['admin_new_appointment_email.html'])
        self.assertIn('Une nouvelle demande de rendez-vous a été reçue pour Sam.',
                      rendered['admin_new_appointment_email.txt'])
        self.assertIn('Un rendez-vous avec Jack pour le service Gate a été reprogrammé.',
                      rendered['reschedule_email.txt'])
        self.assertIn('lang="fr"', rendered['thank_you_email.html'])


class AdminsSettingTests(SimpleTestCase):
    """ADMINS works in both of Django's forms: (name, email) pairs, and email addresses alone (Django 6.0+)."""

    @override_settings(ADMINS=[('George', 'george@sgc.mil'), 'walter@sgc.mil'])
    def test_both_forms_give_name_and_email(self):
        self.assertEqual(get_admins(), [('George', 'george@sgc.mil'), ('walter@sgc.mil', 'walter@sgc.mil')])

    @override_settings(ADMINS=['george@sgc.mil'])
    @patch('appointment.email_sender.email_sender.get_use_django_q_for_emails', return_value=False)
    def test_notify_admin_sends_to_plain_addresses(self, *_):
        notify_admin(subject='New', message='Hello')
        self.assertEqual(mail.outbox[0].to, ['george@sgc.mil'])
