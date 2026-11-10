# Django Appointment 📦

![Tests](https://github.com/adamspd/django-appointment/actions/workflows/tests.yml/badge.svg)
![Published on PyPi](https://github.com/adamspd/django-appointment/actions/workflows/publish.yml/badge.svg)
[![Doc](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/adamspd/d52b1c6c561ebbf94ddc2a8b52561908/raw/django-appointment-doc-status.json)](https://django-appt-doc.adamspierredavid.com)
[![Current Release Version](https://img.shields.io/github/release/adamspd/django-appointment.svg?style=flat-square&logo=github)](https://github.com/adamspd/django-appointment/releases)
[![pypi Version](https://img.shields.io/pypi/v/django-appointment.svg?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/django-appointment/)
[![PyPi downloads](https://static.pepy.tech/personalized-badge/django-appointment?period=total&units=international_system&left_color=grey&right_color=orange&left_text=pip%20downloads)](https://pypi.org/project/django-appointment/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/commits/main)
[![GitHub last commit](https://img.shields.io/github/last-commit/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/commit/main)
[![GitHub issues](https://img.shields.io/github/issues/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/graphs/contributors)
[![GitHub stars](https://img.shields.io/github/stars/adamspd/django-appointment)](https://github.com/adamspd/django-appointment/stargazers)
[![Django compatible version](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/adamspd/django-appointment/main/django_compatible.json)](https://github.com/adamspd/django-appointment/blob/main/compatibility_matrix.md)
[![Python compatible version](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/adamspd/django-appointment/main/python_compatible.json)](https://github.com/adamspd/django-appointment/blob/main/compatibility_matrix.md)
[![Latest on Django Packages](https://img.shields.io/badge/Django%20Packages-django--appointment-8c3c26.svg)](https://djangopackages.org/packages/p/django-appointment/)

Django-Appointment is a Django app for booking appointments. You choose how your days are split into time slots, when
bookings open and close, and how much rest staff get between appointments, or you keep the defaults. The app handles
conflicts and availability for you, so clients only ever see slots that are actually free.

## 👀 Try the demo first

**The quickest way to understand the app is to play with the [live demo](https://django-appt.adamspierredavid.com/).**

It takes a couple of minutes, and it will make the rest of this README (and the configuration options) much easier to
follow. In the demo you can see:

- 📅 how clients book an appointment,
- ⚙️ how the admin settings change what clients see,
- 📧 the email notifications in action,
- 🔄 how conflicts and availability are handled.

### A small favor about emails 🙏

The demo sends real emails. Please use **your real email address**, or, if you'd rather not share yours or don't care
about the emails, use the shared address **`okfiw@thenightcoders.tech`**.

Please don't make up an address. Emails sent to addresses that don't exist bounce back, and if too many bounce, email
providers like Gmail and Yahoo start treating the demo's mail server as spam. If that happens, I'll have to take the
demo offline for everyone. I keep an eye on those bounces, so thank you for helping keep the demo up!

**Your privacy:** the demo database is wiped every 2 hours. I don't keep or use your email address.

*Please read the [terms of use](https://django-appt.adamspierredavid.com/terms-and-conditions/) before using the demo.*

## Documentation 📚

- 📖 [Documentation site](https://django-appt-doc.adamspierredavid.com/): why you'd use the app, its features, and
  every configuration option.
- 🧭 [Tutorial](https://django-appt-doc.adamspierredavid.com/tutorial/): a step-by-step walkthrough of a working setup.
- 📝 Release notes: on the [documentation site](https://django-appt-doc.adamspierredavid.com/release_notes/latest/),
  the [GitHub releases page](https://github.com/adamspd/django-appointment/releases), and, for older versions, in
  [`docs/release_notes`](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes).
- 🕰️ Features added in earlier versions: [`docs/history`](https://github.com/adamspd/django-appointment/tree/main/docs/history).

> ⚠️ **Upgrading from a version older than 2.0.0?** Version 2.0.0 changed the database a lot. Please read the
> [migration guide](https://github.com/adamspd/django-appointment/tree/main/docs/migration_guides/v2_1_0.md) before
> you update. For later versions, see the
> [migration guides folder](https://github.com/adamspd/django-appointment/tree/main/docs/migration_guides).

## Features ✨

1. Customizable time slots, lead time (when bookings open each day) and finish time (when they close).
2. Conflict and availability handling, so clients are only offered slots that are free.
3. Integration with the Django admin.
4. Dedicated staff pages to manage appointments, staff members, services, working hours, days off and conflicts.
5. A friendly booking page where clients see the free slots and book one.
6. Email notifications:
   - a confirmation email to the client as soon as they book,
   - an optional reminder email 24 hours before the appointment (needs Django Q, see below),
   - an ICS attachment so clients can add the appointment to their calendar.
7. Clients can reschedule their appointment, if you allow it.
8. **Custom templates**: replace the default pages and emails with your own designs. See the
   [custom templates guide](https://github.com/adamspd/django-appointment/blob/main/CUSTOM_TEMPLATES.md).
9. Slots that account for the real length of each service, plus an optional rest time between appointments (for
   everyone or per staff member).
10. Automatic cleanup of abandoned booking requests, also available as the `cleanup_appointment_requests` management
    command.
11. Per-day unavailability: a staff member can block part of a single day (a break, a meeting) without taking the
    whole day off, and the booking page hides those slots.

## Quick Start 🚀

Django-Appointment supports Python 3.11+ and Django 4.2+. See the
[compatibility matrix](https://github.com/adamspd/django-appointment/blob/main/compatibility_matrix.md) for the
exact combinations that are tested.

1. Install the package:

   ```bash
   pip install django-appointment
   ```

2. Add `appointment` to `INSTALLED_APPS` in your `settings.py`:

   ```python
   INSTALLED_APPS = [
       # other apps
       'appointment',
   ]
   ```

3. Include the app's URLs in your project's `urls.py`:

   ```python
   from django.urls import path, include

   urlpatterns = [
       # other urls
       path('appointment/', include('appointment.urls')),
   ]
   ```

4. *(Optional)* Set your website's name in `settings.py`. It is shown at the top of the emails sent to clients:

   ```python
   APPOINTMENT_WEBSITE_NAME = 'Chocolates'
   ```

   You can also set it later from the Django admin, in the app's configuration. The admin value wins over the setting.

5. Create and apply the migrations:

   ```bash
   python manage.py makemigrations appointment
   python manage.py migrate
   ```

6. Start the development server (`python manage.py runserver`) and log in to the Django admin at
   http://127.0.0.1:8000/admin/ (the admin app must be enabled).

7. Create at least one **service**. Use a price of `0` if it's free. A description and an image are optional.

8. Add at least one **staff member** who offers that service, and give them **working hours**. Without a staff
   member, the booking page has no slots to show. You can do this from the Django admin or from the staff pages at
   http://127.0.0.1:8000/appointment/app-admin/user-profile/.

9. Open http://127.0.0.1:8000/appointment/request/<service_id>/ to see the free slots and book an appointment.

The [tutorial](https://django-appt-doc.adamspierredavid.com/tutorial/) walks through these steps with screenshots.

### Using a custom user model

You don't need to do anything if you use Django's default user model. If you use your own
(`AUTH_USER_MODEL = 'client.UserClient'`, for example), keep in mind that the app creates an account for each new
client when they book. It calls your manager's `create_user` with keyword arguments and **no password**:

```python
# If your user model has a `username` field:
User.objects.create_user(username=..., email=..., first_name=..., last_name=...)

# Otherwise:
User.objects.create_user(email=..., first_name=..., last_name=...)
```

So your `create_user` must accept those arguments and work without a password. Once the booking is done, the client
gets an email with a link to set their password.

## Email and Django Q Configuration 📧

<!-- --8<-- [start:email-and-q] -->
### Email Configuration 📧

The app needs a working email setup to send confirmations and reminders. Add this to your `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your_smtp_host'
EMAIL_PORT = 587  # or 465 with EMAIL_USE_SSL
EMAIL_USE_TLS = True  # or EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_email_password'

# Optional: your website's name, shown at the top of the emails
APPOINTMENT_WEBSITE_NAME = 'Your Website Name'
```

To change the emails, see [Custom templates](https://django-appt-doc.adamspierredavid.com/custom-templates/): each
email can be overridden, with its subject and its plain-text part, and with `DEBUG = True` a superuser can preview them
all at `app-admin/email-preview/`.

> **Note:** In production, keep secrets like the email password in environment variables (or another secure store),
> not in `settings.py`.

### Django Q Configuration ⏰

Django-Appointment uses [Django Q](https://github.com/django-q2/django-q2) to send reminder emails at the right time
and to clean up abandoned booking requests every day. It's optional, but recommended.

#### Setting up Django Q

1. Install Django Q:
   ```bash
   pip install django-q2
   ```

2. Add `django_q` to `INSTALLED_APPS` in your `settings.py`:
   ```python
   INSTALLED_APPS = [
       # ...
       'django_q',
   ]
   ```

3. Configure Django Q in your `settings.py`:
   ```python
   Q_CLUSTER = {
       'name': 'django-appointment',
       'workers': 4,
       'timeout': 90,
       'retry': 120,
       'queue_limit': 50,
       'bulk': 10,
       'orm': 'default',
   }
   USE_DJANGO_Q_FOR_EMAILS = True  # optional: also send all the other emails in the background
   ```

4. Create Django Q's tables:
   ```bash
   python manage.py migrate
   ```

5. Start the Django Q cluster, and keep it running alongside your server:
   ```bash
   python manage.py qcluster
   ```

> **Note:** Without Django Q, the app works normally, but reminder emails are not sent and old booking requests are
> only cleaned up when you run `python manage.py cleanup_appointment_requests` yourself.
<!-- --8<-- [end:email-and-q] -->

## Template Configuration 📝

The app's pages don't come with their own navbar or footer: they render inside your site's base template. Tell the
app which template to use in `settings.py`:

```python
APPOINTMENT_BASE_TEMPLATE = 'base.html'  # used by the booking pages
APPOINTMENT_ADMIN_BASE_TEMPLATE = 'base.html'  # (optional) used by the staff pages, can be a different base
```

Every page of the app extends `appointment/layout.html`, which extends the base you set. Your base must include these
blocks:

```html
{% block customMetaTag %}
{% endblock %}

{% block customCSS %}
{% endblock %}

{% block title %}
{% endblock %}

{% block description %}
{% endblock %}

{% block body %}
{% endblock %}

{% block customJS %}
{% endblock %}
```

What each block is for:
- `customMetaTag` goes inside `<head>`: the staff pages put the CSRF token there for their AJAX requests.
- `customCSS` and `customJS` let the app add its styles and scripts.
- `body` is where each page's content goes, inside a `<div class="djappt">` wrapper. The app's CSS only applies inside
  that wrapper, so your navbar and footer keep their look.
- `title` and `description` are used for SEO. They're recommended but not required.

Your base must also load jQuery and Bootstrap 5 (CSS and JS) before the `customJS` block.

Here's an [example `base.html`](https://github.com/adamspd/django-appointment/blob/main/appointment/templates/base_templates/base.html).
It's the one used when you don't set `APPOINTMENT_BASE_TEMPLATE`.

## Customization 🔧

You can change the default values (slot duration, lead time, finish time, and more) in your `settings.py`, and the app
adapts to them. Most of them can also be changed from the Django admin, in the app's configuration, and the admin
value wins. The rest time between appointments is only set from the admin, for everyone or per staff member. The full
list is in the [configuration documentation](https://django-appt-doc.adamspierredavid.com/configuration/).

To go further, you can extend the provided models, views and templates, or write your own.

## Internationalization 🌍

Django-Appointment is translated and shows dates in the client's language.

**Languages:**
- English (en), the default
- French (fr), maintained by the project
- Spanish (es), contributed by @alexandermamaniy (new maintainers welcome!)

**What you get:**
- 🗣️ The interface translated into 3 languages (more are welcome!)
- 📅 Localized date formats for 39 languages
- 🌐 Automatic language detection
- 📝 Right-to-left (RTL) language support

**Quick setup:**
```python
# settings.py
USE_I18N = True
LANGUAGES = [('en', 'English'), ('fr', 'French'), ('es', 'Spanish')]

MIDDLEWARE = [
    # ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # after SessionMiddleware, before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

**Want to add your language or translate database content?**
👉 **[See the full Internationalization Guide](INTERNATIONALIZATION.md)**

## Docker Support 🐳

<!-- --8<-- [start:docker] -->
The repository comes with a Docker setup to try the app or work on it locally.

> **Note:** This setup is meant for **development and local testing**, and it runs from a clone of the repository.
> For production, follow Django's [deployment checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/).

1. **Clone the repository** and go into it:

   ```bash
   git clone https://github.com/adamspd/django-appointment.git
   # or, with SSH: git clone git@github.com:adamspd/django-appointment.git
   cd django-appointment
   ```

2. **Create a `.env` file** at the root of the repository. Fill in your own email server's details if you want emails
   to work:

   ```plaintext
   # Main admin user. To add more admins, change ADMINS in appointments/settings.py
   ADMIN_NAME="Super Admin"
   ADMIN_EMAIL=super.admin@example.com

   # Replace these 3 with your own, otherwise sending emails will fail
   EMAIL_HOST_USER=no-reply@example.com
   EMAIL_HOST_PASSWORD=youcantguessme
   EMAIL_HOST=smtp.example.com

   # The default backend, you can leave it as is
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

   # 587 for TLS. For SSL, use 465 and EMAIL_USE_SSL=True instead
   EMAIL_PORT=587
   EMAIL_USE_TLS=True

   # Django Q is already installed in the Docker image. Outside Docker, install django-q2 first
   USE_DJANGO_Q=True
   ```

   > **Note:** The `.env` file holds secrets. Don't commit it.

3. **Build and start the containers:**

   ```bash
   docker compose up -d --build
   ```

   > On older Docker installs, use `docker-compose` (with a hyphen) instead of `docker compose` in every command.

4. **Create and apply the migrations:**

   ```bash
   docker compose exec web python manage.py makemigrations appointment
   docker compose exec web python manage.py migrate
   ```

5. **Create a superuser** to log in to the Django admin:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. **Open the app** at http://localhost:8000 and the Django admin at http://localhost:8000/admin/. From there, add a
   service and a staff member by following the [tutorial](https://django-appt-doc.adamspierredavid.com/tutorial/).

7. **Stop the containers** when you're done:

   ```bash
   docker compose down
   ```

> **Note:** The Docker setup uses the project's default database (SQLite). To use another database, change the
> `Dockerfile` and `docker-compose.yml`.
<!-- --8<-- [end:docker] -->

## Compatibility Matrix 📊

The [compatibility matrix](https://github.com/adamspd/django-appointment/blob/main/compatibility_matrix.md) shows
which versions of Python and Django the package is tested against. It is updated with each round of compatibility
tests.

## Support 💬

Have a question? Start with the [documentation site](https://django-appt-doc.adamspierredavid.com/). If you've found a
bug or something isn't clear, please [open an issue](https://github.com/adamspd/django-appointment/issues).

## Contributing 🤝

Contributions are welcome! Please read the
[contributing guidelines](https://github.com/adamspd/django-appointment/tree/main/CONTRIBUTING.md) to get started.

If you find the project useful, a ⭐ on GitHub would mean a lot. It tells me people are using it and that it's worth
keeping it maintained. Thank you!

## Code of Conduct 📜

Please read the [code of conduct](https://github.com/adamspd/django-appointment/tree/main/CODE_OF_CONDUCT.md).

## Security Policy 🔒

Please read the [security policy](https://github.com/adamspd/django-appointment/tree/main/SECURITY.md), especially
before reporting a vulnerability.

## About the Author

Adams Pierre David - [Website](https://adamspierredavid.com/)
