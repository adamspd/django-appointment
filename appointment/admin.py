from django.contrib import admin

from .models import Service, AppointmentRequest, Appointment, EmailVerificationCode


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
    search_fields = ('client__user__username', 'appointment_request__service__name',)
    list_filter = ('client', 'appointment_request__service',)


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code')
