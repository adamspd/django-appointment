## Migration Guide for Version 3.13.0 🚀

Version 3.13.0 does **not** change the database, and every change keeps the old names, fields and folders working. If
you use the package's pages and emails as they are, upgrading is only a `pip install` and a `collectstatic`. If you
override the staff pages, the schedule forms or the emails, read the steps below.

### Before you start: supported versions

The supported Python, Django and dependency versions are the same as in 3.12.0. The
[compatibility matrix](../compatibility.md) has the tested combinations.

### Steps for Upgrading to Version 3.13.0:

1. **Backup Your Database**:
    - As a best practice, always back up your current database before an upgrade, even one without migrations.

2. **Update Package**:
    - Upgrade to the latest version by running:
      ```bash
      pip install --upgrade django-appointment
      ```

3. **Check there is nothing to migrate**:
    - ```bash
      python manage.py makemigrations appointment --check --dry-run
      ```
    - It should report "No changes detected".

4. **Collect the static files**:
    - The calendar, service form, schedule form and confirm dialog scripts changed. If your site serves collected
      static files, run:
      ```bash
      python manage.py collectstatic
      ```

5. **Check your schedule form overrides**:
    - If you override `manage_working_hours.html` or `manage_unavailability.html`, nothing breaks: the `*_raw` fields
      are still read. But you can now post the plain field names (`date`, `start_time`, `end_time`, `day_of_week`)
      from `<input type="date">` and `<input type="time">`, and drop the hidden `*_raw` copies.
    - Errors now come back as `{"errors": {"<field>": ["..."]}}` with status 400. The package's
      `js/app_admin/schedule_form.js` shows them under the fields; if you post the form with your own script, read
      that shape.

6. **Check your service and staff form overrides**:
    - `{{ form.services_offered }}` now draws checkboxes. If you drew your own checkboxes by looping over the choices,
      nothing changes.
    - `{{ form.duration }}` now draws two inputs, `duration_hours` and `duration_minutes`. If your template draws its
      own input named `duration` with an `HH:MM:SS` value, it keeps working. If your script reads
      `form.elements.duration`, read the two new inputs instead.

7. **Check your email overrides**:
    - Your templates get more context now (see [Custom templates](../custom-templates.md)); the keys they used keep
      their values, with one exception: in the admin copy of `reminder_email.html`, `first_name` is empty. Use
      `client_first_name` if you showed the client's name to the admin.
    - Without an override, the password and verification emails are now HTML. If you relied on the plain-text body,
      add your own `emails/password_reset.html` or `emails/verification.html`.
    - Set `APPOINTMENT_SITE_URL` if your emails should link to your site (it is needed for full links in reminders
      and staff notifications). When set, it is also used for the set-password and reschedule links.

8. **Test the booking flow**:
    - Book an appointment and enter a wrong phone number: the error should show under the field.

### Optional follow-ups

- **Move your overrides into folders**: `custom/admin/` for staff pages and `custom/booking/` for client pages.
- **Drop copied code**: an override that only changed a title or a button can now extend the default page and fill
  `djappt_heading` or `djappt_actions`. A calendar override that only changed the height can use
  `APPOINTMENT_CALENDAR_OPTIONS`. Views or context processors that worked out page titles can use `page_title`.
- **Check your emails**: with `DEBUG = True`, open `app-admin/email-preview/` as a superuser.

### Troubleshooting:

- **My override in `custom/` is ignored**:
    - A file with the same name in `custom/admin/` or `custom/booking/` wins. Remove one of them.
- **The calendar keeps its old height**:
    - Your `staff_index.html` override must print the options: add
      `{{ calendar_options|json_script:"djappt-calendar-options" }}` before the page's scripts.
- **Issues Post Upgrade**:
    - Consult the [release notes](../release_notes/latest.md) for the details of each change, and check the Django
      logs for error messages.

### Important Notes 📝:

- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
- Upgrading from 3.11 or older? Read the [3.12 migration guide](v3_12_0.md) first.
