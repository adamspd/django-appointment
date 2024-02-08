# Django Appointment 📦

![Tests](https://github.com/adamspd/django-appointment/actions/workflows/tests.yml/badge.svg)
![Published on PyPi](https://github.com/adamspd/django-appointment/actions/workflows/publish.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/django-appointment.svg)](https://badge.fury.io/py/django-appointment)
[![codecov](https://codecov.io/gh/adamspd/django-appointment/branch/main/graph/badge.svg?token=ZQZQZQZQZQ)](https://codecov.io/gh/adamspd/django-appointment)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/commits/main)
[![GitHub last commit](https://img.shields.io/github/last-commit/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/commit/main)
[![GitHub issues](https://img.shields.io/github/issues/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/graphs/contributors)

⚠️ **IMPORTANT**: If upgrading from a version before 2.x.x, please note significant database changes were introduced in
Version 2.0.0 introduces significant database changes. Please read
the [migration guide](https://github.com/adamspd/django-appointment/tree/main/docs/migration_guides/v2_1_0.md) before
updating. No database changes were introduced in version 3.0.1.

Django-Appointment is a Django app engineered for managing appointment scheduling with ease and flexibility. It enables
users to define custom configurations for time slots, lead time, and finish time, or utilize the default values
provided. This app proficiently manages conflicts and availability for appointments, ensuring a seamless user
experience.

For a detailed walkthrough and live example of the system, please refer to 
[this tutorial](https://github.com/adamspd/django-appointment/tree/main/docs/explanation.md).

Detailed documentation can be found in
the [docs' directory](https://github.com/adamspd/django-appointment/tree/main/docs/README.md).
For changes and migration information, please refer to the [release
notes](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/latest.md).

## Features ✨

1. Customizable time slots, lead time, and finish time.
2. Competent handling of appointment conflicts and availability.
3. Seamless integration with the Django admin interface for appointment management.
4. Custom admin interface for managing appointment/staff member editing, creation, availability, and conflicts.
5. User-friendly interface for viewing available time slots and scheduling appointments.
6. Capability to send email notifications to clients upon scheduling an appointment.

## Key features introduced in previous versions.

- For more information, please refer to
  this [documentation](https://github.com/adamspd/django-appointment/tree/main/docs/history/readme_v2_1_1.md).

## Added Features in version 3.0.1

This release of Django Appointment brings a series of improvements and updates aimed at enhancing the overall
functionality and user experience:

1. **Dynamic Appointment Management (#49, #55)**

2. **User Interface Enhancements and JavaScript Refactoring (#55)**

3. **Dynamic Label Customization in Appointment Pages (#19)**

4. **Updated Documentation and Workflow Enhancements (#25, #26, #27)**

5. **Community Engagement and Standards (#21, #22, #23, #24)**

6. **Library Updates and Security Patches (#14, #15, #18)**

7. **Enhanced Project Visibility (#16)**

8. **Translation Refinements (#31)**

9. **Bug Fixes (#48)**

See more at the [release notes](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/latest.md).

These updates collectively contribute to the robustness and versatility of the Django Appointment package, aligning with
our commitment to providing a high-quality and user-friendly appointment management solution.

### Bug Fixes 🆕

See the [release notes](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/latest.md)
for more information.

### Breaking Changes in version 3.0.1:

See the [release notes](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/latest.md) for more
  information.

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

   If you're utilizing the default Django user model, there's no need to add this line since Django automatically sets
   it to:

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

   And the current year is 2023, the password will be "Chocolates2023". If `APPOINTMENT_WEBSITE_NAME` is not provided,
   the default value is "Website", rendering the password as "Website2023".

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
