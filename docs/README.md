# Django Appointment 📦

This application helps you to schedule appointments with your clients. It is a simple application that allows any client
to schedule an appointment for a service.

## Model Structure

The application has nine (9) models:

1. [Service](models.md#service)
2. [StaffMember](models.md#staffmember) 🆕
3. [AppointmentRequest](models.md#appointmentrequest)
4. [Appointment](models.md#appointment)
5. [Config](models.md#config)
6. [PaymentInfo](models.md#paymentinfo)
7. [EmailVerificationCode](models.md#emailverificationcode)
8. [DayOff](models.md#dayoff) 🆕
9. [WorkingHours](models.md#workinghours) 🆕

### Service

It represents a service provided by the system, including details such as the name, description, duration, price, and an
image representing the service.
It also handles the currency and down payment information.
[More details here](https://github.com/adamspd/django-appointment/blob/main/docs/models.md#service).

### StaffMember 🆕

This model is linked to a user and represents a staff member who offers services. It contains information about the
services offered, working hours, and availability on weekends.
[More details](https://github.com/adamspd/django-appointment/blob/main/docs/models.md#staffmember).

### Appointment Request

Represents a request for an appointment made by a client.
It includes the date, start and end times, selected service,
staff member, and payment type for the appointment.

The appointment request is used to create the appointment. An appointment is considered having more information than
that, and since we don't want to overload the appointment model, we use the appointment request to store all
the information about the appointment.
[More details here](https://github.com/adamspd/django-appointment/blob/main/docs/models.md#appointmentrequest).

### Appointment

The appointment model is used to define the last step in the appointment scheduling.
A confirmed appointment is created when a client confirms an appointment request.
It includes the client information, appointment request details, and additional information such as phone number and
address.
[More details here](https://github.com/adamspd/django-appointment/blob/main/docs/models.md#appointment).

### Config

Hold the configuration settings for the appointment system such as slot duration, working hours, and buffer time
between appointments.
[More details here](https://github.com/adamspd/django-appointment/blob/main/docs/models.md#config).

### PaymentInfo

Contains payment information for an appointment, linked to a specific appointment.

The model provides several methods to access related appointment details, such as service name, price, currency, client
name, and email.
It also includes a method to update the payment status.

### EmailVerificationCode

The EmailVerificationCode model is used to represent an email verification code for a user when the email already exists
in the database.
Or when the user wants to change their email address.
The model includes a class method to generate a new verification code for a user.

### DayOff 🆕

The DayOff model is used to represent a day off for a staff member.
It includes the date and the staff member associated with the day off.

### WorkingHours 🆕

The WorkingHours model is used to represent the working hours for a staff member.
It includes the start and end times, and the staff member associated with the working hours.

---

## Configuration

Customizing your Django appointment scheduler is straightforward. In your Django project's `settings.py` file, you can
override the default configurations to tailor the application, according to your needs. Below is a breakdown of the
configurations:

### Essential Configurations:

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

#### New Configurations:

A new configuration has been added to the application to allow you to use Django Q for sending all emails. 
If you're already using Django Q to send email reminders, it is nice to set this configuration.

```python
USE_DJANGO_Q_FOR_EMAILS = False  # 🆕 Use Django Q for sending email reminders
```

### Django Default Settings Utilization:

The application leverages some of the default settings from your Django project.
Ensure these values (DEFAULT_FROM_EMAIL, TIME_ZONE) are set in your `settings.py` because they are used as:

```python
APP_DEFAULT_FROM_EMAIL = 'DEFAULT_FROM_EMAIL'  # Default email for sending notifications
APP_TIME_ZONE = 'TIME_ZONE'  # Ensure the TIME_ZONE is set to your desired timezone
```

### Deprecated Configurations:

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
