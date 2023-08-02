import datetime
import random
import string

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MinLengthValidator, MaxLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from appointment.utils import Utility
from .settings import APPOINTMENT_CLIENT_MODEL

phone_regex = RegexValidator(
    regex=r'^\d{10}$',
    message=_("Phone number must not contain spaces, letters, parentheses or dashes. It must contain 10 digits.")
)

PAYMENT_TYPES = (
    ('full', _('Full payment')),
    ('down', _('Down payment')),
)


class Service(models.Model):
    """
    Represents a service provided by the appointment system.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration = models.DurationField()
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    down_payment = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD', validators=[MaxLengthValidator(3), MinLengthValidator(3)])
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

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
            parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds:
            parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

        return ' '.join(parts)

    def get_price(self):
        return self.price

    def get_price_text(self):
        if self.price == 0:
            return "Free"
        else:
            return f"{self.price} {self.currency}"

    def get_down_payment(self):
        return self.down_payment

    def get_currency(self):
        return self.currency

    def get_image(self):
        return self.image

    def get_image_url(self):
        return self.image.url

    def get_created_at(self):
        return self.created_at

    def get_updated_at(self):
        return self.updated_at

    def is_a_paid_service(self):
        return self.price > 0

    def accepts_down_payment(self):
        return self.down_payment > 0


class AppointmentRequest(models.Model):
    """
    Represents an appointment request made by a client.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=4, choices=PAYMENT_TYPES, default='full')
    id_request = models.CharField(max_length=100, blank=True, null=True)

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {self.start_time} to {self.end_time} - {self.service.name}"

    def clean(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("Start time must be before end time")

    def save(self, *args, **kwargs):
        if self.id_request is None:
            self.id_request = f"{Utility.get_timestamp()}{self.service.id}{Utility.generate_random_id()}"
        return super().save(*args, **kwargs)

    def get_date(self):
        return self.date

    def get_start_time(self):
        return self.start_time

    def get_end_time(self):
        return self.end_time

    def get_service(self):
        return self.service

    def get_service_name(self):
        return self.service.get_name()

    def get_service_duration(self):
        return self.service.get_duration()

    def get_service_price(self):
        return self.service.get_price()

    def get_service_down_payment(self):
        return self.service.get_down_payment()

    def get_service_image(self):
        return self.service.get_image()

    def get_service_image_url(self):
        return self.service.get_image_url()

    def get_service_description(self):
        return self.service.get_description()

    def get_id_request(self):
        return self.id_request

    def is_a_paid_service(self):
        return self.service.is_a_paid_service()

    def accepts_down_payment(self):
        return self.service.accepts_down_payment()

    def get_payment_type(self):
        return self.payment_type

    def get_created_at(self):
        return self.created_at

    def get_updated_at(self):
        return self.updated_at


class Appointment(models.Model):
    """
    Represents an appointment made by a client. It is created when the client confirms the appointment request.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    client = models.ForeignKey(APPOINTMENT_CLIENT_MODEL, on_delete=models.CASCADE)
    appointment_request = models.OneToOneField(AppointmentRequest, on_delete=models.CASCADE)
    phone = models.CharField(validators=[phone_regex], max_length=10, blank=True, null=True, default="",
                             help_text=_("Phone number must not contain spaces, letters, parentheses or "
                                         "dashes. It must contain 10 digits."))
    address = models.CharField(max_length=255, blank=True, null=True, default="",
                               help_text=_("Does not have to be specific, just the city and the state"))
    want_reminder = models.BooleanField(default=False)
    additional_info = models.TextField(blank=True, null=True)
    paid = models.BooleanField(default=False)
    amount_to_pay = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    id_request = models.CharField(max_length=100, blank=True, null=True)

    # meta datas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} - " \
               f"{self.appointment_request.start_time.strftime('%Y-%m-%d %H:%M')} to " \
               f"{self.appointment_request.end_time.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if self.id_request is None:
            self.id_request = f"{Utility.get_timestamp()}{self.appointment_request.id}{Utility.generate_random_id()}"
        if self.amount_to_pay is None or self.amount_to_pay == 0:
            payment_type = self.appointment_request.get_payment_type()
            if payment_type == 'full':
                self.amount_to_pay = self.appointment_request.get_service_price()
            elif payment_type == 'down':
                self.amount_to_pay = self.appointment_request.get_service_down_payment()
            else:
                self.amount_to_pay = 0
        return super().save(*args, **kwargs)

    def get_client(self):
        return self.client

    def get_start_time(self):
        return datetime.datetime.combine(self.appointment_request.get_date(), self.appointment_request.get_start_time())

    def get_end_time(self):
        return datetime.datetime.combine(self.appointment_request.get_date(), self.appointment_request.get_end_time())

    def get_service_name(self):
        return self.appointment_request.get_service_name()

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

    def get_phone(self):
        return self.phone

    def get_address(self):
        return self.address

    def get_want_reminder(self):
        return self.want_reminder

    def get_additional_info(self):
        return self.additional_info

    def is_paid(self):
        return self.paid

    def get_appointment_amount_to_pay(self):
        return self.amount_to_pay

    def get_appointment_currency(self):
        return self.appointment_request.get_service().get_currency()

    def get_appointment_id_request(self):
        return self.id_request

    def get_created_at(self):
        return self.created_at

    def get_updated_at(self):
        return self.updated_at

    def set_appointment_paid_status(self, status: bool):
        self.paid = status
        self.save()


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
        help_text=_("Minimum time for an appointment in minutes, recommended 30."),
    )
    lead_time = models.TimeField(
        null=True,
        help_text=_("Time when we start working."),
    )
    finish_time = models.TimeField(
        null=True,
        help_text=_("Time when we stop working."),
    )
    appointment_buffer_time = models.FloatField(
        null=True,
        help_text=_("Time between now and the first available slot for the current day (doesn't affect tomorrow)."),
    )
    website_name = models.CharField(
        max_length=255,
        default="",
        help_text=_("Name of your website."),
    )

    def clean(self):
        if Config.objects.exists() and not self.pk:
            raise ValidationError(_("You can only create one Config object"))
        if self.lead_time is not None and self.finish_time is not None:
            if self.lead_time >= self.finish_time:
                raise ValidationError(_("Lead time must be before finish time"))

    def save(self, *args, **kwargs):
        self.clean()
        super(Config, self).save(*args, **kwargs)

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
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
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
        return self.appointment.get_client().first_name

    def get_user_email(self):
        return self.appointment.get_client().email


class EmailVerificationCode(models.Model):
    """
    Represents an email verification code for a user when the email already exists in the database.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.1.0
    """
    user = models.ForeignKey(APPOINTMENT_CLIENT_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code}"

    @classmethod
    def generate_code(cls, user):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        verification_code = cls(user=user, code=code)
        verification_code.save()
        return code
