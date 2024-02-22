# admin.py
# Path: appointment/admin.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from django import forms
from django.contrib import admin

from .models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, Config, DayOff, EmailVerificationCode,
    PasswordResetToken, Service, StaffMember, WorkingHours
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'created_at', 'updated_at',)
    search_fields = ('name',)
    list_filter = ('duration',)


@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'service', 'created_at', 'updated_at',)
    search_fields = ('date', 'service__name',)
    list_filter = ('date', 'service',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'appointment_request', 'created_at', 'updated_at',)
    search_fields = ('appointment_request__service__name',)
    list_filter = ('client', 'appointment_request__service',)


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code')


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = (
        'slot_duration', 'lead_time', 'finish_time', 'appointment_buffer_time', 'website_name', 'app_offered_by_label')


# Define a custom ModelForm for StaffMember
class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    form = StaffMemberForm
    list_display = (
        'get_staff_member_name', 'get_slot_duration', 'lead_time', 'finish_time', 'work_on_saturday', 'work_on_sunday')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('work_on_saturday', 'work_on_sunday', 'lead_time', 'finish_time')


@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'start_date', 'end_date', 'description')
    search_fields = ('description',)
    list_filter = ('start_date', 'end_date')


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'day_of_week', 'start_time', 'end_time')
    search_fields = ('day_of_week',)
    list_filter = ('day_of_week', 'start_time', 'end_time')


@admin.register(AppointmentRescheduleHistory)
class AppointmentRescheduleHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'appointment_request', 'date', 'start_time',
        'end_time', 'staff_member', 'reason_for_rescheduling', 'created_at'
    )
    search_fields = (
        'appointment_request__id_request', 'staff_member__user__first_name',
        'staff_member__user__last_name', 'reason_for_rescheduling'
    )
    list_filter = ('appointment_request__service', 'date', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'status')
    search_fields = ('user__email', 'token')
    list_filter = ('status', 'expires_at')
    date_hierarchy = 'expires_at'
    ordering = ('-expires_at',)
