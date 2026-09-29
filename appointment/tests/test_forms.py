import datetime

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import translation

from appointment.forms import AppointmentForm, ClientDataForm, DurationWidget, ServiceForm, StaffMemberForm
from appointment.models import Service


def service_data(**extra):
    data = {'name': 'Consultation', 'price': '100', 'down_payment': '0', 'currency': 'USD',
            'background_color': '#00307c'}
    data.update(extra)
    return data


class DurationWidgetTests(SimpleTestCase):
    def test_hours_and_minutes_make_a_duration(self):
        form = ServiceForm(data=service_data(duration_hours='1', duration_minutes='30'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['duration'], datetime.timedelta(hours=1, minutes=30))

    def test_minutes_only_and_minutes_over_an_hour(self):
        form = ServiceForm(data=service_data(duration_minutes='90'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['duration'], datetime.timedelta(minutes=90))

    def test_old_single_value_still_works(self):
        form = ServiceForm(data=service_data(duration='00:45:00'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['duration'], datetime.timedelta(minutes=45))

    def test_bad_values_are_rejected(self):
        for hours, minutes in (('x', '10'), ('-1', '10')):
            with self.subTest(hours=hours):
                form = ServiceForm(data=service_data(duration_hours=hours, duration_minutes=minutes))
                self.assertIn('duration', form.errors)

    def test_empty_inputs_are_required(self):
        form = ServiceForm(data=service_data(duration_hours='', duration_minutes=''))
        self.assertIn('duration', form.errors)

    def test_decompress(self):
        widget = DurationWidget()
        self.assertEqual(widget.decompress(datetime.timedelta(hours=2, minutes=5)), [2, 5])
        self.assertEqual(widget.decompress('00:15:00'), [0, 15])
        self.assertEqual(widget.decompress(None), [None, None])

    def test_renders_hours_and_minutes_inputs(self):
        service = Service(name='x', duration=datetime.timedelta(minutes=75), price=10)
        html = str(ServiceForm(instance=service)['duration'])
        self.assertIn('name="duration_hours" value="1"', html)
        self.assertIn('name="duration_minutes" value="15"', html)


class ServiceFormPriceTests(SimpleTestCase):
    def test_price_is_not_localized(self):
        service = Service(name='x', duration=datetime.timedelta(minutes=30), price='150.50', down_payment='10.25')
        with translation.override('fr'), override_settings(USE_THOUSAND_SEPARATOR=True):
            form = ServiceForm(instance=service)
            self.assertIn('value="150.50"', str(form['price']))
            self.assertIn('value="10.25"', str(form['down_payment']))


class WidgetClassesTests(TestCase):
    def test_default_classes_are_kept(self):
        self.assertIn('form-control', ClientDataForm().fields['name'].widget.attrs['class'])

    @override_settings(APPOINTMENT_FORM_CLASSES={'form-control': 'input input-bordered', 'form-select': ''})
    def test_classes_are_swapped_or_removed(self):
        self.assertEqual(ClientDataForm().fields['name'].widget.attrs['class'], 'input input-bordered')
        form = ServiceForm()
        self.assertNotIn('class', form.fields['currency'].widget.attrs)
        self.assertEqual(form.fields['background_color'].widget.attrs['class'], 'input input-bordered form-control-color')
        # The two inputs of the duration widget get the class too
        self.assertIn('input input-bordered', str(form['duration']))

    @override_settings(APPOINTMENT_FORM_CLASSES={'form-control': 'input', 'form-select': 'select'})
    def test_appointment_form_and_its_phone_widgets(self):
        form = AppointmentForm()
        country, number = form.fields['phone'].widget.widgets
        self.assertEqual(country.attrs['class'], 'select')
        self.assertEqual(number.attrs['class'], 'input')
        self.assertEqual(form.fields['address'].widget.attrs['class'], 'input')

    @override_settings(APPOINTMENT_FORM_CLASSES={'form-control': 'input'})
    def test_the_setting_does_not_leak_into_the_next_form(self):
        ClientDataForm()
        with override_settings(APPOINTMENT_FORM_CLASSES=None):
            self.assertEqual(ClientDataForm().fields['name'].widget.attrs['class'], 'form-control')


class StaffFormTests(TestCase):
    def test_services_are_checkboxes(self):
        self.assertEqual(StaffMemberForm().fields['services_offered'].widget.__class__.__name__,
                         'CheckboxSelectMultiple')

    def test_short_help_text(self):
        help_text = str(StaffMemberForm().fields['appointment_buffer_time'].help_text)
        self.assertLess(len(help_text), 100)
