# django-appointment 📦

**v3.15.0 🆕**

## ___Release Notes for Version 3.15.0___

## Introduction 📜

Version 3.15.0 tightens the booking flow, the staff calendar and the email codes, and fixes several bugs found while
testing a full site from start to finish. It changes the database (run `makemigrations appointment`), adds two
settings and changes how rescheduling and email codes behave. **Please read the
[migration guide](../migration_guides/latest.md) before upgrading.**

## New Features ✨

- **Working hours for several days at once.** On the add working hours page, staff can now pick several days, and they
  all get the same hours. Days that already have working hours are shown crossed out.

## Changes ⚙️

### Booking

- **Only free slots can be booked.** The booking form and the final step both check that the chosen time is one of the
  staff member's free slots for that service. The end time now always follows the service's duration. If someone else
  takes the slot first, the client sees "This time is not available" and picks another one.
- **Unknown payment types fall back to full payment.**
- **Booking pages show names and messages as text.** Service names, staff names and server messages are no longer read
  as HTML on the booking page.

### Email codes

- **Codes expire and work once.** A code is valid for `APPOINTMENT_VERIFICATION_CODE_MINUTES` (10 by default), is
  replaced by the next code sent, and stops working after 5 wrong tries.
- **New clients get an account only after entering the code.** Before, the account was created as soon as the form was
  sent.
- **At most 3 codes per address in an hour.** The same message is shown whether the address has an account or not.
- **Staff and superusers are not logged in by a booking code.** Their booking is still made; they log in with their
  password.
- **Email change codes are tied to the user and the new address.** The email only changes when the code sent to the new
  address is entered. Emails are compared without case.

### Rescheduling

- **Confirming a reschedule takes a click.** The link in the email opens a page with a Confirm button, so mail scanners
  that open links no longer confirm it.
- **The reschedule limit counts confirmed reschedules.** It used to count only the last few minutes. The service's own
  limit applies when rescheduling is allowed on the service, otherwise the default limit from the settings.
- **The service and, unless allowed, the staff member stay the same.** The new time must be a free slot. Only the latest
  pending request is kept.

### Staff calendar

- Staff can only create, move and delete appointments in their own calendar. Only a superuser can change a client's
  email.
- Calendar requests check their input and return 400, 403 or 404 instead of an error page. Deleting an appointment
  needs a POST.

### Links in emails

- **New `APPOINTMENT_SITE_URL` setting.** When set, every link in emails uses it instead of the request's address. Also
  make sure `ALLOWED_HOSTS` lists your real domain names.

### Logs

- Logs show ids instead of tokens and email addresses.

## Bug Fixes 🐛

- **Emails on Django 6.1 with `MAILERS`.** New Django 6.1 projects set `MAILERS` instead of the `EMAIL_*` settings,
  and the package then sent no email at all. It now sends them with either setup.
- **Empty settings no longer break slots and profiles.** Once the settings row existed with empty values (it is created
  on the first reschedule), the slot list and the staff profile page failed. They now fall back to
  `APPOINTMENT_SLOT_DURATION` and `APPOINTMENT_BUFFER_TIME`.
- **Editing an appointment in the calendar works for staff who are not superusers.**
- **Changing your email from the profile page** no longer returns an error.
- **Moving working hours onto a day that already has them** now shows an error instead of failing.
- **Refused staff pages answer with the right status.** Another staff member's profile returned the 403 page with a 200
  status, and another staff member's appointment showed a "page not found" page.
- **A pending move to another staff member** no longer blocks the wrong staff member's slot.

## Getting Started 🚀

### Installation 📥:

```bash
pip install django-appointment==3.15.0
python manage.py makemigrations appointment
python manage.py migrate
python manage.py collectstatic
```

## Previous Version Highlights 🔙

- [Release notes for version 3.14.2](v3_14_2.md)
- [Release notes for version 3.14.0](v3_14_0.md)

## Support & Feedback 📞

Feedback is welcome. For support, documentation, and further details, please refer to the
[documentation site](https://django-appt-doc.adamspierredavid.com/) or open an issue on
[GitHub](https://github.com/adamspd/django-appointment/issues). To report a security issue, please follow the
[security policy](https://github.com/adamspd/django-appointment/security/policy) instead of opening a public issue.
