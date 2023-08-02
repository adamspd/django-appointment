import datetime
import uuid

from django.apps import apps
from django.utils.translation import gettext as _
from django.utils.translation import to_locale, get_language

from appointment.settings import APPOINTMENT_SLOT_DURATION, APPOINTMENT_LEAD_TIME, APPOINTMENT_FINISH_TIME, \
    APP_TIME_ZONE, APPOINTMENT_BUFFER_TIME, APPOINTMENT_WEBSITE_NAME, APPOINTMENT_PAYMENT_URL, APPOINTMENT_CLIENT_MODEL


class Utility:
    """
    Utility class containing useful static methods for general-purpose tasks.
    """

    @staticmethod
    def is_ajax(request):
        """
        Check if the request is an AJAX request.

        :param request: HttpRequest object
        :return: bool, True if the request is an AJAX request, False otherwise
        """
        return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    @staticmethod
    def generate_random_id():
        """
        Generate a random UUID and return it as a hexadecimal string.

        :return: str, the randomly generated UUID as a hex string
        """
        return uuid.uuid4().hex

    @staticmethod
    def get_timestamp():
        """
        Get the current timestamp as a string without the decimal part.

        :return: str, the current timestamp
        """
        timestamp = str(datetime.datetime.now().timestamp())
        return timestamp.replace('.', '')

    @staticmethod
    def get_available_slots(date, appointments):
        """
        Calculate the available time slots for a given date and a list of appointments.

        :param date: date, the date for which to calculate the available slots
        :param appointments: list, a list of Appointment objects
        :return: list, a list of available time slots as strings in the format '%I:%M %p'
        """
        from appointment.models import Config
        config = Config.objects.first()

        if config:
            start_time = datetime.datetime.combine(date, datetime.time(hour=config.lead_time.hour,
                                                                       minute=config.lead_time.minute))
            end_time = datetime.datetime.combine(date, datetime.time(hour=config.finish_time.hour,
                                                                     minute=config.finish_time.minute))
            slot_duration = datetime.timedelta(minutes=config.slot_duration)
            buff_time = datetime.timedelta(hours=config.appointment_buffer_time)
        else:
            start_hour, start_minute = APPOINTMENT_LEAD_TIME
            start_time = datetime.datetime.combine(date, datetime.time(hour=start_hour, minute=start_minute))

            finish_hour, finish_minute = APPOINTMENT_FINISH_TIME
            end_time = datetime.datetime.combine(date, datetime.time(hour=finish_hour, minute=finish_minute))

            slot_duration = datetime.timedelta(minutes=APPOINTMENT_SLOT_DURATION)
            buff_time = datetime.timedelta(hours=APPOINTMENT_BUFFER_TIME)

        # Add a buffer of 3 hours to the current time only if the date is today
        now = datetime.datetime.now()
        buffer_time = now + buff_time if date == now.date() else now
        slots = []
        while start_time <= end_time:
            if start_time >= buffer_time:
                slots.append(start_time)
            start_time += slot_duration
        for appointment in appointments:
            appointment_start_time = appointment.get_start_time()
            appointment_end_time = appointment.get_end_time()
            slots = [slot for slot in slots if not (appointment_start_time <= slot <= appointment_end_time)]
        return [slot.strftime('%I:%M %p') for slot in slots]

    @staticmethod
    def get_locale():
        """
        Get the current locale based on the user's language settings.

        :return: str, the current locale as a string
        """
        local = to_locale(get_language())
        if local == 'en':
            return local
        elif local == 'en_US':
            return 'en'
        elif local == 'fr':
            return local
        elif local == 'fr_FR':
            return 'fr'
        else:
            return 'en'

    @staticmethod
    def get_current_year():
        """
        Get the current year as an integer.

        :return: int, the current year
        """
        return datetime.datetime.now().year

    @staticmethod
    def get_timezone_txt():
        """
        Get the current timezone as a string.

        :return: str, the current timezone
        """
        tmz = APP_TIME_ZONE
        timezone_map = {
            'UTC': 'Universal Time Coordinated (UTC)',
            'US/Eastern': 'Eastern Daylight Time (US & Canada)',
            'US/Central': 'Central Time (US & Canada)',
            'US/Mountain': 'Mountain Time (US & Canada)',
            'US/Pacific': 'Pacific Time (US & Canada)',
            'US/Alaska': 'Alaska Time (US & Canada)',
            'US/Hawaii': 'Hawaii Time (US & Canada)',
            'Europe/Paris': 'Paris Time (Europe)',
            'Europe/London': 'London Time (Europe)'
        }
        return timezone_map.get(tmz, 'Universal Time Coordinated (UTC)')

    @staticmethod
    def get_timezone():
        return APP_TIME_ZONE

    @staticmethod
    def convert_str_to_date(date_str):
        """
        Convert a date string to a datetime.date object.

        :param date_str: str, the date string in the format '%Y-%m-%d'
        :return: datetime.date, the converted date
        """
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

    @staticmethod
    def get_website_name():
        """
        Get the website name from the settings file.

        :return: str, the website name
        """
        from appointment.models import Config

        config = Config.objects.first()

        if config and config.website_name != "":
            return config.website_name
        return APPOINTMENT_WEBSITE_NAME

    @staticmethod
    def get_appointment_slot_duration():
        """
        Get the appointment slot duration from the settings file.

        :return: int, the appointment slot duration
        """
        from appointment.models import Config

        config = Config.objects.first()

        if config and config.slot_duration:
            return config.slot_duration
        return APPOINTMENT_SLOT_DURATION

    @staticmethod
    def get_appointment_lead_time():
        """
        Get the appointment lead time from the settings file.

        :return: int, the appointment lead time
        """
        from appointment.models import Config

        config = Config.objects.first()

        if config and config.lead_time:
            return config.lead_time
        return APPOINTMENT_LEAD_TIME

    @staticmethod
    def get_appointment_finish_time():
        """
        Get the appointment finish time from the settings file.

        :return: int, the appointment finish time
        """
        from appointment.models import Config

        config = Config.objects.first()

        if config and config.finish_time:
            return config.finish_time
        return APPOINTMENT_FINISH_TIME

    @staticmethod
    def get_appointment_buffer_time():
        """
        Get the appointment buffer time from the settings file.

        :return: int, the appointment buffer time
        """
        from appointment.models import Config

        config = Config.objects.first()

        if config and config.appointment_buffer_time:
            return config.appointment_buffer_time
        return APPOINTMENT_BUFFER_TIME

    @staticmethod
    def get_finish_button_text(service) -> str:
        """
        Check if a service is free.

        :param service: Service, the service to check
        :return: bool, True if the service is free, False otherwise
        """
        print("APPOINTMENT_PAYMENT_URL", APPOINTMENT_PAYMENT_URL)
        print("service.is_a_paid_service()", service.is_a_paid_service())
        if service.is_a_paid_service() and APPOINTMENT_PAYMENT_URL:
            return _("Pay Now")
        return _("Finish")

    @staticmethod
    def get_user_model():
        """
        Get the client models from the settings file.

        :return: The client models
        """
        return apps.get_model(APPOINTMENT_CLIENT_MODEL)
