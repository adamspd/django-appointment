# django-appointment 📦

**v3.14.2 🆕**

## ___Release Notes for Version 3.14.2___

## Introduction 📜

Version 3.14.2 is a security release. It fixes a permission check that let a staff member change the date and time of
another staff member's appointments. It also includes the date format fix from 3.14.1 and better Brazilian Portuguese
wording. There is no database change and no new setting, so upgrading is a drop-in. **Please upgrade.**

## Security 🔒

- **Staff members can only reschedule their own appointments**
  ([GHSA-pp78-hqpw-28pf](https://github.com/adamspd/django-appointment/security/advisories/GHSA-pp78-hqpw-28pf),
  CVE-XXXX-XXXXX). The endpoint used to drag an appointment to a new date and time in the staff calendar
  (`update_appt_date_time`) did not check who owned the appointment. Any staff member could move any other staff
  member's appointment by sending its id. It now returns a 403 unless the appointment belongs to the staff member, as
  the other appointment endpoints already did. Superusers can still reschedule any appointment.

  Only staff accounts could do this, so clients and visitors were never able to. No appointment data was exposed.
  Rated Moderate (CVSS 6.5). Thanks to [@p-w](https://github.com/p-w) for finding this, reporting it privately and
  writing the fix.

## Bug Fixes 🐛

- **Booking page in four languages** (from 3.14.1). The date formats for Portuguese, Finnish, Latvian and Vietnamese
  left some letters unescaped, such as the "e" in "de", so the booking page returned an error in those languages.

## Translations 🌍

- **Brazilian Portuguese.** Thanks to [@FelipeCarvalhoS](https://github.com/FelipeCarvalhoS) for making some sentences
  sound more natural and for using "dias de folga" everywhere for days off.

## Getting Started 🚀

### Installation 📥:

```bash
pip install django-appointment==3.14.2
```

No migration and no `collectstatic` run is needed for this release.

## Previous Version Highlights 🔙

- [Release notes for version 3.14.0](v3_14_0.md)
- [Release notes for version 3.13.1](v3_13_1.md)

## Support & Feedback 📞

Feedback is welcome. For support, documentation, and further details, please refer to the
[documentation site](https://django-appt-doc.adamspierredavid.com/) or open an issue on
[GitHub](https://github.com/adamspd/django-appointment/issues). To report a security issue, please follow the
[security policy](https://github.com/adamspd/django-appointment/security/policy) instead of opening a public issue.
