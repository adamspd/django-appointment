# forms.py
# Path: appointment/forms.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

import re
from datetime import time

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import SplitPhoneNumberField

from .models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, DayOff, Unavailability, Service, StaffMember,
    WorkingHours
)
from .utils.db_helpers import get_user_model
from .utils.validators import not_in_the_past


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


class ReschedulingForm(forms.ModelForm):
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


class ClientDataForm(forms.Form):
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


class PersonalInformationForm(forms.Form):
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


class StaffAppointmentInformationForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['services_offered', 'slot_duration', 'lead_time', 'finish_time',
                  'appointment_buffer_time', 'work_on_saturday', 'work_on_sunday']
        widgets = {
            'services_offered': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'slot_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 30, 60, 90, 120... (in minutes)')
            }),
            'lead_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 08:00:00, 09:00:00... (24-hour format)')
            }),
            'finish_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 17:00:00, 18:00:00... (24-hour format)')
            }),
            'appointment_buffer_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 15, 30, 45, 60... (in minutes)')
            }),
            'work_on_saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'work_on_sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['user', 'services_offered', 'slot_duration', 'lead_time', 'finish_time',
                  'appointment_buffer_time', 'work_on_saturday', 'work_on_sunday']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'services_offered': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'slot_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 30, 60, 90, 120... (in minutes)')
            }),
            'lead_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 08:00:00, 09:00:00... (24-hour format)')
            }),
            'finish_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 17:00:00, 18:00:00... (24-hour format)')
            }),
            'appointment_buffer_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example value: 15, 30, 45, 60... (in minutes)')
            }),
            'work_on_saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'work_on_sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

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


class StaffDaysOffForm(forms.ModelForm):
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


class StaffUnavailabilityForm(forms.ModelForm):
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


class StaffWorkingHoursForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StaffWorkingHoursForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].initial = time(9, 0)
        self.fields['end_time'].initial = time(17, 0)

    class Meta:
        model = WorkingHours
        fields = ['day_of_week', 'start_time', 'end_time']


def color_to_hex(color):
    """Convert an ``rgb(r, g, b)`` color to ``#rrggbb``; any other value is returned unchanged."""
    match = re.fullmatch(r'\s*rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)\s*', color)
    if not match:
        return color
    return '#' + ''.join(f'{min(int(channel), 255):02x}' for channel in match.groups())


class ServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        # <input type="color"> only accepts #rrggbb; older services were given n rgb(r, g, b) default, which the
        # browser would show, and then save, as black.
        color = self.initial.get('background_color')
        if isinstance(color, str):
            self.initial['background_color'] = color_to_hex(color)

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
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('HH:MM:SS, (example: 00:15:00 for 15 minutes)')
            }),
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
