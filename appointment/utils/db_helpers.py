# db_helpers.py
# Path: appointment/utils/db_helpers.py

"""
Author: Adams Pierre David
Since: 2.0.0
"""

import datetime
from typing import Optional
from urllib.parse import urlparse

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import schedule

from appointment.logger_config import logger
from appointment.settings import (
    APPOINTMENT_BUFFER_TIME, APPOINTMENT_FINISH_TIME, APPOINTMENT_LEAD_TIME, APPOINTMENT_PAYMENT_URL,
    APPOINTMENT_SLOT_DURATION, APPOINTMENT_WEBSITE_NAME
)
from appointment.utils.date_time import combine_date_and_time, get_weekday_num

Appointment = apps.get_model('appointment', 'Appointment')
AppointmentRequest = apps.get_model('appointment', 'AppointmentRequest')
WorkingHours = apps.get_model('appointment', 'WorkingHours')
DayOff = apps.get_model('appointment', 'DayOff')
PaymentInfo = apps.get_model('appointment', 'PaymentInfo')
StaffMember = apps.get_model('appointment', 'StaffMember')
Config = apps.get_model('appointment', 'Config')
Service = apps.get_model('appointment', 'Service')
EmailVerificationCode = apps.get_model('appointment', 'EmailVerificationCode')
AppointmentRescheduleHistory = apps.get_model('appointment', 'AppointmentRescheduleHistory')


def calculate_slots(start_time, end_time, buffer_time, slot_duration):
    """Calculate the available slots between the given start and end times using the given buffer time and slot duration

    :param start_time: The start time.
    :param end_time: The end time.
    :param buffer_time: The buffer time.
    :param slot_duration: The duration of each slot.
    :return: A list of available slots.
    """
    slots = []
    buffer_time = buffer_time.replace(tzinfo=None)
    while start_time + slot_duration <= end_time:
        if start_time >= buffer_time:
            slots.append(start_time)
        start_time += slot_duration
    return slots


def calculate_staff_slots(date, staff_member):
    """Calculate the available slots for the given staff member on the given date.

    :param date: The date to calculate the slots for.
    :param staff_member: The staff member to calculate the slots for.
    :return: A list of available slots.
    """
    # Convert the times to datetime objects
    weekday_num = get_weekday_num_from_date(date)
    if not is_working_day(staff_member, weekday_num):
        return []
    staff_member_start_time = get_staff_member_start_time(staff_member, date)
    start_time = datetime.datetime.combine(date, staff_member_start_time)
    end_time = datetime.datetime.combine(date, get_staff_member_end_time(staff_member, date))

    # Convert the buffer duration in minutes to a timedelta object
    buffer_duration_minutes = get_staff_member_buffer_time(staff_member, date)
    buffer_duration = datetime.timedelta(minutes=buffer_duration_minutes)
    buffer_time_init = datetime.datetime.combine(date, staff_member_start_time)
    buffer_time = buffer_time_init + buffer_duration

    # Convert slot duration to a timedelta object
    slot_duration_minutes = get_staff_member_slot_duration(staff_member, date)
    slot_duration = datetime.timedelta(minutes=slot_duration_minutes)

    return calculate_slots(start_time, end_time, buffer_time, slot_duration)


def check_day_off_for_staff(staff_member, date) -> bool:
    """Check if the given staff member is off on the given date.
    :param staff_member: The staff member to check.
    :param date: The date to check.
    """
    return DayOff.objects.filter(staff_member=staff_member, start_date__lte=date, end_date__gte=date).exists()


def create_and_save_appointment(ar, client_data: dict, appointment_data: dict, request):
    """Create and save a new appointment based on the provided appointment request and client data.

    :param ar: The appointment request associated with the new appointment.
    :param client_data: The data of the client making the appointment.
    :param appointment_data: Additional data for the appointment, including phone number, address, etc.
    :param request: The request object.
    :return: The newly created appointment.
    """
    user = get_user_by_email(client_data['email'])
    appointment = Appointment.objects.create(
            client=user, appointment_request=ar,
            **appointment_data
    )
    appointment.save()
    logger.info(f"New appointment created: {appointment.to_dict()}")
    if appointment.want_reminder:
        schedule_email_reminder(appointment, request)
    return appointment


