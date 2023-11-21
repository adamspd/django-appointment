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

⚠️ **IMPORTANT**: If upgrading from a version before 2.0.0, please note significant database changes were introduced in
Version 2.0.0 introduces significant database changes. Please read
the [migration guide](https://github.com/adamspd/django-appointment/tree/main/docs/migration_guides/v2_1_0.md) before
updating.

Django-Appointment is a Django app engineered for managing appointment scheduling with ease and flexibility. It enables
users to define custom configurations for time slots, lead time, and finish time, or utilize the default values
provided. This app proficiently manages conflicts and availability for appointments, ensuring a seamless user
experience.

Detailed documentation can be found in
the [docs' directory](https://github.com/adamspd/django-appointment/tree/main/docs/README.md).
For changes and migration information, please refer to the [release
notes](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/latest.md).

## Features ✨

1. Customizable time slots, lead time, and finish time.
2. Competent handling of appointment conflicts and availability.
3. Seamless integration with the Django admin interface for appointment management.
4. User-friendly interface for viewing available time slots and scheduling appointments.
5. Capability to send email notifications to clients upon scheduling an appointment.

## Key features introduced in previous versions.

- For more information, please refer to
  this [documentation](https://github.com/adamspd/django-appointment/tree/main/docs/history/readme_v2_1_1.md).

## Added Features in version 2.1.3

This release of Django Appointment brings a series of improvements and updates aimed at enhancing the overall
functionality and user experience:

1. **Dynamic Label Customization in Appointment Pages (#19)**:
    - Added a new configuration option `app_offered_by_label` to the `Config` model.
    - This feature allows for dynamic labeling in the appointment HTML page to showcase the staff members or services
      offering the appointment.
    - The default value is "Offered by", which can be customized to fit different contexts, such as "Provided by" or "
      Choose Photographer" for photography services.

2. **Updated Documentation and Workflow Enhancements (#25, #26, #27)**:
    - Improved clarity and consistency in the project's documentation, making it more accessible and user-friendly.
    - Updated workflow processes to streamline development and issue tracking.

3. **Community Engagement and Standards (#21, #22, #23, #24)**:
    - Introduced a `CODE_OF_CONDUCT.md` to foster a respectful and inclusive community environment.
    - Created `CONTRIBUTING.md` to guide contributors through the process of making contributions to the project.
    - Established a `SECURITY.md` policy to address security protocols and reporting.
    - Refined issue templates for bug reports and feature requests, enhancing the efficiency of community contributions
      and feedback.

4. **Library Updates and Security Patches (#14, #15, #18)**:
    - Updated dependencies such as `phonenumbers` and `django` to their latest versions, ensuring better performance and
      security.

5. **Enhanced Project Visibility (#16)**:
    - Added GitHub Badges to the README for better visibility and quick access to project metrics like build status,
      versioning, and contribution activities.

6. **Translation Refinements (#31)**:
    - Removed inconsistencies in translations, improving the internationalization aspect of the application.

These updates collectively contribute to the robustness and versatility of the Django Appointment package, aligning with
our commitment to providing a high-quality and user-friendly appointment management solution.

### Breaking Changes in version 2.1.2:

- None

### New Features  & Bug Fixes 🆕

See the [release notes](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/latest.md)
for more information.

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

## Customization 🔧

1. In your Django project's `settings.py`, you can override the default values for the appointment scheduler. More
   information regarding available configurations can be found in
   the [documentation](https://github.com/adamspd/django-appointment/tree/main/docs/README.md#configuration).
2. Modify these values as needed for your application, and the app will adapt to the new settings.
3. For further customization, you can extend the provided models, views, and templates or create your own.

## Support 💬

For support or inquiries regarding the Appointment Scheduler app, please refer to the documentation in the "docs"
directory or visit the GitHub repository for more information.

## Contributing 🤝

Contributions are welcome! Please refer to
the [contributing guidelines](https://github.com/adamspd/django-appointment/tree/main/CONTRIBUTING.md) for more
information.

## Code of Conduct 📜

Please refer to the [code of conduct](https://github.com/adamspd/django-appointment/tree/main/CODE_OF_CONDUCT.md) for
more information.

## Security policy 🔒

Please refer to the [security policy](https://github.com/adamspd/django-appointment/tree/main/SECURITY.md) for more
information.

## Notes 📝⚠️

Currently, the application does not send email reminders yet.

## About the Author

Adams Pierre David - [Website](https://adamspierredavid.com/)