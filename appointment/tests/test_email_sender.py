# test_email_sender.py
# Path: appointment/tests/test_email_sender.py

from unittest.mock import patch

from django.core import mail
from django.template import TemplateDoesNotExist
from django.test import SimpleTestCase, override_settings

from appointment.email_sender import notify_admin, send_email
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
