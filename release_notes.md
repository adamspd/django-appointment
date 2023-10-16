# django-appointment 📦

**v2.0.0 🆕**

## ___Release Notes for Version 2.0.0___

## Introduction 📜

Version 2.0.0 brings significant enhancements to the django-appointment package, with major features such as staff
member management, working hours, and days off, alongside improvements in the configuration settings for added
flexibility. This release not only refines the user experience but also provides administrators and staff with more
control and customization.

⚠️ **Important Note**: This version introduces significant database schema changes. Before updating, ensure you follow
the migration steps outlined in
the [migration guide](https://github.com/adamspd/django-appointment/tree/main/migration_guide_v2.0.0.md).

## New Features ✨

### Staff Member Management 🧑‍💼

- Introduced a new `StaffMember` model linked to a user, representing a staff member offering services, detailing their
  services, working hours, and weekend availability.
- Admin features allowing for creating, removing, and converting superusers to staff members.
- Provided the ability for staff members to view and update their profiles, including email change verification for
  added security.

### Service Management 🛠

- Superusers can now add, update, or delete services from the system, ensuring the list of services remains relevant and
  up-to-date.

### Days Off and Working Hours Management 🕰

- Implemented `DayOff` and `WorkingHours` models to manage staff availability.
- Staff members can specify days they're not available and define their standard working hours, providing more accurate
  availability information for appointment scheduling.
- Superusers have the capability to manage these settings for any staff member.

### Enhanced Configuration Settings ⚙️

- New configurations added to customize buffer time between the current time and the first available slot for the day.
- Staff members can now define their own configuration settings for slot duration, working hours, and buffer time.
  However, only superusers have the privilege to add/remove services.
- Deprecated the `APPOINTMENT_CLIENT_MODEL` setting in favor of a more flexible approach with `AUTH_USER_MODEL`.

### Continued Integration and Responsiveness 🌐

- Continued integration of the django-phonenumber-field for efficient phone number handling.
- Improved responsiveness of the client information request page for better user experience across devices.

## Bug Fixes 🐛

No major bug fixes in this release.

## Updates 🔄

No additional updates in this release.

## Previous Version Highlights (1.1.2) 🔙

Please refer to the release notes for version 1.1.2 for details on username handling fixes, email template updates,
testing enhancements, and other core features.

## Getting Started 🚀

If you're upgrading from a previous version or installing for the first time, follow the instructions below:

### Installation 📥:

```bash
pip install django-appointment==2.0.0
```

### Database Migration 🔧:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Support & Feedback 📞

We value your feedback and are committed to continuous improvement. For support, documentation, and further details,
please refer to the provided resources.

## Conclusion 🎉

Version 2.0.0 introduces comprehensive features and enhancements to make the appointment scheduling process more robust,
user-friendly, and customizable. With the addition of staff management capabilities, more precise working hours, and
day-off settings, this release guarantees a refined experience for both administrators and end-users.

For detailed documentation and instructions on how to use the package, please refer to the accompanying README files and
online resources.