def schedule_email_reminder(appointment, request, appointment_datetime=None):
    """Schedule an email reminder for the given appointment."""
    # Check if the Django-Q cluster is running
    from appointment.settings import check_q_cluster
    if not check_q_cluster():
        logger.warning("Django-Q cluster is not running. Email reminder will not be scheduled.")
        return

    # Calculate reminder datetime if not provided
    if appointment_datetime is None:
        appointment_datetime = combine_date_and_time(appointment.appointment_request.date,
                                                     appointment.appointment_request.start_time)
    if timezone.is_naive(appointment_datetime):
        appointment_datetime = timezone.make_aware(appointment_datetime)

    reminder_datetime = appointment_datetime - datetime.timedelta(days=1)

    ar_id_request = appointment.appointment_request.get_id_request()
    relative_reschedule_url = reverse('appointment:prepare_reschedule_appointment', args=[ar_id_request])
    reschedule_link = get_absolute_url_(relative_reschedule_url, request)

    logger.info(f"Scheduling email reminder for appointment {appointment.id} at {reminder_datetime}")

    # Schedule the email reminder task with Django-Q
    schedule('appointment.tasks.send_email_reminder',
             to_email=appointment.client.email,
             name=f"reminder_{appointment.id_request}",
             first_name=appointment.client.first_name,
             reschedule_link=reschedule_link,
             appointment_id=appointment.id,
             schedule_type=Schedule.ONCE,  # Use Schedule.ONCE for a one-time task
             next_run=reminder_datetime)


def update_appointment_reminder(appointment, new_date, new_start_time, request, want_reminder=None):
    """
    Updates or cancels the appointment reminder based on changes to the start time or date,
    and the user's preference for receiving a reminder.
    """
    # Convert new date and time strings to datetime objects for comparison
    new_datetime = combine_date_and_time(new_date, new_start_time)

    existing_datetime = combine_date_and_time(appointment.appointment_request.date,
                                              appointment.appointment_request.start_time)

    # Ensure new_datetime is timezone-aware
    if timezone.is_naive(new_datetime):
        new_datetime = timezone.make_aware(new_datetime)

    # Ensure existing_datetime is timezone-aware
    if timezone.is_naive(existing_datetime):
        existing_datetime = timezone.make_aware(existing_datetime)

    # Determine if there's been a change in the datetime or the reminder preference
    want_reminder = want_reminder if want_reminder is not None else appointment.want_reminder
    datetime_changed = new_datetime != existing_datetime
    reminder_preference_changed = appointment.want_reminder != want_reminder

    if datetime_changed or reminder_preference_changed:
        # Cancel any existing reminder
        cancel_existing_reminder(appointment.id_request)

        # If a reminder is still desired and the appointment is in the future, schedule a new one
        if want_reminder and new_datetime > timezone.now():
            schedule_email_reminder(appointment, request, new_datetime)
        else:
            logger.info(
                    f"Reminder for appointment {appointment.id} is not scheduled per "
                    f"user's preference or past datetime.")

    # Update the appointment's reminder preference
    appointment.want_reminder = want_reminder
    appointment.save()


def cancel_existing_reminder(appointment_id_request):
    """
    Cancels any existing reminder for the appointment.
    """
    task_name = f"reminder_{appointment_id_request}"
    Schedule.objects.filter(name=task_name).delete()


