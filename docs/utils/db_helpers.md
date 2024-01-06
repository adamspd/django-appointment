# Django Appointment 📦: `db_helpers.py`

This module contains various utility functions to assist in the database operations related to the Django appointment
system.

## Overview:

- [Module Metadata](#module-metadata)
- [Utility Functions](#utility-functions)
    - [Slot Calculations](#slot-calculations)
    - [Appointments](#appointments)
    - [Users & Staff Members](#users-and-staff-members)
    - [Working Hours & Days Off](#working-hours-and-days-off)
    - [Configurations & Settings](#configurations-and-settings)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.2.0

## Utility Functions:

### Slot Calculations:

- **calculate_slots**: Calculate the available slots between given start and end times using buffer time and slot
  duration.
- **calculate_staff_slots**: Calculate the available slots for a given staff member on a specified date.

### Appointments:

- **check_day_off_for_staff**: Check if a given staff member is off on a specified date.
- **create_and_save_appointment**: Create and save a new appointment based on the provided appointment request and
  client data.
- **exclude_booked_slots**: Exclude booked slots from a list of available slots.
- **get_all_appointments**: Retrieve all appointments from the database.
- **get_appointment_by_id**: Retrieve an appointment by its ID.
- **get_appointments_for_date_and_time**: Fetch all appointments overlapping with a specific date and time range.

### Users and Staff Members:

- **create_new_user**: Create and save a new user to the database.
- **get_user_by_email**: Fetch a user by their email address.
- **get_user_model**: Get the user model from the settings.
- **get_staff_member_by_user_id**: Fetch a staff member using their user ID.
- **get_staff_member_from_user_id_or_logged_in**: Fetch a staff member based on a user ID or the logged-in user.

### Working Hours and Days Off:

- **day_off_exists_for_date_range**: Check if a day off exists for a given staff member within a specified date range.
- **get_day_off_by_id**: Retrieve a day off record by its ID.
- **get_non_working_days_for_staff**: Get non-working days for a given staff member.
- **get_staff_member_appointment_list**: Fetch a list of appointments for a given staff member.
- **get_weekday_num_from_date**: Determine the number of the weekday from a given date.
- **get_working_hours_by_id**: Fetch working hours by its ID.
- **get_working_hours_for_staff_and_day**: Fetch the working hours for a given staff member on a specific day of the
  week.
- **is_working_day**: Determine if a specified day is a working day for a given staff member.
- **working_hours_exist**: Check if working hours exist for a specified day of the week and staff member.

### Configurations and Settings:

- **create_payment_info_and_get_url**: Create a payment information record for an appointment and retrieve the payment
  URL.
- **get_all_staff_members**: Fetch all staff members from the database.
- **get_appointment_buffer_time**: Retrieve the appointment buffer time from the settings or the configuration.
- **get_appointment_finish_time**: Fetch the appointment finish time from the settings or the configuration.
- **get_appointment_lead_time**: Fetch the appointment lead time from the settings or the configuration.
- **get_appointment_slot_duration**: Retrieve the appointment slot duration from the settings or the configuration.
- **get_config**: Fetch the configuration object from the database or cache.
- **get_times_from_config**: Fetch various time settings from the configuration or settings file.
- **get_website_name**: Retrieve the website name from the configuration or settings.
