import datetime
import uuid

from django.utils.translation import to_locale, get_language

from appointment.settings import APPOINTMENT_SLOT_DURATION, APPOINTMENT_LEAD_TIME, APPOINTMENT_FINISH_TIME


class Utility:
    """
    Utility class containing useful static methods for general-purpose tasks.
    """

    def __init__(self):
        pass

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
        else:
            start_hour, start_minute = APPOINTMENT_LEAD_TIME
            start_time = datetime.datetime.combine(date, datetime.time(hour=start_hour, minute=start_minute))

            finish_hour, finish_minute = APPOINTMENT_FINISH_TIME
            end_time = datetime.datetime.combine(date, datetime.time(hour=finish_hour, minute=finish_minute))

            slot_duration = datetime.timedelta(minutes=APPOINTMENT_SLOT_DURATION)

        slots = []
        while start_time <= end_time:
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
