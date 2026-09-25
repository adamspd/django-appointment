# Configuration

Customizing your Django appointment scheduler is straightforward. In your Django project's `settings.py` file, you can
override the default configurations to tailor the application according to your needs. Below is a breakdown of the
configurations.

## Essential Configurations:

These configurations are needed for the application to operate correctly; most of them can also be set in the Config
model in the admin panel. However, you can also set them here.
The values provided here represent the default settings. Change them to suit your needs.

```python
APPOINTMENT_BASE_TEMPLATE = 'base_templates/base.html'  # Your site's base template, used by the booking pages
APPOINTMENT_ADMIN_BASE_TEMPLATE = 'base_templates/base.html'  # (optional) Specify a different base template for the admin panel
APPOINTMENT_WEBSITE_NAME = 'Website'  # Can be set in the Config model.
APPOINTMENT_PAYMENT_URL = None
APPOINTMENT_THANK_YOU_URL = None
APPOINTMENT_BUFFER_TIME = 0  # Can be set in the Config Model. Minutes between now and the first available slot for the current day (doesn't affect future dates)
APPOINTMENT_SLOT_DURATION = 30  # Can be set in the Config Model. Duration of each appointment slot in minutes 
APPOINTMENT_LEAD_TIME = (9, 0)  # Can be set in the Config Model. Start time of the appointment slots (in 24-hour format)
APPOINTMENT_FINISH_TIME = (18, 30)  # Can be set in the Config Model. End time of the appointment slots (in 24-hour format)
USE_DJANGO_Q_FOR_EMAILS = False  # Use Django Q for sending ALL emails.
```

The package pages extend `appointment/layout.html`, which extends the base template you set. See
[Your base template](custom-templates.md#your-base-template) for the blocks and scripts it must provide.

!!! note "Settings vs. the Config model"
    Where a setting says "Can be set in the Config Model", the database value wins when a `Config` row exists.
    The `settings.py` value is the fallback used when it doesn't. See the [Config model](models.md#config).

## Custom Template Configurations:

These control where the package looks for your template overrides. Both are optional and shown with their defaults:

```python
APPOINTMENT_CUSTOM_TEMPLATES_DIR = 'custom'  # Directory (inside your templates dir) for page overrides
APPOINTMENT_CUSTOM_EMAILS_DIR = 'emails'  # Directory (inside your templates dir) for email overrides
```

See [Custom templates](custom-templates.md) for the list of template names you can override and the context each one
receives.

## Cleanup Configuration:

Appointment requests that never became an appointment (a client picked a slot, then abandoned the flow) pile up over
time. The package deletes the stale ones for you:

```python
APPOINTMENT_CLEANUP_DAYS = 7  # Delete unassociated appointment requests older than this many days
```

If `django_q` is in your `INSTALLED_APPS`, a daily cleanup task is scheduled automatically when the app starts — you
don't have to register anything. Without Django Q, nothing is scheduled and you can run the cleanup yourself:

```bash
python manage.py cleanup_appointment_requests

# See what would be deleted without deleting anything:
python manage.py cleanup_appointment_requests --dry-run
```

Only appointment requests with no associated `Appointment` are removed; confirmed appointments are never touched.

## Django Q Configuration:

For email reminders with Django Q, you can configure the following settings after adding `django_q` to
your `INSTALLED_APPS`:

```python
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}
```

If those settings are not provided, the application won't send email reminders. You also have to
run `python manage.py qcluster` to start the Django Q cluster.

### Sending all emails through Django Q

By default, only the 24-hour reminders go through Django Q; every other email is sent inline, during the request.
If you're already running a cluster, it is worth offloading the rest of them too:

```python
USE_DJANGO_Q_FOR_EMAILS = True  # Use Django Q for sending ALL emails, not just reminders
```

## Django Default Settings Utilization:

The application leverages some of the default settings from your Django project.
Ensure these values (DEFAULT_FROM_EMAIL, TIME_ZONE) are set in your `settings.py` because they are used as:

```python
APP_DEFAULT_FROM_EMAIL = 'DEFAULT_FROM_EMAIL'  # Default email for sending notifications
APP_TIME_ZONE = 'TIME_ZONE'  # Ensure the TIME_ZONE is set to your desired timezone
```

The package also reads `ADMINS` to decide who receives the admin notification emails for new and rescheduled
appointments.

## Deprecated Configurations:

The following configuration is no longer in use:

```python
APPOINTMENT_CLIENT_MODEL = 'auth.User'  # Deprecated
```

It has been replaced with a more flexible approach: the package resolves the client model through Django's own
`django.contrib.auth.get_user_model()`, which honours your `AUTH_USER_MODEL`.

```python
AUTH_USER_MODEL = 'your_app.YourUserModel'  # Optional if you use Django's default user model
```

Ensure `AUTH_USER_MODEL` is correctly set in your `settings.py` if you use a custom user model.
