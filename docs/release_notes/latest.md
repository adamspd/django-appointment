# django-appointment 📦

**v3.13.0 🆕**

## ___Release Notes for Version 3.13.0___

## Introduction 📜

Version 3.13.0 is a maintenance and security release on top of 3.12.0. It moves the package to Pillow 13.0.0,
which fixes a long list of security vulnerabilities in the earlier versions, and, because Pillow 13 no longer runs
on Python 3.10, it drops Python 3.10.

There is no database change. See [Breaking Changes](#breaking-changes) and the
[migration guide](../migration_guides/latest.md) before upgrading.

## Security 🔒

- **Pillow 13.0.0 is now required.** Pillow 12.x and older have several known vulnerabilities, a few of them
  critical: buffer overflows and out-of-bounds reads in the JPEG, TIFF and WMF/EMF decoders, decompression bomb
  checks that can be bypassed, and denial of service through crafted PDF, BMP, GIF and other files. The package uses
  Pillow to check the image uploaded for a service (`Service.image`), so a crafted upload could reach those code
  paths. `install_requires` now asks for `Pillow>=13.0,<14.0`, so `pip` upgrades it for you. See
  [Pillow's 13.0.0 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html) for the full
  list.

## Improvements 📈

- Dependency updates: Pillow, Django, phonenumbers, python-dotenv, setuptools and pymdown-extensions.
- The CI test matrix, the compatibility matrix and the demo `Dockerfile` no longer use Python 3.10; the demo image
  now runs Python 3.12.

## Breaking Changes 🚨

- **Python 3.10 is no longer supported.** `python_requires` is now `>=3.11`. Python 3.10 reached end of life in
  October 2026, and Pillow 13 does not support it. If you are still on 3.10, stay on 3.12.0 until you can upgrade
  the interpreter, and keep in mind that it cannot get the Pillow security fixes.
- **Pillow 13.0 is the minimum.** If your project pins Pillow below 13.0, `pip` will refuse to install 3.13.0
  together with it. Raise or remove that pin.

## Getting Started 🚀

### Installation 📥:

```bash
pip install django-appointment==3.13.0
```

## Previous Version Highlights 🔙

- [Release notes for version 3.12.0](v3_12_0.md)
- [Release notes for version 3.11.0](v3_11_0.md)

## Support & Feedback 📞

Feedback is welcome. For support, documentation, and further details, please refer to the
[documentation site](https://django-appt-doc.adamspierredavid.com/) or open an issue on
[GitHub](https://github.com/adamspd/django-appointment/issues).
