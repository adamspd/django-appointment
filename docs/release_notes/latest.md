# django-appointment 📦

**v3.16.0 🆕**

## ___Release Notes for Version 3.16.0___

## Introduction 📜

Version 3.16.0 adds Persian with the Jalali calendar, right-to-left pages and emails, several working hours on the
same day, the client's own time on the booking page, and a way to keep values from the moment a client books. It also
fixes the booking calendar graying out the wrong days in browsers west of UTC. It changes the database (run
`makemigrations appointment`) and adds one setting. **Please read the
[migration guide](../migration_guides/latest.md) before upgrading.**

## New Features ✨

- **Several working hours on the same day.** Staff can split a day, for example 9:00 to 12:00 and 14:00 to 17:00, as
  long as the hours don't overlap. No slot is offered in the break, and a service can't run into it.
- **The client's own time.** When the client's time zone is not the site's, the booking page says so and shows the
  chosen slot in their time. The thank-you page and the client emails show it too, and the `.ics` file now carries the
  site's time zone.
- **Booking context.** The booking view sends a new `appointment_request_created` signal with the new request and the
  web request. A listener can keep values such as the campaign in the new `booking_context` field. Only the keys
  listed in the new `APPOINTMENT_BOOKING_CONTEXT_KEYS` setting can be stored (none by default). See
  [Keeping booking context](../booking-context.md).
- **Persian.** A Persian (`fa`) translation, which still needs a review by a native speaker. In Persian, pages and
  emails show dates in the Jalali (Solar Hijri) calendar with Persian digits, and the booking and staff calendars show
  Jalali months. The day off, unavailability and working hours forms get Jalali date lists and Persian digits instead
  of the browser's pickers. Dates are still stored as Gregorian dates.
- **Right-to-left languages.** In Arabic, Hebrew and Persian, the package's pages and emails are written right to left.
- **Larger prices.** A service's price and down payment, and an appointment's amount to pay, now go up to
  9,999,999,999.99. Before, the price stopped at 999,999.99 and the down payment at 9,999.99.

## Changes ⚙️

- **Dates follow the language.** Emails, the thank-you details and the reschedule page write dates with the language's
  format, like the booking page already did. Emails used one fixed format for every language, and the reschedule page
  wrote its date in English.
- **The staff calendar follows the language's week.** It starts the week on the language's first day, like the booking
  calendar, and shades the region's weekend instead of always Saturday and Sunday.
- **The base page's `lang`** follows the current language instead of always being `en`.
- Brazilian Portuguese, added in an earlier version, is now listed in the README and the internationalization guide.

## Bug Fixes 🐛

- **Booking calendar days west of UTC.** In browsers west of UTC, the booking calendar grayed out the wrong days (a
  Monday to Friday schedule showed Sunday and Monday as closed and Saturday as open). Days and "today" now follow the
  site's time zone. Fixes [#352](https://github.com/adamspd/django-appointment/issues/352) and
  [#305](https://github.com/adamspd/django-appointment/issues/305).

## Getting Started 🚀

### Installation 📥:

```bash
pip install django-appointment==3.16.0
python manage.py makemigrations appointment
python manage.py migrate
python manage.py collectstatic
```

## Previous Version Highlights 🔙

- [Release notes for version 3.15.0](v3_15_0.md)
- [Release notes for version 3.14.2](v3_14_2.md)

## Support & Feedback 📞

Feedback is welcome. For support, documentation, and further details, please refer to the
[documentation site](https://django-appt-doc.adamspierredavid.com/) or open an issue on
[GitHub](https://github.com/adamspd/django-appointment/issues). To report a security issue, please follow the
[security policy](https://github.com/adamspd/django-appointment/security/policy) instead of opening a public issue.