def can_appointment_be_rescheduled(appointment_request):
    # Datetime 5 minutes ago from now
    five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)

    # Filter reschedule histories to those created within the last 5 minutes
    recent_reschedule_count = appointment_request.reschedule_histories.filter(created_at__gte=five_minutes_ago).count()
    service = appointment_request.service
    config = Config.get_instance()

    # Determine which rescheduled limit to use based on service settings
    if service.allow_rescheduling:
        # If rescheduling is allowed
        logger.info(f"Rescheduling is allowed for service {service.name} -> "
                    f"Reschedule count: {recent_reschedule_count}, Reschedule limit: {service.reschedule_limit}")
        return recent_reschedule_count < service.reschedule_limit
    else:
        # Rescheduling is allowed but no specific limit set; use system default
        logger.info(f"Rescheduling is allowed but no specific limit set for service {service.name} -> "
                    f"Reschedule count: {recent_reschedule_count}, Reschedule limit: {config.default_reschedule_limit}")
        return recent_reschedule_count < config.default_reschedule_limit


def staff_change_allowed_on_reschedule():
    return Config.objects.first().allow_staff_change_on_reschedule


def generate_unique_username_from_email(email: str) -> str:
    username_base = email.split('@')[0]
    username = username_base
    suffix = 1
    CLIENT_MODEL = get_user_model()

    while CLIENT_MODEL.objects.filter(username=username).exists():
        suffix_str = f"{suffix:02}"
        username = f"{username_base}{suffix_str}"
        suffix += 1
    return username


def parse_name(name: str):
    parts = name.split(' ', 1)
    if len(parts) == 1:
        parts.append('')  # Add an empty string for the last name if not provided
    return parts[0], parts[1]


def create_user_with_email(client_data: dict):
    CLIENT_MODEL = get_user_model()
    # Valid fields
    valid_fields = ['email', 'first_name', 'last_name']

    # Filter client_data to include only valid fields
    user_data = {field: client_data.get(field, '') for field in valid_fields}

    user = CLIENT_MODEL.objects.create_user(**user_data)
    return user


def create_user_with_username(client_data: dict):
    CLIENT_MODEL = get_user_model()
    if 'username' not in client_data:
        username = generate_unique_username_from_email(client_data['email'])
    else:
        username = client_data['username']
    user_data = {
        'username': username,
        'email': client_data['email'],
        'first_name': client_data.get('first_name', ''),
        'last_name': client_data.get('last_name', '')
    }
    user = CLIENT_MODEL.objects.create_user(**user_data)
    return user


def create_new_user(client_data: dict):
    CLIENT_MODEL = get_user_model()

    # Check if client_data has first_name and last_name
    if 'first_name' not in client_data or 'last_name' not in client_data:
        # Assuming 'name' contains a single space between first and last name.
        client_data['first_name'], client_data['last_name'] = parse_name(client_data['name'])

    try:
        # Check if the 'username' field exists in the User model
        CLIENT_MODEL._meta.get_field('username')
        user = create_user_with_username(client_data)
    except FieldDoesNotExist:
        client_data.pop('username', None)
        user = create_user_with_email(client_data)
    return user


def username_in_user_model():
    CLIENT_MODEL = get_user_model()
    try:
        # Check if the 'username' field exists in the User model
        CLIENT_MODEL._meta.get_field('username')
        return True
    except FieldDoesNotExist:
        return False


def create_payment_info_and_get_url(appointment):
    """
    Create a new payment information entry for the appointment and return the payment URL.

    :param appointment: The appointment to create the payment information for.
    :return: The payment URL for the appointment.
    """
    # Create a new PaymentInfo entry for the appointment
    payment_info = PaymentInfo(appointment=appointment)
    payment_info.save()

    # Check if APPOINTMENT_PAYMENT_URL is a Django reverse URL (e.g. "app:view_name") or an external link
    if (":" in APPOINTMENT_PAYMENT_URL and "/" not in APPOINTMENT_PAYMENT_URL) and not bool(
            urlparse(APPOINTMENT_PAYMENT_URL).netloc):
        # It's a Django reverse URL; generate the URL
        payment_url = reverse(
                APPOINTMENT_PAYMENT_URL,
                kwargs={'object_id': payment_info.id, 'id_request': payment_info.get_id_request()}
        )
    else:
        # It's an external link; return as is or append necessary data
        payment_url = APPOINTMENT_PAYMENT_URL

    return payment_url


