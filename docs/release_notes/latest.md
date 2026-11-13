# django-appointment 📦

**v3.14.0 🆕** (≈ π, to three significant digits)

## ___Release Notes for Version 3.14.0___

## Introduction 📜

Version 3.14.0 adds Brazilian Portuguese 🇧🇷 and the first browser tests for booking. It is a small release with no
database change, no new setting and no change to the package's logic, so upgrading is a drop-in. The version number is
a happy coincidence: this release is 3.14, and I did not bake it, so there is no slice of Pi to share, only
translations. 🥧 It is also a rational number, unlike its famous neighbour, so it ends where it should: at 3.14.0.

## What's New ✨

- **Brazilian Portuguese (`pt-br`).** Thanks to [@FelipeCarvalhoS](https://github.com/FelipeCarvalhoS) for the
  translation. It covers the booking pages, the staff pages, the admin pages and every email, including the pages and
  emails added in 3.13 (staff account and set-password emails, the email preview, the verification code). To use it,
  add it to your `LANGUAGES` setting:

  ```python
  LANGUAGES = [
      ('en', 'English'),
      ('pt-br', 'Brazilian Portuguese'),
  ]
  ```

  The locale folder is `pt_BR`, as Django expects for `pt-br`.

## Under the Hood 🔧

These changes do not affect how the package works for you.

- **Browser tests for booking.** Thanks to [@trippiez](https://github.com/trippiez) for adding Playwright tests
  (Chromium, run in CI) for the two booking flows: a new client who verifies their email, and a signed-in client who
  books another slot. See `e2e/README.md`.
- **Updated dependencies.** The pinned versions of Django (6.1.3), phonenumbers (9.0.43), pytest and the documentation
  tools are up to date, and the GitHub Actions workflows use the latest action versions.
- **TestPyPI uploads skip files that already exist,** so a second push of the same version no longer fails the
  publishing workflow.

## Good to Know 📝

- If you set `LANGUAGES` yourself, nothing changes until you add `pt-br`.
- Spotted a wording that does not read right in Portuguese? Please open an issue or a pull request.

## Getting Started 🚀

### Installation 📥:

```bash
pip install django-appointment==3.14.0
```

No migration and no `collectstatic` run is needed for this release. The database keeps its shape: circumference and
diameter are unchanged. ⭕

## Previous Version Highlights 🔙

- [Release notes for version 3.13.1](v3_13_1.md)
- [Release notes for version 3.13.0](v3_13_0.md)

## Support & Feedback 📞

Feedback is welcome. For support, documentation, and further details, please refer to the
[documentation site](https://django-appt-doc.adamspierredavid.com/) or open an issue on
[GitHub](https://github.com/adamspd/django-appointment/issues).
