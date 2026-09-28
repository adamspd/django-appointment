# test_templatetags.py
# Path: appointment/tests/test_templatetags.py

import datetime

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.utils import timezone

from appointment.models import AppointmentRequest
from appointment.templatetags.appointment_tags import initials, money, upcoming_appointments
from appointment.tests.base.base_test import BaseTest


class UpcomingAppointmentsTagTests(BaseTest):
    def test_counts_upcoming_and_all_for_a_service_and_staff_member(self):
        today = timezone.localdate()
        past = self.create_appt_request_for_sm1(date_=today + datetime.timedelta(days=5))
        soon = self.create_appt_request_for_sm1(date_=today + datetime.timedelta(days=1))
        other = self.create_appt_request_for_sm2(date_=today + datetime.timedelta(days=1))
        for ar in (past, soon, other):
            self.create_appt_for_sm1(appointment_request=ar)
        # Saving refuses past dates, so move it back without save()
        AppointmentRequest.objects.filter(pk=past.pk).update(date=today - datetime.timedelta(days=3))

        bookings = upcoming_appointments(service=self.service1)
        self.assertEqual((bookings['upcoming_count'], bookings['total_count']), (1, 2))
        self.assertEqual(bookings['upcoming'][0].appointment_request, soon)

        mine = upcoming_appointments(staff_member=self.staff_member2.user)
        self.assertEqual(mine['total_count'], 1)
        self.assertEqual(upcoming_appointments(staff_member=self.staff_member2)['total_count'], 1)

    def test_tag_in_a_template(self):
        rendered = Template('{% load appointment_tags %}{% upcoming_appointments limit=2 as b %}{{ b.total_count }}')
        self.assertEqual(rendered.render(Context()), '0')


class FilterTests(BaseTest):
    def test_initials(self):
        user = get_user_model()(first_name='Samantha', last_name='Carter', username='sam', email='s@x.com')
        self.assertEqual(initials(user), 'SC')
        user.first_name = ''
        self.assertEqual(initials(user), 'S')
        self.assertEqual(initials(None), '')

    def test_money_follows_the_active_language(self):
        self.assertEqual(money(150, 'USD'), '$150')
        self.assertEqual(money(None), '')