def exclude_booked_slots(appointments, slots, slot_duration=None):
    """Exclude the booked slots from the given list of slots.

    :param appointments: The appointments to exclude.
    :param slots: The slots to exclude the appointments from.
    :param slot_duration: The duration of each slot.
    :return: The slots with the booked slots excluded.
    """
    available_slots = []
    for slot in slots:
        slot_end = slot + slot_duration
        is_available = True
        for appointment in appointments:
            appointment_start_time = appointment.get_start_time()
            appointment_end_time = appointment.get_end_time()
            if appointment_start_time < slot_end and slot < appointment_end_time:
                is_available = False
                break
        if is_available:
            available_slots.append(slot)
    return available_slots


def exclude_pending_reschedules(slots, staff_member, date):
    """
    Exclude the slots that are pending reschedule for the given staff member and date.
    """

    # Calculate the time window for "last 5 minutes"
    ten_minutes_ago = timezone.now() - datetime.timedelta(minutes=5)
    pending_reschedules = AppointmentRescheduleHistory.objects.filter(
            appointment_request__staff_member=staff_member,
            date=date,
            reschedule_status='pending',
            created_at__gte=ten_minutes_ago
    )

    # Filter out slots that overlap with any pending rescheduling
    filtered_slots = slots[:]
    for reschedule in pending_reschedules:
        reschedule_start_time = datetime.datetime.combine(date, reschedule.start_time)
        reschedule_end_time = datetime.datetime.combine(date, reschedule.end_time)

        filtered_slots = [slot for slot in filtered_slots if
                          not (reschedule_start_time <= slot < reschedule_end_time)]

    return filtered_slots


def day_off_exists_for_date_range(staff_member, start_date, end_date, days_off_id=None) -> bool:
    """Check if a day off exists for the given staff member and date range.

    :param staff_member: The staff member to check.
    :param start_date: The start date of the date range.
    :param end_date: The end date of the date range.
    :param days_off_id: The ID of the day off to exclude from the check.
    :return: True if a day off exists for the given staff member and date range; otherwise, False.
    """
    days_off = DayOff.objects.filter(staff_member=staff_member, start_date__lte=end_date, end_date__gte=start_date)
    if days_off_id:
        days_off = days_off.exclude(id=days_off_id)
    return days_off.exists()


def get_all_appointments() -> list:
    """Get all appointments from the database.

    :return: QuerySet, all appointments
    """
    return Appointment.objects.all()


def get_all_staff_members() -> list:
    """Get all staff members from the database.

    :return: QuerySet, all staff members
    """
    return StaffMember.objects.all()


def get_appointment_buffer_time():
    """Get the appointment buffer time from the settings file.

    :return: The appointment buffer time
    """
    from appointment.models import Config

    config = Config.objects.first()

    if config and config.appointment_buffer_time:
        return config.appointment_buffer_time
    return APPOINTMENT_BUFFER_TIME


def get_appointment_by_id(appointment_id):
    """Get an appointment by its ID.

    :param appointment_id: The appointment's ID
    :return: The appointment with the specified ID or None if no appointment with the specified ID exists
    """
    try:
        return Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return None


def get_appointment_finish_time():
    """Get the appointment finish time from the settings file.

    :return: The appointment's finish time
    """
    from appointment.models import Config

    config = Config.objects.first()

    if config and config.finish_time:
        return config.finish_time
    return APPOINTMENT_FINISH_TIME


def get_appointment_lead_time():
    """Get the appointment lead time from the settings file.

    :return: The appointment's lead time
    """
    from appointment.models import Config

    config = Config.objects.first()

    if config and config.lead_time:
        return config.lead_time
    return APPOINTMENT_LEAD_TIME


def get_appointment_slot_duration():
    """Get the appointment slot duration from the settings file.

    :return: The appointment slot duration
    """
    from appointment.models import Config

    config = Config.objects.first()

    if config and config.slot_duration:
        return config.slot_duration
    return APPOINTMENT_SLOT_DURATION


