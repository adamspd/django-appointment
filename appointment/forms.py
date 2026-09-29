# forms.py
# Path: appointment/forms.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

import re
from datetime import time, timedelta

from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_duration
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import SplitPhoneNumberField

from .models import (
    DAYS_OF_WEEK, Appointment, AppointmentRequest, AppointmentRescheduleHistory, DayOff, Unavailability, Service, StaffMember,
    WorkingHours
)
from .utils.db_helpers import get_user_model
from .utils.validators import not_in_the_past


def apply_widget_classes(form):
    """
    Swap the CSS classes the widgets use for the ones set in ``APPOINTMENT_FORM_CLASSES``.

    The setting maps a package class to yours, for example ``{'form-control': 'input', 'form-select': 'select'}``.
    An empty string removes the class. Classes not in the setting are kept.
    """
    mapping = getattr(settings, 'APPOINTMENT_FORM_CLASSES', None)
    if not mapping:
        return
    for field in form.fields.values():
        for widget in [field.widget, *getattr(field.widget, 'widgets', [])]:
            classes = widget.attrs.get('class')
            if not classes:
                continue
            new_classes = []
            for name in classes.split():
                new_classes.extend(mapping.get(name, name).split())
            if new_classes:
                widget.attrs['class'] = ' '.join(new_classes)
            else:
                del widget.attrs['class']


