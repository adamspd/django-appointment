## Migration Guide for Version 3.16.0 🚀

Version 3.16.0 changes the database (working hours, appointment requests and amounts), adds one optional setting and a
new script used by the booking and staff calendars. The supported Python and Django versions are the same.

### Coming from 3.15.x

1. **Upgrade the package**:

    ```bash
    pip install django-appointment==3.16.0
    ```

2. **Create and run the migration.** It covers these changes:
    - `WorkingHours` no longer has the one-row-per-day constraint, so a day can have several working hours.
    - `AppointmentRequest` has new `client_timezone` and `booking_context` fields.
    - `Service.price`, `Service.down_payment` and `Appointment.amount_to_pay` take up to 12 digits.

    ```bash
    python manage.py makemigrations appointment
    python manage.py migrate
    ```

3. **Collect the static files**, since the booking and staff calendar scripts changed and `js/local_calendar.js` is
   new:

    ```bash
    python manage.py collectstatic
    ```

4. **Check your template overrides.** If you override these templates, copy the new lines from the package's version:
    - `appointment/appointments.html` and `administration/staff_index.html`: load `js/local_calendar.js` before the
      calendar script. **Without it, the booking or staff calendar doesn't load.**

        ```django
        <script src="{% static 'js/local_calendar.js' %}"></script>
        ```

    - `appointment/appointments.html`: add the `djappt-tz-notice` paragraph and the `djappt-local-time` block if you
      want the client's own time on the booking page.
    - `base_templates/base.html` and `email_sender/base_email.html`: set `lang` and `dir` from the current language,
      so right-to-left languages are mirrored.
    - `administration/manage_day_off.html`, `manage_unavailability.html` and `manage_working_hours.html`: load
      `js/local_calendar.js` and call `localDateTimeInputs(document.documentElement.lang)` if you use Persian.

5. **Optional:** keep values from the moment a client books, such as the campaign. List the keys a listener of the new
   `appointment_request_created` signal may store (none by default):

    ```python
    APPOINTMENT_BOOKING_CONTEXT_KEYS = ['utm_source', 'utm_campaign']
    ```

   See [Keeping booking context](../booking-context.md).

6. **Check what changed in behaviour:**
    - Emails, the thank-you details and the reschedule page write dates with the language's format, not a fixed
      `l, d F Y` format.
    - The staff calendar starts the week on the language's first day and shades the region's weekend.
    - In Persian, dates are shown in the Jalali calendar with Persian digits. They are still stored as Gregorian dates.

### Coming from 3.14.x or older

Follow the [3.15.0 migration guide](v3_15_0.md) first, then the steps above.

### Important Notes 📝:

- See the [release notes](../release_notes/latest.md) for what is new.
- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
