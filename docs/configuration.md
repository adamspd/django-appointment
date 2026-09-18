# Configuration

Customizing your Django appointment scheduler is straightforward. In your Django project's `settings.py`
file, you can override the default configurations to tailor the application to your needs. Below is a
breakdown of the configurations.

Customizing your Django appointment scheduler is straightforward. In your Django project's `settings.py` file, you can
override the default configurations to tailor the application, according to your needs. Below is a breakdown of the
configurations:

## Essential Configurations:

These configurations are needed for the application to operate correctly; most of them can also be set in the Config 
model in the admin panel. However, you can also set them here.
The values provided here represent the default settings. Change them to suit your needs.

```python
APPOINTMENT_BASE_TEMPLATE = 'base_templates/base.html'
APPOINTMENT_ADMIN_BASE_TEMPLATE = 'base_templates/base.html'  # (optional) Specify a different base template for the admin panel
APPOINTMENT_WEBSITE_NAME = 'Website'  # Can be set in the Config model.
APPOINTMENT_PAYMENT_URL = None
APPOINTMENT_THANK_YOU_URL = None
APPOINTMENT_BUFFER_TIME = 0  # Can be set in the Config Model. Minutes between now and the first available slot for the current day (doesn't affect future dates)
APPOINTMENT_SLOT_DURATION = 30  # Can be set in the Config Model. Duration of each appointment slot in minutes 
APPOINTMENT_LEAD_TIME = (9, 0)  # Can be set in the Config Model. Start time of the appointment slots (in 24-hour format)
APPOINTMENT_FINISH_TIME = (16, 30)  # Can be set in the Config Model. End time of the appointment slots (in 24-hour format)
USE_DJANGO_Q_FOR_EMAILS = False  # 🆕 Use Django Q for sending ALL emails.
```

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

### New Configurations:

A new configuration has been added to the application to allow you to use Django Q for sending all emails. 
If you're already using Django Q to send email reminders, it is nice to set this configuration.

```python
USE_DJANGO_Q_FOR_EMAILS = False  # 🆕 Use Django Q for sending email reminders
```

## Django Default Settings Utilization:

The application leverages some of the default settings from your Django project.
Ensure these values (DEFAULT_FROM_EMAIL, TIME_ZONE) are set in your `settings.py` because they are used as:

```python
APP_DEFAULT_FROM_EMAIL = 'DEFAULT_FROM_EMAIL'  # Default email for sending notifications
APP_TIME_ZONE = 'TIME_ZONE'  # Ensure the TIME_ZONE is set to your desired timezone
```

## Deprecated Configurations:

The following configuration is no longer in use:

```python
APPOINTMENT_CLIENT_MODEL = 'auth.User'  # Deprecated
```

It has been replaced with a more flexible approach, allowing for custom user models:

```python
from django.apps import apps
from django.conf import settings


def get_user_model():
    """
    Fetch the client model from the settings file.

    :return: The user model
    """
    return apps.get_model(settings.AUTH_USER_MODEL)
```

`AUTH_USER_MODEL` is your application's user model, ensure it is correctly set in your `settings.py`.
