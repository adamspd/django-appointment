## Migration Guide for Version 3.15.0 🚀

Version 3.15.0 changes the database (email verification codes), adds three settings and changes how rescheduling and
email codes behave. The supported Python and Django versions are the same.

### Coming from 3.14.x

1. **Upgrade the package**:

    ```bash
    pip install django-appointment==3.15.0
    ```

2. **Create and run the migration.** `EmailVerificationCode` has new `attempts` and `email` fields, and its `user` can
   now be empty (a new client's account is only created once they enter the code):

    ```bash
    python manage.py makemigrations appointment
    python manage.py migrate
    ```

3. **Collect the static files**, since the booking and calendar scripts changed:

    ```bash
    python manage.py collectstatic
    ```

4. **Check your site address** (optional). Links in emails use, in order, `APPOINTMENT_SITE_URL`, the current `Site`
   of `django.contrib.sites` when that app is installed, or the request's address:

    ```python
    APPOINTMENT_SITE_URL = "https://example.com"
    ```

   If you use `django.contrib.sites`, make sure your `Site`'s domain is not still `example.com`. Also make sure
   `ALLOWED_HOSTS` lists your real domain names, not `["*"]`.

5. **Optional:** change how long email codes stay valid (10 minutes by default):

    ```python
    APPOINTMENT_VERIFICATION_CODE_MINUTES = 10
    ```

   And limit the codes asked for from one IP address in an hour (off by default; read the
   [configuration page](../configuration.md) first if your site is behind a proxy):

    ```python
    APPOINTMENT_VERIFICATION_EMAILS_PER_IP = 10
    ```

6. **Check what changed in behaviour:**
    - Confirming a reschedule now takes a click on a Confirm button. The link opens the new
      `appointment/confirm_reschedule.html` page, which you can override like the other templates. Only a POST to
      that page confirms.
    - The reschedule limit now counts confirmed reschedules for each appointment request.
    - Staff and superuser accounts are no longer logged in by a booking code.
    - Bookings outside the staff member's free slots are refused, and the end time follows the service's duration.
    - If you override `manage_working_hours.html`, it keeps working with one day. To let staff pick several days,
      use checkboxes when `multiple_days` is set, as the package template does.
    - The calendar delete endpoint (`delete_appointment_ajax`) only accepts AJAX POST requests.
    - Only 3 codes are sent to the same address in an hour. The count uses Django's cache, so with several worker
      processes use a shared cache (Redis, Memcached or the database) for an exact count.

### Coming from 3.13.x or older

Follow the [3.14.0 migration guide](v3_14_0.md) first, then the steps above.

### Important Notes 📝:

- See the [release notes](../release_notes/latest.md) for what is new.
- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
