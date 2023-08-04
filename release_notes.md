# django-appointment

**v1.1.1**

# Release Notes for Version 1.1.1

## Introduction

Version 1.1.1 brings an important fix to the package, addressing a specific issue in slot availability. The update also
includes enhanced testing to ensure the integrity of the solution. This release builds on the previous versions,
focusing on reliability and responsiveness.

## Bug Fixes

### Slot Availability Fix

- Fixed an issue where booking the second slot did not correctly block the first slot if it was booked later. This fix
  ensures that both slots are handled correctly, and one does not affect the availability of the other.

### Testing Enhancements

- Added specific tests to reproduce and verify the slot availability issue, strengthening the robustness of the
  codebase.

## Previous Version Highlights (1.1.0)

Please refer to the release notes for version 1.1.0 for details on new models, user interface enhancements, code quality
improvements, and core features introduced in that version.

## Getting Started

If you haven't already installed the package, or if you're upgrading from a previous version, follow the instructions
below:

### Installation:

```bash
pip install django-appointment==1.1.0
```

### Database Migration:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Support & Feedback

We value your feedback and are committed to continuous improvement. For support, documentation, and further details,
please refer to the provided resources.

## Conclusion

Version 1.1.1 is a targeted update focusing on fixing a specific issue and enhancing the reliability of the package. By
addressing user-reported concerns and strengthening the testing framework, this release underscores our commitment to
providing a robust and dependable solution.

For detailed documentation and instructions on how to use the package, please refer to the accompanying README files and
online resources.