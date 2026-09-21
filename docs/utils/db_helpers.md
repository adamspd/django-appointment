# `db_helpers.py`

This module contains various utility functions to assist in the database operations related to the Django appointment
system.

## Overview:

- [Module Metadata](#module-metadata)
- [Utility Functions](#utility-functions)
    - [Slot Calculations](#slot-calculations)
    - [Appointments](#appointments)
    - [Reminders](#reminders)
    - [Rescheduling](#rescheduling)
    - [Users & Staff Members](#users-and-staff-members)
    - [Per-staff-member Scheduling Values](#per-staff-member-scheduling-values)
    - [Unavailabilities, Working Hours & Days Off](#unavailabilities-working-hours-and-days-off)
    - [Configurations & Settings](#configurations-and-settings)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.2.0

## Utility Functions:

### Slot Calculations:

- **calculate_slots**: Calculate the available slots between given start and end times using buffer time and slot
  duration.
- **calculate_staff_slots**: Calculate the available slots for a given staff member on a specified date.
- **exclude_unavailable_slots**: Remove from a list of slots everything the staff member cannot take: the
  `appointments` already booked, and the `unavailabilities` blocking part of the day. Takes an optional
  `service_duration` so services longer than the slot step don't overlap, and an optional `gap_time` applied on both
  sides of each appointment. A slot is dropped as soon as it overlaps either kind of entry, even partly.
- **exclude_pending_reschedules**: Exclude the slots that have a pending reschedule request for the given staff
  member and date.

### Appointments:

- **check_day_off_for_staff**: Check if a given staff member is off on a specified date.
- **create_and_save_appointment**: Create and save a new appointment based on the provided appointment request and
  client data.
- **get_all_appointments**: Retrieve all appointments from the database.
- **get_appointment_by_id**: Retrieve an appointment by its ID.
- **get_appointments_for_date_and_time**: Fetch all appointments overlapping with a specific date and time range.
- **get_staff_member_appointment_list**: Fetch a list of appointments for a given staff member.

### Reminders:

These require Django Q; without it they log a warning and do nothing.

- **schedule_email_reminder**: Schedule the 24-hour reminder email for an appointment.
- **update_appointment_reminder**: Update or cancel an appointment's reminder after its date, time, or the client's
  reminder preference has changed.
- **cancel_existing_reminder**: Cancel any reminder already scheduled for an appointment.

### Rescheduling:

- **can_appointment_be_rescheduled**: Determine whether an appointment request may be rescheduled. Counts the
  reschedule history entries created in the last 5 minutes and compares that with `Service.reschedule_limit` (when
  the service has `allow_rescheduling` enabled) or `Config.default_reschedule_limit` otherwise.
- **staff_change_allowed_on_reschedule**: Return the `allow_staff_change_on_reschedule` value from the configuration.

### Users and Staff Members:

- **create_new_user**: Create and save a new user to the database, dispatching to the email- or username-based
  variant depending on the user model.
- **create_user_with_email**: Create a user on a model that has no `username` field.
- **create_user_with_username**: Create a user on a model that has a `username` field, generating one when it is not
  supplied.
- **generate_unique_username_from_email**: Build a username from the local part of an email, adding a numeric suffix
  until it is unique.
- **username_in_user_model**: Check whether the configured user model has a `username` field.
- **parse_name**: Split a full name into a first name and a last name.
- **get_user_by_email**: Fetch a user by their email address.
- **get_staff_member_by_user_id**: Fetch a staff member using their user ID.
- **get_staff_member_from_user_id_or_logged_in**: Fetch a staff member based on a user ID or the logged-in user.
- **get_all_staff_members**: Fetch all staff members from the database.

### Per-staff-member Scheduling Values:

Each of these resolves the staff member's own value first and falls back to the global configuration.

- **get_staff_member_start_time**: The start time for a given staff member on a given date.
- **get_staff_member_end_time**: The end time for a given staff member on a given date.
- **get_staff_member_slot_duration**: The slot duration for a given staff member on a given date.
- **get_staff_member_buffer_time**: The buffer time for a given staff member on a given date.
- **get_staff_member_slot_gap_time**: The rest time in minutes between two appointments. Resolves in priority order:
  the staff member's `slot_gap_time`, then `Config.slot_gap_time`, then `0`.

### Unavailabilities, Working Hours and Days Off:

- **day_off_exists_for_date_range**: Check if a day off exists for a given staff member within a specified date range.
- **get_day_off_by_id**: Retrieve a day off record by its ID.
- **get_unavailability_by_id**: Retrieve an [`Unavailability`](../models.md#unavailability) by its ID, or `None` when
  there is no such row.
- **get_unavailabilities_for_date_and_time**: Return the staff member's unavailabilities on a given date that overlap
  a time range — the range being the working hours of the day, so the result is what actually eats into bookable
  slots.
- **get_non_working_days_for_staff**: Get non-working days for a given staff member.
- **get_weekday_num_from_date**: Determine the number of the weekday from a given date.
- **get_working_hours_by_id**: Fetch working hours by its ID.
- **get_working_hours_for_staff_and_day**: Fetch the working hours for a given staff member on a specific day of the
  week.
- **is_working_day**: Determine if a specified day is a working day for a given staff member.
- **working_hours_exist**: Check if working hours exist for a specified day of the week and staff member.

### Configurations and Settings:

- **create_payment_info_and_get_url**: Create a payment information record for an appointment and retrieve the payment
  URL.
- **get_appointment_buffer_time**: Retrieve the appointment buffer time from the settings or the configuration.
- **get_appointment_finish_time**: Fetch the appointment finish time from the settings or the configuration.
- **get_appointment_lead_time**: Fetch the appointment lead time from the settings or the configuration.
- **get_appointment_slot_duration**: Retrieve the appointment slot duration from the settings or the configuration.
- **get_config**: Fetch the configuration object from the database or cache.
- **get_times_from_config**: Fetch various time settings from the configuration or settings file.
- **get_website_name**: Retrieve the website name from the configuration or settings.
- **get_absolute_url_**: Turn a relative URL into an absolute one using the current request.
