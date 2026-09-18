# `ics_utils.py`

This module builds the iCalendar (`.ics`) attachment that ships with the appointment emails, so clients and staff can
add the appointment to their own calendar in one click.

## Module Metadata:

**Author**: Adams Pierre David

## Functions:

- **generate_ics_file(appointment)**:
    - Builds an iCalendar file for the given appointment and returns it as bytes, ready to be attached to an email as
      `('appointment.ics', ics_file, 'text/calendar')`.
    - The event carries the service name as its summary, the appointment's start and end times, the client's address
      as the location, and any additional info as the description. The staff member is set as the organizer and the
      client as the attendee.
    - The calendar's product ID uses the website name from the [configuration](../configuration.md).

It is used by `send_thank_you_email`, `notify_admin_about_appointment` and `notify_admin_about_reschedule` in
[`email_ops.py`](email_ops.md).