def get_appointments_for_date_and_time(date, start_time, end_time, staff_member):
    """Returns all appointments that overlap with the specified date and time range.

    :param date: The date to filter appointments on.
    :param start_time: The starting time to filter appointments on.
    :param end_time: The ending time to filter appointments on.
    :param staff_member: The staff member to filter appointments on.

    :return: QuerySet, all appointments that overlap with the specified date and time range
    """
    return Appointment.objects.filter(
            appointment_request__date=date,
            appointment_request__start_time__lte=end_time,
            appointment_request__end_time__gte=start_time,
            appointment_request__staff_member=staff_member
    )


def get_config():
    """Returns the configuration object from the database or the cache."""
    config = cache.get('config')
    if not config:
        config = Config.objects.first()
        # Cache the configuration for 1 hour (3600 seconds)
        cache.set('config', config, 3600)
    return config


def get_day_off_by_id(day_off_id):
    """Get a day off by its ID.

    :param day_off_id: The day offs ID
    :return: DayOff, the day off with the specified ID or None if no day off with the specified ID exists.
    """
    try:
        return DayOff.objects.get(pk=day_off_id)
    except DayOff.DoesNotExist:
        return None


def get_non_working_days_for_staff(staff_member_id):
    """Return the non-working days for the given staff member or an empty list if the staff member does not exist."""
    all_days = set(range(7))  # Represents all days (0-6)
    try:
        staff_member = StaffMember.objects.get(id=staff_member_id)
        working_days = set(WorkingHours.objects.filter(staff_member=staff_member).values_list('day_of_week', flat=True))

        # Subtracting working_days from all_days to get non-working days
        non_working_days = list(all_days - working_days)
        return non_working_days
    except StaffMember.DoesNotExist:
        return []


def get_staff_member_appointment_list(staff_member: StaffMember) -> list:
    """Get a list of appointments for the given staff member."""
    return Appointment.objects.filter(appointment_request__staff_member=staff_member)


def get_weekday_num_from_date(date: datetime.date = None) -> int:
    """Get the number of the weekday from the given date."""
    if date is None:
        date = datetime.date.today()
    return get_weekday_num(date.strftime("%A"))


def get_staff_member_buffer_time(staff_member: StaffMember, date: datetime.date) -> float:
    """Return the buffer time for the given staff member on the given date."""
    _, _, _, buff_time = get_times_from_config(date)
    buffer_minutes = buff_time.total_seconds() / 60
    return staff_member.appointment_buffer_time or buffer_minutes


def get_staff_member_by_user_id(user_id):
    """Return a staff member by their user ID."""
    try:
        return StaffMember.objects.get(user_id=user_id)
    except StaffMember.DoesNotExist:
        return None


def get_staff_member_end_time(staff_member: StaffMember, date: datetime.date) -> Optional[datetime.time]:
    """Return the end time for the given staff member on the given date."""
    weekday_num = get_weekday_num_from_date(date)
    working_hours = get_working_hours_for_staff_and_day(staff_member, weekday_num)
    return working_hours['end_time']


def get_staff_member_from_user_id_or_logged_in(user, user_id=None):
    """Fetch StaffMember based on the user_id or the logged-in user."""
    staff_member = None
    try:
        if user_id:
            staff_member = StaffMember.objects.get(user_id=user_id)
        else:
            staff_member = user.staffmember
    except StaffMember.DoesNotExist:
        pass
    return staff_member


def get_staff_member_slot_duration(staff_member: StaffMember, date: datetime.date) -> int:
    """Return the slot duration for the given staff member on the given date."""
    _, _, slot_duration, _ = get_times_from_config(date)
    slot_minutes = slot_duration.total_seconds() / 60
    return staff_member.slot_duration or slot_minutes


def get_staff_member_start_time(staff_member: StaffMember, date: datetime.date) -> Optional[datetime.time]:
    """Return the start time for the given staff member on the given date."""
    weekday_num = get_weekday_num_from_date(date)
    working_hours = get_working_hours_for_staff_and_day(staff_member, weekday_num)
    return working_hours['start_time']


