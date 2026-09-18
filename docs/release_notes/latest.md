# django-appointment 📦

**v3.10.x 🆕**

## ___Release Notes for the 3.10 series___

## Introduction 📜

The 3.10 series is the largest set of changes since 3.0. It makes slot availability aware of how long a service
actually takes, lets you replace any page or email the package renders with your own template, tightens authorization
on appointment updates, adds Spanish, and keeps the database from filling up with abandoned appointment requests.

Version 3.10.1 follows 3.9.2; there is no separately published 3.9.3.

## New Features ✨

### Custom templates for pages and emails

Every HTML page and every email the package sends can now be replaced with your own template, without forking
anything. Drop a file with the expected name into `templates/custom/` or `templates/emails/` and it is used instead of
the packaged default; anything you don't provide keeps working as before.

Two new settings control where the package looks:

```python
APPOINTMENT_CUSTOM_TEMPLATES_DIR = 'custom'
APPOINTMENT_CUSTOM_EMAILS_DIR = 'emails'
```

See [Custom templates](../custom-templates.md) for the full list of names and the context each one receives.

### Flexible slot duration and gap time

Previously a service longer than the configured slot step could be double-booked, because availability was checked
against the slot step rather than the service's real duration. Slot calculation now accounts for the service duration,
and you can require a rest period between consecutive appointments.

New fields:

- `Config.default_to_service_duration` — when enabled (the default), every service uses its own duration when
  checking availability.
- `Service.use_service_duration_as_slot` — the per-service equivalent, consulted when the Config flag above is off.
- `Config.slot_gap_time` — required rest time in minutes between the end of one appointment and the start of the
  next.
- `StaffMember.slot_gap_time` — the per-staff-member override of that gap.

Addresses issues #261 and #57.

### Automatic cleanup of abandoned appointment requests

Appointment requests that never became an appointment are now deleted automatically. When `django_q` is in your
`INSTALLED_APPS` a daily task is scheduled for you on startup; otherwise you can run it yourself:

```bash
python manage.py cleanup_appointment_requests --dry-run
python manage.py cleanup_appointment_requests
```

The retention window is configurable with `APPOINTMENT_CLEANUP_DAYS` (default `7`). Confirmed appointments are never
touched.

### Spanish translation 🇪🇸

Spanish (`es`) is now bundled, contributed by a community member. It is not actively maintained — see the
[internationalization guide](../internationalization.md) — and maintainers would be very welcome.

Alongside it, two translation bugs were fixed: `forms.py` used `gettext` instead of `gettext_lazy`, so field
placeholders were always rendered in English, and email bodies were composed with `gettext`, so they were always sent
in English regardless of the active language.

### Smoother booking for logged-in users

- A logged-in user booking an appointment no longer has to go through email verification.
- `ClientDataForm` pre-fills and disables the identity fields for a logged-in user, and the appointment is created
  from `request.user` rather than from the submitted data.
- The address field is no longer required.
- Django messages stay on screen 5 seconds longer.

### Django 6 support

Django 6.0 and 6.1 are supported and covered by the compatibility matrix, which was reworked at the same time. The
supported range is now `Django>=4.2,<7.0` on Python 3.10 – 3.14. See the
[compatibility matrix](../compatibility.md).

## Bug Fixes 🐛

- **Security:** authorization is now enforced on appointment updates, so a staff member can no longer modify an
  appointment that isn't theirs (#426).
- Fixed service durations under a minute being mishandled by `formatTime` (#262).
- Fixed a local variable named `_` shadowing gettext's `_` in `views.py`, which broke translation in that module
  (#455).
- Fixed the name of the `areRequiredFieldsFilled()` JavaScript function.
- `send_verification_email` now accepts the `request`, so custom email templates can use context processors. The
  request is passed to all renderers.

## Improvements 📈

- The documentation site now lives in this repository under `docs/`, and is built with MkDocs Material.
- Dependency updates across the board: Pillow, phonenumbers, django-phonenumber-field, babel, icalendar, django-q2,
  python-dotenv, requests and setuptools.

## Breaking Changes 🚨

- None in the public API. The new model fields do require a migration — see the
  [migration guide](../migration_guides/latest.md).

## Getting Started 🚀

### Installation 📥:

```bash
pip install django-appointment==3.10.1
```

### Database Migration 🔧:

```bash
python manage.py makemigrations appointment
python manage.py migrate
```

## Previous Version Highlights 🔙

- [Release notes for version 3.0.1](v3_0_1.md)
- [Release notes for version 3.0.0](v3_0_0.md)

## Support & Feedback 📞

Feedback is welcome. For support, documentation, and further details, please refer to the
[documentation site](https://django-appt-doc.adamspierredavid.com/) or open an issue on
[GitHub](https://github.com/adamspd/django-appointment/issues).
