# Appointment Scheduler

Appointment Scheduler is a Django app designed for managing appointment scheduling with ease and flexibility. It allows
users to define custom configurations for time slots, lead time, and finish time, or use the default values provided.
The app also handles conflicts and availability for appointments, ensuring a smooth user experience.

Detailed documentation is in the "docs" directory.

## Features

1. Customizable time slots, lead time, and finish time.
2. Handles appointment conflicts and availability.
3. Easy integration with Django admin interface for appointment management.
4. User-friendly interface for viewing available time slots and scheduling appointments.

## Quick start

1. Add "appointment" to your INSTALLED_APPS setting like this:

```python
INSTALLED_APPS = [
    '...',
    'appointment',
]
```

2. Include the appointment URLconf in your project urls.py like this:

```python
from django.urls import path, include

urlpatterns = [
    '...',
    path('appointment/', include('appointment.urls')),
]
```

3. Run `python manage.py migrate` to create the appointment models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create appointments, manage configurations, and handle appointment conflicts (you'll need the Admin app enabled).

5. You have to create at least a service before using the application in the admin page. If your service is free, add 0
   as the price. If you want to charge for your service, add the price in the price field. You can also add a
   description
   for your service.

6. Visit http://127.0.0.1:8000/appointment/request/<service_id>/ to view the available time slots and schedule an
   appointment.

## Customization

1. In your Django project's settings.py, you can override the default values for the appointment scheduler:

```python
APPOINTMENT_SLOT_DURATION = 30  # minutes
APPOINTMENT_LEAD_TIME = (9, 0)  # (hour, minute) 24-hour format
APPOINTMENT_FINISH_TIME = (16, 30)  # (hour, minute) 24-hour format

# Additional configuration options
APPOINTMENT_CLIENT_MODEL = 'auth.User'
APPOINTMENT_BASE_TEMPLATE = 'base_templates/base.html'
APPOINTMENT_WEBSITE_NAME = 'Website'
APPOINTMENT_PAYMENT_URL = None
APPOINTMENT_THANK_YOU_URL = None
```

2. Modify these values as needed for your application, and the scheduler will adapt to the new settings.

3. To further customize the app, you can extend the provided models, views, and templates or create your own.

## Support

For support or questions regarding the Appointment Scheduler app, please refer to the documentation in the "docs"
directory or visit the GitHub repository for more information.
