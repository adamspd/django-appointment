# Getting Started with Django-Appointment

Django-Appointment is a flexible Django app for managing appointment scheduling. This guide will walk you through the basic setup process.

## Installation

- Install Django-Appointment using pip:

   ```bash
   pip install django-appointment
   ```

- Add "appointment" to your `INSTALLED_APPS` in `settings.py`:

   ```python
   INSTALLED_APPS = [
       # other apps
       'appointment',
       'django_q',  # Optional: for email reminders
   ]
   ```

- Include the appointment URLconf in your project's `urls.py`:

   ```python
   from django.urls import path, include

   urlpatterns = [
       # other urls
       path('appointment/', include('appointment.urls')),
   ]
   ```

## Configuration

- In your `settings.py`, configure the user model (if using a custom one):

   ```python
   AUTH_USER_MODEL = 'your_app.YourUserModel'  # Optional if using Django's default user model
   ```

- Set the website name:

   ```python
   APPOINTMENT_WEBSITE_NAME = 'Your Website Name'
   ```

- For email reminders (optional), configure Django Q:

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

   # Optional: also send every other email through the cluster, not just the reminders.
   USE_DJANGO_Q_FOR_EMAILS = True
   ```

   Reminders only need `django_q` installed and a running cluster. `USE_DJANGO_Q_FOR_EMAILS` is separate: it moves
   the confirmation, verification and reschedule emails off the request cycle too.

For more configuration options, refer to [the configuration reference](configuration.md).

## Database Setup

- Create and apply migrations:

   ```bash
   python manage.py makemigrations appointment
   python manage.py migrate
   ```

- Start the Django Q cluster (if using email reminders):

   ```bash
   python manage.py qcluster
   ```

## Initial Setup

- Start your Django development server:

   ```bash
   python manage.py runserver
   ```

- Access the admin panel at `http://127.0.0.1:8000/admin/` to create services, manage configurations, and handle appointments.

- Create at least one service before using the application.

- Access the appointment booking page at `http://127.0.0.1:8000/appointment/request/<service_id>/`.

## Template Configuration

Ensure your base template includes the following blocks:

```html
{% block customCSS %}{% endblock %}
{% block title %}{% endblock %}
{% block description %}{% endblock %}
{% block body %}{% endblock %}
{% block customJS %}{% endblock %}
```

Note: At minimum, the `customCSS`, `body`, and `customJS` blocks are required. jQuery is also necessary for proper functionality.

## Customization

You can override default settings in your `settings.py`.

## Next Steps

- Explore the [admin interface](http://127.0.0.1:8000/admin/) to manage services, staff, and appointments.
- Customize the appearance and behavior by overriding templates and extending views.
- Implement additional features like payment integration or custom notifications.
