# appointment/utils/ics_utils.py

import datetime
import logging

from icalendar import Calendar, Event, vRecur

from appointment.models import RecurringAppointment
from appointment.utils.db_helpers import Appointment, get_website_name

logger = logging.getLogger(__name__)


def generate_ics_file(appointment: Appointment):
    company_name = get_website_name()

    cal = Calendar()
    cal.add('prodid', f"-//{company_name}//DjangoAppointmentSystem//EN")
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', appointment.get_service_name())
    event.add('dtstart', appointment.get_start_time())
    event.add('dtend', appointment.get_end_time())
    event.add('dtstamp', datetime.datetime.now())
    event.add('location', appointment.address)
    event.add('description', appointment.additional_info)

    organizer = f"MAILTO:{appointment.appointment_request.staff_member.user.email}"
    event.add('organizer', organizer)

    attendee = f"MAILTO:{appointment.client.email}"
    event.add('attendee', attendee)

    # Add recurrence rule if applicable
    try:
        recurring_info = RecurringAppointment.objects.get(appointment_request=appointment.appointment_request)

        if recurring_info.recurrence_rule:
            # Convert the django-recurrence object to RRULE string
            rrule_string = str(recurring_info.recurrence_rule)
            logger.debug(f"Recurrence rule string: {rrule_string}")

            # Remove RRULE: prefix if present
            if rrule_string.startswith('RRULE:'):
                rrule_content = rrule_string[6:]
            else:
                rrule_content = rrule_string

            if rrule_content.strip():
                # Parse the RRULE string into a dictionary that icalendar can understand
                rrule_dict = {}
                parts = rrule_content.split(';')

                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        if key == 'FREQ':
                            rrule_dict['FREQ'] = [value]
                        elif key == 'BYDAY':
                            rrule_dict['BYDAY'] = value.split(',')
                        elif key == 'UNTIL':
                            # Parse the UNTIL date - DON'T put it in a list
                            until_dt = datetime.datetime.strptime(value, '%Y%m%dT%H%M%SZ')
                            rrule_dict['UNTIL'] = until_dt  # Single datetime object, not a list
                        elif key == 'INTERVAL':
                            rrule_dict['INTERVAL'] = [int(value)]

                # Create vRecur object
                if rrule_dict:
                    rrule_obj = vRecur(rrule_dict)
                    event.add('rrule', rrule_obj)
                    logger.debug(f"Added RRULE to appointment {appointment.id}: {rrule_dict}")
                else:
                    logger.warning(f"Could not parse RRULE for appointment {appointment.id}")
            else:
                logger.warning(f"Empty RRULE content for appointment {appointment.id}")

    except RecurringAppointment.DoesNotExist:
        logger.debug(f"No recurring info for appointment {appointment.id}, not adding RRULE.")
    except Exception as e:
        logger.error(f"Error generating RRULE for ICS for appointment {appointment.id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

    cal.add_component(event)
    return cal.to_ical()
