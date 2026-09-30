## Migration Guide for Version 3.13.0 🚀

Version 3.13.0 does **not** change the database: no model, field or constraint is added, renamed or removed, so there
is no migration to generate. It raises the minimum Python and Pillow versions, so check those first. The template,
form and email changes keep the old names, fields and folders working: if you use the package's pages and emails as
they are, upgrading is a `pip install` and a `collectstatic`. If you override the staff pages, the schedule forms or
the emails, read the steps after that.

### Before you start: supported versions

| Declared in `setup.cfg` | 3.12.0 | 3.13.0 |
|---|---|---|
| `python_requires` | `>=3.10` | **`>=3.11`** |
| Django | `>=4.2,<7.0` | `>=4.2,<7.0` |
| `Pillow` | `>=10.4,<13.0` | **`>=13.0,<14.0`** |
| Tested combinations | Python 3.10 – 3.14, Django 4.2 – 6.1 | **Python 3.11 – 3.14, Django 4.2 – 6.1** |

Python 3.10 is no longer accepted. `pip` will refuse to install 3.13.0 on it rather than installing something
broken, so if you are still on 3.10, stay on 3.12.0 until you can upgrade the interpreter. Pillow 13 fixes several
security vulnerabilities and does not support Python 3.10, so upgrading the interpreter is the only way to get those
fixes.

The [compatibility matrix](../compatibility.md) has the full grid of tested Python and Django combinations.

### Steps for Upgrading to Version 3.13.0:

1. **Check your Python version**:
    - Run `python --version` in the environment that serves your site. It must be 3.11 or newer. If you build a
      Docker image, check the base image too (`python:3.10-slim` has to move to 3.11 or newer).

2. **Check your Pillow pin**:
    - If your own requirements pin Pillow (`Pillow==12.3.0`, `Pillow<13`), raise it to `13.0` or newer, or remove it
      and let `pip` pick the version. Otherwise `pip` will report a conflict.

3. **Backup Your Database**:
    - As a best practice, always back up your current database before an upgrade, even one without migrations.

4. **Update Package**:
    - Upgrade to the latest version by running:
      ```bash
      pip install --upgrade django-appointment
      ```
    - Confirm Pillow was upgraded:
      ```bash
      python -c "import PIL; print(PIL.__version__)"
      ```
      It should print `13.0.0` or newer.

5. **Check there is nothing to migrate**:
    - The package does not ship migration files, so confirm your own ones are up to date:
      ```bash
      python manage.py makemigrations appointment --check --dry-run
      ```
    - It should report "No changes detected". If it proposes changes, they come from an earlier upgrade you have not
      migrated yet, not from 3.13.0: read that version's migration guide first.

6. **Collect the static files**:
    - The calendar, service form, schedule form and confirm dialog scripts changed. If your site serves collected
      static files, run:
      ```bash
      python manage.py collectstatic
      ```

7. **Check your schedule form overrides**:
    - If you override `manage_working_hours.html` or `manage_unavailability.html`, nothing breaks: the `*_raw` fields
      are still read. But you can now post the plain field names (`date`, `start_time`, `end_time`, `day_of_week`)
      from `<input type="date">` and `<input type="time">`, and drop the hidden `*_raw` copies.
    - Errors now come back as `{"errors": {"<field>": ["..."]}}` with status 400. The package's
      `js/app_admin/schedule_form.js` shows them under the fields; if you post the form with your own script, read
      that shape.

8. **Check your service and staff form overrides**:
    - `{{ form.services_offered }}` now draws checkboxes. If you drew your own checkboxes by looping over the choices,
      nothing changes.
    - `{{ form.duration }}` now draws two inputs, `duration_hours` and `duration_minutes`. If your template draws its
      own input named `duration` with an `HH:MM:SS` value, it keeps working. If your script reads
      `form.elements.duration`, read the two new inputs instead.

9. **Check your email overrides**:
    - Your templates get more context now (see [Custom templates](../custom-templates.md)); the keys they used keep
      their values, with one exception: in the admin copy of `reminder_email.html`, `first_name` is empty. Use
      `client_first_name` if you showed the client's name to the admin.
    - Without an override, the password and verification emails are now HTML. If you relied on the plain-text body,
      add your own `emails/password_reset.html` or `emails/verification.html`.
    - The links in the emails start with the request's address. Behind a proxy, check that Django's
      `USE_X_FORWARDED_HOST` and `SECURE_PROXY_SSL_HEADER` are set, as the set-password links already need.
    - Reminders queued before the upgrade still run, with relative links for the new `appointment_url` and
      `dashboard_url`; reminders scheduled after it get full links.

10. **Review and Test**:
    - Add or edit a service with an image, then book an appointment from start to finish.
    - While booking, enter a wrong phone number: the error should show under the field.
    - If your own code uses Pillow too, check it against Pillow 13: see
      [Pillow's 13.0.0 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html) for what
      changed.

### Optional follow-ups

- **Move your overrides into folders**: `custom/admin/` for staff pages and `custom/booking/` for client pages.
- **Drop copied code**: an override that only changed a title or a button can now extend the default page and fill
  `djappt_heading` or `djappt_actions`. A calendar override that only changed the height can use
  `APPOINTMENT_CALENDAR_OPTIONS`. Views or context processors that worked out page titles can use `page_title`.
- **Check your emails**: with `DEBUG = True`, open `app-admin/email-preview/` as a superuser.

### Troubleshooting:

- **`pip` says the package requires a different Python**:
    - Your environment runs Python 3.10 or older. Upgrade the interpreter (step 1), or stay on 3.12.0 for now.
- **`pip` reports a conflict on Pillow**:
    - Something in your requirements pins Pillow below 13.0 (step 2).
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
- Upgrading from 3.11 or older? Read the [3.12 migration guide](v3_12_0.md) first: that release changed how the
  pages and emails are built.
- Upgrading from the 3.10 series or older? Read the [3.11 migration guide](v3_11_0.md) too: that release added a
  model, so it needs a migration.
