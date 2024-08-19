# forms.py
# Path: appointment/forms.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from django import forms
from django.utils.translation import gettext as _
from phonenumber_field.formfields import SplitPhoneNumberField

from .models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, DayOff, Service, StaffMember,
    WorkingHours
)
from .utils.db_helpers import get_user_model
from .utils.validators import not_in_the_past


class SlotForm(forms.Form):
    selected_date = forms.DateField(validators=[not_in_the_past])
    staff_member = forms.ModelChoiceField(StaffMember.objects.all(),
                                          error_messages={'invalid_choice': 'Staff member does not exist'})


class AppointmentRequestForm(forms.ModelForm):
    class Meta:
        model = AppointmentRequest
        fields = ('date', 'start_time', 'end_time', 'service', 'staff_member')


class ReschedulingForm(forms.ModelForm):
    class Meta:
        model = AppointmentRescheduleHistory
        fields = ['reason_for_rescheduling']
        widgets = {
            'reason_for_rescheduling': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Reason for rescheduling...'}),
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
                    'placeholder': '1234567890'
                })
        self.fields['additional_info'].widget.attrs.update(
                {
                    'rows': 2,
                    'class': 'form-control',
                })
        self.fields['address'].widget.attrs.update(
                {
                    'rows': 2,
                    'class': 'form-control',
                    'placeholder': '1234 Main St, City, State, Zip Code',
                    'required': 'true'
                })
        self.fields['additional_info'].widget.attrs.update(
                {
                    'class': 'form-control',
                    'placeholder': 'I would like to be contacted by phone.'
                })


class ClientDataForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))


class PersonalInformationForm(forms.Form):
    # first_name, last_name, email
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

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
            'service_offered': forms.Select(attrs={'class': 'form-control'}),
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
            'service_offered': forms.Select(attrs={'class': 'form-control'}),
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


class StaffWorkingHoursForm(forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ['day_of_week', 'start_time', 'end_time']


class ServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['background_color'].widget.attrs['value'] = self.instance.background_color

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
                'placeholder': "Example: Overview of client's needs."
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'HH:MM:SS, (example: 00:15:00 for 15 minutes)'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: 100.00 (0 for free)'
            }),
            'down_payment': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: 50.00 (0 for free)'
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(choices=[('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')],
                                     attrs={'class': 'form-control'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'value': '#000000'}),
        }
