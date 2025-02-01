# appointment/utils/ics_utils.py

from datetime import datetime

from icalendar import Calendar, Event

from appointment.utils.db_helpers import Appointment, get_website_name


def generate_ics_file(appointment: Appointment):
    company_name = get_website_name()

    cal = Calendar()
    cal.add('prodid', f"-//{company_name}//DjangoAppointmentSystem//EN")
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', appointment.get_service_name())
    event.add('dtstart', appointment.get_start_time())
    event.add('dtend', appointment.get_end_time())
    event.add('dtstamp', datetime.now())
    event.add('location', appointment.address)
    event.add('description', appointment.additional_info)

    organizer = f"MAILTO:{appointment.appointment_request.staff_member.user.email}"
    event.add('organizer', organizer)

    attendee = f"MAILTO:{appointment.client.email}"
    event.add('attendee', attendee)

    cal.add_component(event)
    return cal.to_ical()