class WidgetClassesMixin:
    """Applies ``APPOINTMENT_FORM_CLASSES`` once the form is built."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_classes(self)


class DurationWidget(forms.MultiWidget):
    """
    Hours and minutes inputs for a duration. They post ``<name>_hours`` and ``<name>_minutes``.

    A single ``<name>`` value ("HH:MM:SS"), as older templates post, is still read.
    """
    template_name = 'appointment/widgets/duration.html'

    def __init__(self, attrs=None):
        widgets = {
            'hours': forms.NumberInput(attrs={'min': 0, 'placeholder': '0', 'aria-label': _('Hours')}),
            'minutes': forms.NumberInput(attrs={'min': 0, 'max': 59, 'placeholder': '30',
                                                'aria-label': _('Minutes')}),
        }
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, str):
            value = parse_duration(value)
        if not isinstance(value, timedelta):
            return [None, None]
        minutes = int(value.total_seconds()) // 60
        return list(divmod(minutes, 60))

    def value_from_datadict(self, data, files, name):
        hours, minutes = (data.get(f'{name}{suffix}') for suffix in self.widgets_names)
        if hours in (None, '') and minutes in (None, ''):
            return data.get(name)
        try:
            hours, minutes = int(hours or 0), int(minutes or 0)
        except (TypeError, ValueError):
            return 'invalid'  # DurationField rejects it with its own message
        if hours < 0 or minutes < 0:
            return 'invalid'
        hours, minutes = divmod(hours * 60 + minutes, 60)
        return f'{hours:02d}:{minutes:02d}:00'

    def value_omitted_from_data(self, data, files, name):
        return name not in data and all(f'{name}{suffix}' not in data for suffix in self.widgets_names)


# Short help texts for the staff forms; the model's longer ones stay for the Django admin
STAFF_HELP_TEXTS = {
    'slot_duration': _("Length of each slot, in minutes."),
    'appointment_buffer_time': _("Minutes between now and the first slot of today. Other days are not changed."),
}


class SlotForm(forms.Form):
    selected_date = forms.DateField(validators=[not_in_the_past])
    staff_member = forms.ModelChoiceField(
        StaffMember.objects.all(),
        error_messages={'invalid_choice': _('Staff member does not exist')}
    )
    service_id = forms.ModelChoiceField(
        queryset=Service.objects.none(),
        required=False,
        error_messages={'invalid_choice': _('Service does not exist')}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service_id'].queryset = Service.objects.all()


class AppointmentRequestForm(forms.ModelForm):
    class Meta:
        model = AppointmentRequest
        fields = ('date', 'start_time', 'end_time', 'service', 'staff_member')


class ReschedulingForm(WidgetClassesMixin, forms.ModelForm):
    class Meta:
        model = AppointmentRescheduleHistory
        fields = ['reason_for_rescheduling']
        widgets = {
            'reason_for_rescheduling': forms.Textarea(
                attrs={'rows': 4, 'placeholder': _('Reason for rescheduling...')}),
        }


class AppointmentForm(forms.ModelForm):
    phone = SplitPhoneNumberField()

    class Meta:
        model = Appointment
        fields = ('phone', 'want_reminder', 'address', 'additional_info')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].widget.attrs.update(
            {
                'placeholder': _('1234567890')
            })
        # Split widget: country code select, then the number.
        country_widget, number_widget = self.fields['phone'].widget.widgets
        country_widget.attrs.update({'class': 'form-select'})
        number_widget.attrs.update({'class': 'form-control'})
        self.fields['want_reminder'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['additional_info'].widget.attrs.update(
            {
                'rows': 2,
                'class': 'form-control',
            })
        self.fields['address'].widget.attrs.update(
            {
                'rows': 2,
                'class': 'form-control',
                'placeholder': _('1234 Main St, City, State, Zip Code')
            })
        self.fields['additional_info'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': _('I would like to be contacted by phone.')
            })
        apply_widget_classes(self)


class ClientDataForm(WidgetClassesMixin, forms.Form):
    name = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('John Doe')}))
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('john.doe@example.com')}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            # The name is prefilled but stays editable (saved to the account). The email is the account's identity:
            # the booking goes to that account, so it can't be changed here.
            self.fields['name'].initial = user.get_full_name()
            self.fields['email'].disabled = True
            self.fields['email'].initial = user.email


class PersonalInformationForm(WidgetClassesMixin, forms.Form):
    # first_name, last_name, email
    first_name = forms.CharField(max_length=50,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('John')}))
    last_name = forms.CharField(max_length=50,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Doe')}))
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('john.doe@example.com')}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # pop the user from the kwargs
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.user:
            if self.user.email == email:
                return email
            queryset = get_user_model().objects.exclude(pk=self.user.pk)
        else:
            queryset = get_user_model().objects.all()

        if queryset.filter(email=email).exists():
            raise forms.ValidationError(_("This email is already taken."))

        return email


class StaffAppointmentInformationForm(WidgetClassesMixin, forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['services_offered', 'slot_duration', 'lead_time', 'finish_time',
                  'appointment_buffer_time', 'work_on_saturday', 'work_on_sunday']
        widgets = {
            'services_offered': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            # Minutes: a short example fits the small field next to its "min" unit
            'slot_duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30', 'min': 0}),
            # The browser's time picker; it sends HH:MM, which TimeField accepts
            'lead_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'finish_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'appointment_buffer_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0',
                                                                'min': 0}),
            'work_on_saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'work_on_sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = STAFF_HELP_TEXTS


class StaffMemberForm(WidgetClassesMixin, forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['user', 'services_offered', 'slot_duration', 'lead_time', 'finish_time',
                  'appointment_buffer_time', 'work_on_saturday', 'work_on_sunday']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'services_offered': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            # Minutes: a short example fits the small field next to its "min" unit
            'slot_duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30', 'min': 0}),
            # The browser's time picker; it sends HH:MM, which TimeField accepts
            'lead_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'finish_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'appointment_buffer_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0',
                                                                'min': 0}),
            'work_on_saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'work_on_sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = STAFF_HELP_TEXTS

    def __init__(self, *args, **kwargs):
        super(StaffMemberForm, self).__init__(*args, **kwargs)
        # Exclude users who are already staff members
        existing_staff_user_ids = StaffMember.objects.values_list('user', flat=True)
        # Filter queryset for user field to include only superusers or users not already staff members
        self.fields['user'].queryset = get_user_model().objects.filter(
            is_superuser=True
        ).exclude(id__in=existing_staff_user_ids) | get_user_model().objects.exclude(
            id__in=existing_staff_user_ids
        )


class StaffDaysOffForm(WidgetClassesMixin, forms.ModelForm):
    class Meta:
        model = DayOff
        fields = ['start_date', 'end_date', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'datepicker'}),
            'end_date': forms.DateInput(attrs={'class': 'datepicker'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class StaffUnavailabilityForm(WidgetClassesMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StaffUnavailabilityForm, self).__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.localdate()
        self.fields['start_time'].initial = time(9, 0)
        self.fields['end_time'].initial = time(17, 0)

    class Meta:
        model = Unavailability
        fields = ['date', 'start_time', 'end_time', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'datepicker'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'timepicker'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'timepicker'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class StaffWorkingHoursForm(WidgetClassesMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StaffWorkingHoursForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].initial = time(9, 0)
        self.fields['end_time'].initial = time(17, 0)

    class Meta:
        model = WorkingHours
        fields = ['day_of_week', 'start_time', 'end_time']


class UnavailabilityDataForm(forms.Form):
    """Reads what an unavailability form posts: ISO ``date`` (YYYY-MM-DD) and ``start_time``/``end_time`` (HH:MM)."""
    date = forms.DateField()
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    description = forms.CharField(required=False, max_length=255)

    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get('start_time'), cleaned_data.get('end_time')
        if start and end and start >= end:
            self.add_error('end_time', _("Start time must be before end time."))
        return cleaned_data


class WorkingHoursDataForm(forms.Form):
    """Reads what a working hours form posts: ``day_of_week`` and ISO ``start_time``/``end_time`` (HH:MM)."""
    day_of_week = forms.TypedChoiceField(choices=DAYS_OF_WEEK, coerce=int)
    start_time = forms.TimeField()
    end_time = forms.TimeField()

    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get('start_time'), cleaned_data.get('end_time')
        if start and end and start >= end:
            self.add_error('end_time', _("Start time must be before end time."))
        return cleaned_data


def color_to_hex(color):
    """Convert an ``rgb(r, g, b)`` color to ``#rrggbb``; any other value is returned unchanged."""
    match = re.fullmatch(r'\s*rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)\s*', color)
    if not match:
        return color
    return '#' + ''.join(f'{min(int(channel), 255):02x}' for channel in match.groups())


class ServiceForm(WidgetClassesMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        # <input type="color"> only accepts #rrggbb; older services were given n rgb(r, g, b) default, which the
        # browser would show, and then save, as black.
        color = self.initial.get('background_color')
        if isinstance(color, str):
            self.initial['background_color'] = color_to_hex(color)
        # <input type="number"> needs a dot as the decimal separator, so the amounts are never localized
        for name in ('price', 'down_payment'):
            self.fields[name].localize = False
            self.fields[name].widget.is_localized = False

    class Meta:
        model = Service
        fields = ['name', 'description', 'duration', 'price', 'down_payment', 'image', 'currency', 'background_color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example: First Consultation')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _("Example: Overview of client's needs.")
            }),
            'duration': DurationWidget(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example: 100.00 (0 for free)')
            }),
            'down_payment': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example: 50.00 (0 for free)')
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(choices=[('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')],
                                     attrs={'class': 'form-select'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }
