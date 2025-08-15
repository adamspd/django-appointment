# models.py
# Path: appointment/models.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""
import colorsys
import datetime
import random
import string
import uuid

from babel.numbers import get_currency_symbol
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from phonenumber_field.modelfields import PhoneNumberField

from appointment.utils.date_time import convert_minutes_in_human_readable_format, get_timestamp, get_weekday_num, \
    time_difference
from appointment.utils.view_helpers import generate_random_id, get_locale

PAYMENT_TYPES = (
    ('full', _('Full payment')),
    ('down', _('Down payment')),
)

DAYS_OF_WEEK = (
    (0, _('Sunday')),
    (1, _('Monday')),
    (2, _('Tuesday')),
    (3, _('Wednesday')),
    (4, _('Thursday')),
    (5, _('Friday')),
    (6, _('Saturday')),
)


def generate_rgb_color():
    hue = random.random()  # Random hue between 0 and 1
    saturation = 0.9  # High saturation to ensure a vivid color
    value = 0.9  # High value to ensure a bright color

    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)

    # Convert to 0-255 RGB values
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)

    return f'rgb({r}, {g}, {b})'


class Service(models.Model):
    """
    Represents a service provided by the appointment system.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    name = models.CharField(max_length=100, blank=False, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    duration = models.DurationField(
        validators=[MinValueValidator(datetime.timedelta(seconds=1))],
        verbose_name=_("Duration")
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Price")
    )
    down_payment = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Down Payment")
    )
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name=_('Image'), )
    currency = models.CharField(
        max_length=3,
        default='USD',
        validators=[MaxLengthValidator(3), MinLengthValidator(3)],
        verbose_name=_("Currency")
    )
    background_color = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=generate_rgb_color,
        verbose_name=_("Background Color")
    )
    reschedule_limit = models.PositiveIntegerField(
        default=0,
        help_text=_("Maximum number of times an appointment can be rescheduled."),
        verbose_name=_("Reschedule limit")
    )
    allow_rescheduling = models.BooleanField(
        default=False,
        help_text=_("Indicates whether appointments for this service can be rescheduled."),
        verbose_name=_("Allow Rescheduling")
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        ordering = ['name']  # alphabetical by default
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price)  # Convert Decimal to string for JSON serialization
        }

    def get_duration_parts(self):
        total_seconds = int(self.duration.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return days, hours, minutes, seconds

    def get_duration(self):
        days, hours, minutes, seconds = self.get_duration_parts()
        parts = []

        if days:
            parts.append(ngettext(
                    "%(count)d day",
                    "%(count)d days",
                    days
            ) % {'count': days})

        if hours:
            parts.append(ngettext(
                    "%(count)d hour",
                    "%(count)d hours",
                    hours
            ) % {'count': hours})

        if minutes:
            parts.append(ngettext(
                    "%(count)d minute",
                    "%(count)d minutes",
                    minutes
            ) % {'count': minutes})

        if seconds:
            parts.append(ngettext(
                    "%(count)d second",
                    "%(count)d seconds",
                    seconds
            ) % {'count': seconds})

        return ' '.join(parts)

    def get_price(self):
        # Check if the decimal part is 0
        if self.price % 1 == 0:
            return int(self.price)  # Return as an integer
        else:
            return self.price  # Return the original float value

    def get_currency_icon(self):
        return get_currency_symbol(self.currency, locale=get_locale())

    def get_price_text(self):
        if self.price == 0:
            return _("Free")
        else:
            return f"{self.get_price()}{self.get_currency_icon()}"

    def get_down_payment(self):
        if self.down_payment % 1 == 0:
            return int(self.down_payment)  # Return as an integer
        else:
            return self.down_payment  # Return the original float value

    def get_down_payment_text(self):
        if self.down_payment == 0:
            return f"Free"
        return f"{self.get_down_payment()}{self.get_currency_icon()}"

    def get_image_url(self):
        if not self.image:
            return ""
        return self.image.url

    def is_a_paid_service(self):
        return self.price > 0

    def accepts_down_payment(self):
        return self.down_payment > 0


class StaffMember(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))
    services_offered = models.ManyToManyField(
        Service,
        verbose_name=_("Services Offered"),
        help_text=_("Services that this staff member provides.")
    )
    slot_duration = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("Slot Duration"),
        help_text=_("Minimum time for an appointment in minutes, recommended 30.")
    )
    lead_time = models.TimeField(
        null=True, blank=True,
        verbose_name=_("Lead Time"),
        help_text=_("Time when the staff member starts working.")
    )
    finish_time = models.TimeField(
        null=True, blank=True,
        verbose_name=_("Finish Time"),
        help_text=_("Time when the staff member stops working.")
    )
    appointment_buffer_time = models.FloatField(
        blank=True, null=True,
        verbose_name=_("Appointment Buffer Time"),
        help_text=_("Time between now and the first available slot for the current day (doesn't affect tomorrow). "
                    "e.g: If you start working at 9:00 AM and the current time is 8:30 AM and you set it to 30 "
                    "minutes, the first available slot will be at 9:00 AM. If you set the appointment buffer time to "
                    "60 minutes, the first available slot will be at 9:30 AM.")
    )
    work_on_saturday = models.BooleanField(
        default=False,
        verbose_name=_("Work on Saturday"),
        help_text=_("Indicates whether this staff member works on Saturdays.")
    )
    work_on_sunday = models.BooleanField(
        default=False,
        verbose_name=_("Work on Sunday"),
        help_text=_("Indicates whether this staff member works on Sundays.")
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Staff Member")
        verbose_name_plural = _("Staff Members")
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.get_staff_member_name()}"

    def get_slot_duration(self):
        config = Config.objects.first()
        return self.slot_duration or (config.slot_duration if config else 0)

    def get_slot_duration_text(self):
        slot_duration = self.get_slot_duration()
        return convert_minutes_in_human_readable_format(slot_duration)

    def get_lead_time(self):
        config = Config.objects.first()
        return self.lead_time or (config.lead_time if config else None)

    def get_finish_time(self):
        config = Config.objects.first()
        return self.finish_time or (config.finish_time if config else None)

    def works_on_both_weekends_day(self):
        return self.work_on_saturday and self.work_on_sunday

    def get_staff_member_name(self):
        name_options = [
            getattr(self.user, 'get_full_name', lambda: '')(),
            f"{self.user.first_name} {self.user.last_name}",
            self.user.username,
            self.user.email,
            f"Staff Member {self.id}"
        ]
        return next((name.strip() for name in name_options if name.strip()), "Unknown")

    def get_staff_member_first_name(self):
        return self.user.first_name

    def get_non_working_days(self):
        non_working_days = []

        if not self.work_on_saturday:
            non_working_days.append(6)  # Saturday
        if not self.work_on_sunday:
            non_working_days.append(0)  # Sunday
        return non_working_days

    def get_weekend_days_worked_text(self):
        if self.work_on_saturday and self.work_on_sunday:
            return _("Saturday and Sunday")
        elif self.work_on_saturday:
            return _("Saturday")
        elif self.work_on_sunday:
            return _("Sunday")
        else:
            return _("None")

    def get_services_offered(self):
        return self.services_offered.all()

    def get_service_offered_text(self):
        return ', '.join([service.name for service in self.services_offered.all()])

    def get_service_is_offered(self, service_id):
        return self.services_offered.filter(id=service_id).exists()

    def get_appointment_buffer_time(self):
        config = Config.objects.first()
        return self.appointment_buffer_time or (config.appointment_buffer_time if config else 0)

    def get_appointment_buffer_time_text(self):
        # convert buffer time (which is in minutes) in day hours minutes if necessary
        return convert_minutes_in_human_readable_format(self.get_appointment_buffer_time())

    def get_days_off(self):
        return DayOff.objects.filter(staff_member=self)

    def get_working_hours(self):
        return self.workinghours_set.all()

    def update_upon_working_hours_deletion(self, day_of_week: int):
        if day_of_week == 6:
            self.work_on_saturday = False
        elif day_of_week == 0:
            self.work_on_sunday = False
        self.save()

    def is_working_day(self, day: int):
        return day not in self.get_non_working_days()


class AppointmentRequest(models.Model):
    """
    Represents an appointment request made by a client.

    Author: Adams Pierre David
    Since: 1.0.0
    """
    date = models.DateField(verbose_name=_("Date"), help_text=_("The date of the appointment request."))
    start_time = models.TimeField(
        verbose_name=_("Start Time"),
        help_text=_("The start time of the appointment request.")
    )
    end_time = models.TimeField(
        verbose_name=_("End Time"),
        help_text=_("The end time of the appointment request.")
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name=_("Service"))
    staff_member = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, verbose_name=_("Staff Member"))
    payment_type = models.CharField(
        max_length=4,
        choices=PAYMENT_TYPES,
        default='full',
        verbose_name=_("Payment Type")
    )
    id_request = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Request ID"))
    reschedule_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Reschedule Attempts"),
        help_text=_("Number of times this appointment has been rescheduled.")
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Appointment Request")
        verbose_name_plural = _("Appointment Requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['date', 'start_time']),
            models.Index(fields=['staff_member', 'date']),
        ]

    def __str__(self):
        return f"{self.date} - {self.start_time} to {self.end_time} - {self.service.name}"

    def clean(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time > self.end_time:
                raise ValidationError(_("Start time must be before end time"))
            if self.start_time == self.end_time:
                raise ValidationError(_("Start time and end time cannot be the same"))

        # Ensure the date is not in the past:
        if self.date and self.date < datetime.date.today():
            raise ValidationError(_("Date cannot be in the past"))

    def save(self, *args, **kwargs):
        # if no id_request is provided, generate one
        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{self.service.id}{generate_random_id()}"
        # start time should not be equal to end time
        if self.start_time == self.end_time:
            raise ValidationError(_("Start time and end time cannot be the same"))
        # date should not be in the past
        if self.date < datetime.date.today():
            raise ValidationError(_("Date cannot be in the past"))
        # duration should not exceed the service duration
        if time_difference(self.start_time, self.end_time) > self.service.duration:
            raise ValidationError(_("Duration cannot exceed the service duration"))
        return super().save(*args, **kwargs)

    def get_service_name(self):
        return self.service.name

    def get_service_price(self):
        return self.service.get_price()

    def get_service_down_payment(self):
        return self.service.get_down_payment()

    def get_service_image(self):
        return self.service.image

    def get_service_image_url(self):
        return self.service.get_image_url()

    def get_service_description(self):
        return self.service.description

    def get_id_request(self):
        return self.id_request

    def is_a_paid_service(self):
        return self.service.is_a_paid_service()

    def accepts_down_payment(self):
        return self.service.accepts_down_payment()

    def can_be_rescheduled(self):
        return self.reschedule_attempts < self.service.reschedule_limit

    def increment_reschedule_attempts(self):
        self.reschedule_attempts += 1
        self.save(update_fields=['reschedule_attempts'])

    def get_reschedule_history(self):
        return self.reschedule_histories.all().order_by('-created_at')


class AppointmentRescheduleHistory(models.Model):
    appointment_request = models.ForeignKey(
        'AppointmentRequest',
        on_delete=models.CASCADE, related_name='reschedule_histories',
        verbose_name=_("Appointment Request"),
        help_text=_("The appointment request made by a client.")
    )
    date = models.DateField(
        verbose_name=_("Date"),
        help_text=_("The previous date of the appointment before it was rescheduled.")
    )
    start_time = models.TimeField(
        verbose_name=_("Start Time"),
        help_text=_("The previous start time of the appointment before it was rescheduled.")
    )
    end_time = models.TimeField(
        verbose_name=_("End Time"),
        help_text=_("The previous end time of the appointment before it was rescheduled.")
    )
    staff_member = models.ForeignKey(
        StaffMember, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Staff Member"),
        help_text=_("The previous staff member of the appointment before it was rescheduled.")
    )
    reason_for_rescheduling = models.TextField(
        blank=True, null=True,
        verbose_name=_("Reason for Rescheduling"),
        help_text=_("Reason for the appointment reschedule.")
    )
    reschedule_status = models.CharField(
        max_length=10,
        choices=[('pending', _('Pending')), ('confirmed', _('Confirmed'))],
        default='pending',
        verbose_name=_("Reschedule Status"),
        help_text=_("Indicates the status of the reschedule action.")
    )
    id_request = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Request ID"),)

    # meta data
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("The date and time the reschedule was recorded.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("The date and time the reschedule was confirmed.")
    )

    class Meta:
        verbose_name = _("Appointment Reschedule History")
        verbose_name_plural = _("Appointment Reschedule Histories")
        ordering = ['-created_at']

    def __str__(self):
        return f"Reschedule history for {self.appointment_request} from {self.date}"

    def save(self, *args, **kwargs):
        # if no id_request is provided, generate one
        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{generate_random_id()}"
        # date should not be in the past
        if self.date < datetime.date.today():
            raise ValidationError(_("Date cannot be in the past"))
        try:
            datetime.datetime.strptime(str(self.date), '%Y-%m-%d')
        except ValueError:
            raise ValidationError(_("The date is not valid"))
        return super().save(*args, **kwargs)

    def still_valid(self):
        # if more than 5 minutes have passed, it is no longer valid
        now = timezone.now()  # This is offset-aware to match self.created_at
        delta = now - self.created_at
        return delta.total_seconds() < 300


class Appointment(models.Model):
    """
    Represents an appointment made by a client. It is created when the client confirms the appointment request.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Client"),
        help_text=_("The user who made the appointment request.")
    )
    appointment_request = models.OneToOneField(
        AppointmentRequest,
        on_delete=models.CASCADE,
        verbose_name=_("Appointment Request"),
        help_text=_("The appointment request made by the client.")
    )
    phone = PhoneNumberField(blank=True, verbose_name=_("Phone Number"))
    address = models.CharField(
        max_length=255,
        blank=True, null=True,
        default="",
        verbose_name=_("Address"),
        help_text=_("Does not have to be specific, just the city and the state")
    )
    want_reminder = models.BooleanField(
        default=False,
        verbose_name=_("Want Reminder"),
        help_text=_("Indicates whether the client wants a reminder for the appointment.")
    )
    additional_info = models.TextField(
        blank=True, null=True,
        verbose_name=_("Additional Info"),
        help_text=_("Any additional information the client wants to provide for the appointment.")
    )
    paid = models.BooleanField(
        default=False,
        verbose_name=_("Paid"),
        help_text=_("Indicates whether the appointment has been paid for.")
    )
    amount_to_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True, null=True,
        verbose_name=_("Amount to Pay"),
        help_text=_("The amount to be paid for the appointment. "
                    "If 0, it means the appointment is free or already paid.")
    )
    id_request = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Request ID"))

    # meta datas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount_to_pay__gte=0),
                name='positive_amount_to_pay'
            )
        ]

    def __str__(self):
        return f"{self.client} - " \
               f"{self.appointment_request.start_time.strftime('%Y-%m-%d %H:%M')} to " \
               f"{self.appointment_request.end_time.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if not hasattr(self, 'appointment_request'):
            raise ValidationError("Appointment request is required")

        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{self.appointment_request.id}{generate_random_id()}"
        if self.amount_to_pay is None or self.amount_to_pay == 0:
            payment_type = self.appointment_request.payment_type
            if payment_type == 'full':
                self.amount_to_pay = self.appointment_request.get_service_price()
            elif payment_type == 'down':
                self.amount_to_pay = self.appointment_request.get_service_down_payment()
            else:
                self.amount_to_pay = 0
        return super().save(*args, **kwargs)

    def get_client_name(self):
        if hasattr(self.client, 'get_full_name') and callable(getattr(self.client, 'get_full_name')):
            name = self.client.get_full_name()
        else:
            name = self.client.first_name
        return name

    def get_date(self):
        return self.appointment_request.date

    def get_start_time(self):
        return datetime.datetime.combine(self.get_date(), self.appointment_request.start_time)

    def get_end_time(self):
        return datetime.datetime.combine(self.get_date(), self.appointment_request.end_time)

    def get_service(self):
        return self.appointment_request.service

    def get_service_name(self):
        return self.appointment_request.get_service_name()

    def get_service_duration(self):
        return self.appointment_request.service.get_duration()

    def get_staff_member_name(self):
        if not self.appointment_request.staff_member:
            return ""
        return self.appointment_request.staff_member.get_staff_member_name()

    def get_staff_member(self):
        return self.appointment_request.staff_member

    def get_service_price(self):
        return self.appointment_request.get_service_price()

    def get_service_down_payment(self):
        return self.appointment_request.get_service_down_payment()

    def get_service_img(self):
        return self.appointment_request.get_service_image()

    def get_service_img_url(self):
        return self.appointment_request.get_service_image_url()

    def get_service_description(self):
        return self.appointment_request.get_service_description()

    def get_appointment_date(self):
        return self.appointment_request.date

    def is_paid(self):
        if self.get_service_price() == 0 or (self.amount_to_pay is not None and self.amount_to_pay == 0):
            return True
        return self.paid

    def service_is_paid(self):
        return self.get_service_price() != 0

    def is_paid_text(self):
        return _("Yes") if self.is_paid() else _("No")

    def get_appointment_amount_to_pay(self):
        # Check if the decimal part is 0
        if self.amount_to_pay % 1 == 0:
            return int(self.amount_to_pay)  # Return as an integer
        else:
            return self.amount_to_pay  # Return the original float value

    def get_appointment_amount_to_pay_text(self):
        if self.amount_to_pay == 0 and self.get_service_price() == 0:
            return _("Free")
        return f"{self.get_appointment_amount_to_pay()}{self.get_service().get_currency_icon()}"

    def get_appointment_currency(self):
        return self.appointment_request.service.currency

    def wants_reminder_text(self):
        return _("Yes") if self.want_reminder else _("No")

    def get_appointment_id_request(self):
        return self.id_request

    def set_appointment_paid_status(self, status: bool):
        self.paid = status
        self.save()

    def get_absolute_url(self, request=None):
        url = reverse('appointment:display_appointment', args=[str(self.id)])
        return request.build_absolute_uri(url) if request else url

    def get_background_color(self):
        return self.appointment_request.service.background_color

    @staticmethod
    def is_valid_date(appt_date, start_time, staff_member, current_appointment_id, weekday: str):
        weekday_num = get_weekday_num(weekday)
        sm_name = staff_member.get_staff_member_name()

        # Check if the staff member works on the given day
        try:
            working_hours = WorkingHours.objects.get(staff_member=staff_member, day_of_week=weekday_num)
        except WorkingHours.DoesNotExist:
            message = _("{staff_member} does not work on this day.").format(staff_member=sm_name)
            return False, message

        # Check if the start time falls within the staff member's working hours
        if not (working_hours.start_time <= start_time.time() <= working_hours.end_time):
            message = _("The appointment start time is outside of {staff_member}'s working hours.").format(
                staff_member=sm_name)
            return False, message

        # Check if the staff member already has an appointment on the given date and time
        # Using prefetch_related to reduce DB hits when accessing related objects
        appt_list = Appointment.objects.filter(appointment_request__staff_member=staff_member,
                                               appointment_request__date=appt_date).exclude(
            id=current_appointment_id).prefetch_related('appointment_request')
        for appt in appt_list:
            if appt.appointment_request.start_time <= start_time.time() <= appt.appointment_request.end_time:
                message = _("{staff_member} already has an appointment at this time.").format(staff_member=sm_name)
                return False, message

        # Check if the staff member has a day off on the appointment's date
        days_off = DayOff.objects.filter(staff_member=staff_member, start_date__lte=appt_date, end_date__gte=appt_date)
        if days_off.exists():
            message = _("{staff_member} has a day off on this date.").format(staff_member=sm_name)
            return False, message

        return True, ""

    def is_owner(self, staff_user_id):
        return self.appointment_request.staff_member.user.id == staff_user_id

    def to_dict(self):
        return {
            "id": self.id,
            "client_name": self.get_client_name(),
            "client_email": self.client.email,
            "start_time": self.appointment_request.start_time.strftime('%Y-%m-%d %H:%M'),
            "end_time": self.appointment_request.end_time.strftime('%Y-%m-%d %H:%M'),
            "service_name": self.appointment_request.service.name,
            "address": self.address,
            "want_reminder": self.want_reminder,
            "additional_info": self.additional_info,
            "paid": self.paid,
            "amount_to_pay": self.amount_to_pay,
            "id_request": self.id_request,
        }


class Config(models.Model):
    """
    Represents configuration settings for the appointment system. There can only be one Config object in the database.
    If you want to change the settings, you must edit the existing Config object.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    slot_duration = models.PositiveIntegerField(
        null=True,
        verbose_name=_("Slot Duration"),
        help_text=_("Minimum time for an appointment in minutes, recommended 30."),
    )
    lead_time = models.TimeField(
        null=True,
        verbose_name=_("Lead Time"),
        help_text=_("Time when we start working."),
    )
    finish_time = models.TimeField(
        null=True,
        verbose_name=_("Finish Time"),
        help_text=_("Time when we stop working."),
    )
    appointment_buffer_time = models.FloatField(
        null=True,
        verbose_name=_("Appointment Buffer Time"),
        help_text=_("Time between now and the first available slot for the current day (doesn't affect tomorrow)."),
    )
    website_name = models.CharField(
        max_length=255,
        default="",
        verbose_name=_("Website Name"),
        help_text=_("Name of your website."),
    )
    app_offered_by_label = models.CharField(
        max_length=255,
        default=_("Offered by"),
        verbose_name=_("`Offered by` Label"),
        help_text=_("Label for `Offered by` on the appointment page")
    )
    default_reschedule_limit = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Default Reschedule Limit"),
        help_text=_("Default maximum number of times an appointment can be rescheduled across all services.")
    )
    allow_staff_change_on_reschedule = models.BooleanField(
        default=True,
        verbose_name=_("Allow Staff Change on Reschedule"),
        help_text=_("Allows clients to change the staff member when rescheduling an appointment.")
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Config")
        verbose_name_plural = _("Configs")
        ordering = ['-created_at']

    def clean(self):
        if Config.objects.exists() and not self.pk:
            raise ValidationError(_("You can only create one Config object"))
        if self.lead_time is not None and self.finish_time is not None:
            if self.lead_time >= self.finish_time:
                raise ValidationError(_("Lead time must be before finish time"))
        if self.appointment_buffer_time is not None and self.appointment_buffer_time < 0:
            raise ValidationError(_("Appointment buffer time cannot be negative"))
        if self.slot_duration is not None and self.slot_duration <= 0:
            raise ValidationError(_("Slot duration must be greater than 0"))

    def save(self, *args, **kwargs):
        self.clean()
        self.pk = 1
        super(Config, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_instance(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Config {self.pk}: slot_duration={self.slot_duration}, lead_time={self.lead_time}, " \
               f"finish_time={self.finish_time}"


class PaymentInfo(models.Model):
    """
    Represents payment information for an appointment.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, verbose_name=_("Appointment"))

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Payment Info")
        verbose_name_plural = _("Payment Infos")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.appointment.get_service_name()} - {self.appointment.get_service_price()}"

    def __repr__(self):
        return f"{self.appointment.get_service_name()} - {self.appointment.get_service_price()}"

    def get_id_request(self):
        return self.appointment.get_appointment_id_request()

    def get_amount_to_pay(self):
        return self.appointment.get_appointment_amount_to_pay()

    def get_currency(self):
        return self.appointment.get_appointment_currency()

    def get_name(self):
        return self.appointment.get_service_name()

    def get_img_url(self):
        return self.appointment.get_service_img_url()

    def set_paid_status(self, status: bool):
        self.appointment.set_appointment_paid_status(status)

    def get_user_name(self):
        return self.appointment.client.first_name

    def get_user_email(self):
        return self.appointment.client.email


class EmailVerificationCode(models.Model):
    """
    Represents an email verification code for a user when the email already exists in the database.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))
    code = models.CharField(
        max_length=6,
        verbose_name=_("Verification Code"),
        help_text=_("The verification code sent to the user's email.")
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Email Verification Code")
        verbose_name_plural = _("Email Verification Codes")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code}"

    @classmethod
    def generate_code(cls, user):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        verification_code = cls(user=user, code=code)
        verification_code.save()
        return code

    def check_code(self, code):
        return self.code == code


class PasswordResetToken(models.Model):
    """
    Represents a password reset token for users.

    Author: Adams Pierre David
    Version: 3.x.x
    Since: 3.x.x
    """

    class TokenStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        VERIFIED = 'verified', _('Verified')
        INVALIDATED = 'invalidated', _('Invalidated')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name=_("User"),
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_("Token"))
    expires_at = models.DateTimeField(verbose_name=_("Expires At"))
    status = models.CharField(
        max_length=11,
        choices=TokenStatus.choices,
        default=TokenStatus.ACTIVE,
        verbose_name=_("Status"),
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Password Reset Token")
        verbose_name_plural = _("Password Reset Tokens")
        ordering = ['-created_at']

    def __str__(self):
        return f"Password reset token for {self.user} [{self.token} status: {self.status} expires at {self.expires_at}]"

    @property
    def is_expired(self):
        """Checks if the token has expired."""
        return timezone.now() >= self.expires_at

    @property
    def is_verified(self):
        """Checks if the token has been verified."""
        return self.status == self.TokenStatus.VERIFIED

    @property
    def is_active(self):
        """Checks if the token is still active."""
        return self.status == self.TokenStatus.ACTIVE

    @property
    def is_invalidated(self):
        """Checks if the token has been invalidated."""
        return self.status == self.TokenStatus.INVALIDATED

    @classmethod
    def create_token(cls, user, expiration_minutes=60):
        """
        Generates a new token for the user with a specified expiration time.
        Before creating a new token, invalidate all previous active tokens by marking them as invalidated.
        """
        cls.objects.filter(user=user, expires_at__gte=timezone.now(), status=cls.TokenStatus.ACTIVE).update(
            status=cls.TokenStatus.INVALIDATED)
        expires_at = timezone.now() + timezone.timedelta(minutes=expiration_minutes)
        token = cls.objects.create(user=user, expires_at=expires_at, status=cls.TokenStatus.ACTIVE)
        return token

    def mark_as_verified(self):
        """
        Marks the token as verified.
        """
        self.status = self.TokenStatus.VERIFIED
        self.save(update_fields=['status'])

    @classmethod
    def verify_token(cls, user, token):
        """
        Verifies if the provided token is valid and belongs to the given user.
        Additionally, checks if the token has not been marked as verified.
        """
        try:
            return cls.objects.get(user=user, token=token, expires_at__gte=timezone.now(),
                                   status=cls.TokenStatus.ACTIVE)
        except cls.DoesNotExist:
            return None


class DayOff(models.Model):
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, verbose_name=_("Staff Member"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Description"))

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Day Off")
        verbose_name_plural = _("Days Off")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.start_date} to {self.end_date} - {self.description if self.description else 'Day off'}"

    def clean(self):
        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                raise ValidationError(_("Start date must be before end date"))

    def is_owner(self, user_id):
        return self.staff_member.user.id == user_id


class WorkingHours(models.Model):
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, verbose_name=_("Staff Member"))
    day_of_week = models.PositiveIntegerField(choices=DAYS_OF_WEEK, verbose_name=_("Day of Week"))
    start_time = models.TimeField(verbose_name=_("Start Time"))
    end_time = models.TimeField(verbose_name=_("End Time"))

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Working Hour")
        verbose_name_plural = _("Working Hours")
        ordering = ['day_of_week', 'start_time']
        unique_together = ['staff_member', 'day_of_week']
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_time__lt=models.F('end_time')),
                name='start_time_before_end_time'
            )
        ]

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.start_time} to {self.end_time}"

    def save(self, *args, **kwargs):
        # Call the original save method
        super(WorkingHours, self).save(*args, **kwargs)

        # Update staff member's weekend working status
        if self.day_of_week == '6' or self.day_of_week == 6:  # Saturday
            self.staff_member.work_on_saturday = True
        elif self.day_of_week == '0' or self.day_of_week == 0:  # Sunday
            self.staff_member.work_on_sunday = True
        self.staff_member.save()

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")

    def get_start_time(self):
        return self.start_time

    def get_end_time(self):
        return self.end_time

    def get_day_of_week_str(self):
        # return the name of the day instead of the integer
        return self.get_day_of_week_display()

    def is_owner(self, user_id):
        return self.staff_member.user.id == user_id
