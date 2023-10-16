# Django Appointment 📦

⚠️ **IMPORTANT**: Version 2.0.0 introduces significant database changes. Please read the [migration guide](https://github.com/adamspd/django-appointment/tree/main/migration_guide_v2.0.0.md) before updating.

Django-Appointment is a Django app engineered for managing appointment scheduling with ease and flexibility. It enables
users to define custom configurations for time slots, lead time, and finish time, or utilize the default values
provided. This app proficiently manages conflicts and availability for appointments, ensuring a seamless user
experience.

Detailed documentation can be found in the [docs](https://github.com/adamspd/django-appointment/tree/main/docs)
directory.
For changes and migration information, please refer to the release
notes [here](https://github.com/adamspd/django-appointment/tree/main/release_notes.md).

## Features ✨

1. Customizable time slots, lead time, and finish time.
2. Competent handling of appointment conflicts and availability.
3. Seamless integration with the Django admin interface for appointment management.
4. User-friendly interface for viewing available time slots and scheduling appointments.
5. Capability to send email notifications to clients upon scheduling an appointment.

## Added Features in version 2.0.0 🆕
- **Database Changes ⚠️**: Significant modifications to the database schema. Before updating, ensure you follow the migration steps outlined in the [migration guide](https://github.com/adamspd/django-appointment/tree/main/migration_guide_v2.0.0.md).
1. Introduced a staff feature allowing staff members in a team or system to manage their own appointments.
2. Implemented an admin feature panel enabling staff members and superusers (admins) to manage the system.
3. Added buffer time between the current time and the first available slot for the day.
4. Defined working hours for each staff member, along with the specific days they are available during the week.
5. Specified days off for staff members to represent holidays or vacations.
6. Staff members can now define their own configuration settings for the appointment system, such as slot duration,
   working hours, and buffer time between appointments. However, only admins have the privilege to add/remove services.

## Quick Start 🚀

1. Add "appointment" to your `INSTALLED_APPS` setting like so:

   ```python
   INSTALLED_APPS = [
       # other apps
       'appointment',
   ]
   ```

2. Incorporate the appointment URLconf in your project's `urls.py` like so:

   ```python
   from django.urls import path, include
   
   urlpatterns = [
       # other urls
       path('appointment/', include('appointment.urls')),
   ]
   ```

3. In your Django's `settings.py`, append the following:

   ```python
   AUTH_USER_MODEL = 'models.UserModel'  # Optional if you use Django's user model
   ```
   
   For instance, if you employ a custom user model:
   
   ```python
   AUTH_USER_MODEL = 'client.UserClient'
   ```
   
   If you're utilizing the default Django user model, there's no need to add this line since Django automatically sets it
   to:
   
   ```python
   AUTH_USER_MODEL = 'auth.User'
   ```
   
   Ensure your `create_user` function includes the following arguments, even if they are not all utilized:
   
   ```python
   def create_user(first_name, email, username, last_name=None, **extra_fields):
       pass
   ```
   
   This function will create a user with a password formatted as: f"{APPOINTMENT_WEBSITE_NAME}{current_year}"
   
   For instance, if you append this to your `settings.py`:
   
   ```python
   APPOINTMENT_WEBSITE_NAME = 'Chocolates'
   ```
   
   And the current year is 2023, the password will be "Chocolates2023". If `APPOINTMENT_WEBSITE_NAME` is not provided, the
   default value is "Website", rendering the password as "Website2023".
   
   This name is also utilized in the footer of the emails sent to clients upon scheduling an appointment:
   
   ```html
   <p>® 2023 {{ APPOINTMENT_WEBSITE_NAME }}. All Rights Reserved.</p>
   ```

4. Execute `python manage.py migrate` to create the appointment models.
5. Launch the development server and navigate to http://127.0.0.1:8000/admin/ to create appointments, manage
   configurations, and handle appointment conflicts (the Admin app must be enabled).
6. You must create at least one service before using the application on the admin page. If your service is free, input 0
   as the price. If your service is paid, input the price in the price field. You may also provide a description for
   your service.
7. Visit http://127.0.0.1:8000/appointment/request/<service_id>/ to view the available time slots and schedule an
   appointment.

## Customization 🔧

1. In your Django project's `settings.py`, you can override the default values for the appointment scheduler. More
   information regarding available configurations can be found in the
   documentation [here](docs/README.md#configuration).
2. Modify these values as needed for your application, and the app will adapt to the new settings.
3. For further customization, you can extend the provided models, views, and templates or create your own.

## Support 💬

For support or inquiries regarding the Appointment Scheduler app, please refer to the documentation in the "docs"
directory or visit the GitHub repository for more information.

## Notes 📝⚠️

Currently, the application does not send email reminders yet.