def get_times_from_config(date):
    """Get the start time, end time, slot duration, and buffer time from the configuration or the settings file.

    :param date: The date to get the times for.
    :return: The start time, end time, slot duration, and buffer time.
    """
    config = get_config()
    if config:
        start_time = datetime.datetime.combine(date, datetime.time(hour=config.lead_time.hour,
                                                                   minute=config.lead_time.minute))
        end_time = datetime.datetime.combine(date, datetime.time(hour=config.finish_time.hour,
                                                                 minute=config.finish_time.minute))
        slot_duration = datetime.timedelta(minutes=config.slot_duration)
        buff_time = datetime.timedelta(minutes=config.appointment_buffer_time)
    else:
        start_hour, start_minute = APPOINTMENT_LEAD_TIME
        start_time = datetime.datetime.combine(date, datetime.time(hour=start_hour, minute=start_minute))
        finish_hour, finish_minute = APPOINTMENT_FINISH_TIME
        end_time = datetime.datetime.combine(date, datetime.time(hour=finish_hour, minute=finish_minute))
        slot_duration = datetime.timedelta(minutes=APPOINTMENT_SLOT_DURATION)
        buff_time = datetime.timedelta(minutes=APPOINTMENT_BUFFER_TIME)
    return start_time, end_time, slot_duration, buff_time


def get_user_by_email(email: str):
    """Get a user by their email address.

    :param email: The email address of the user.
    :return: The user with the specified email address, if found; otherwise, None.
    """
    CLIENT_MODEL = get_user_model()
    return CLIENT_MODEL.objects.filter(email=email).first()


def get_website_name() -> str:
    """Get the website name from the configuration file.

    :return: The website name
    """
    from appointment.models import Config

    config = Config.objects.first()

    if config and config.website_name != "":
        return config.website_name
    return APPOINTMENT_WEBSITE_NAME


def get_working_hours_by_id(working_hours_id):
    """Get a working hours by its ID.

    :param working_hours_id: The working hours' ID
    :return: WorkingHours, the working hours with the specified ID
    """
    try:
        return WorkingHours.objects.get(pk=working_hours_id)
    except WorkingHours.DoesNotExist:
        return None


def get_working_hours_for_staff_and_day(staff_member, day_of_week):
    """Get the working hours for the given staff member and day of the week.

    :param staff_member: The staff member to get the working hours for.
    :param day_of_week: The day of the week to get the working hours for.
    :return: The working hours for the given staff member and day of the week.
    """
    working_hours = WorkingHours.objects.filter(staff_member=staff_member, day_of_week=day_of_week).first()
    start_time = staff_member.get_lead_time()
    end_time = staff_member.get_finish_time()
    if not working_hours and not (start_time and end_time):
        return None
    # If no specific working hours are set for that day, use the default start and end times from StaffMember
    if not working_hours:
        return {
            'staff_member': staff_member,
            'day_of_week': day_of_week,
            'start_time': staff_member.get_lead_time(),
            'end_time': staff_member.get_finish_time()
        }

    # If a WorkingHours instance is found, convert it to a dictionary for consistent return type
    return {
        'staff_member': working_hours.staff_member,
        'day_of_week': working_hours.day_of_week,
        'start_time': working_hours.start_time,
        'end_time': working_hours.end_time
    }


def is_working_day(staff_member: StaffMember, day: int) -> bool:
    """Check if the given day is a working day for the staff member."""
    working_days = list(WorkingHours.objects.filter(staff_member=staff_member).values_list('day_of_week', flat=True))
    return day in working_days


def working_hours_exist(day_of_week, staff_member):
    """Check if working hours exist for the given day of the week and staff member."""
    return WorkingHours.objects.filter(day_of_week=day_of_week, staff_member=staff_member).exists()


def get_absolute_url_(relative_url, request):
    return request.build_absolute_uri(relative_url)
