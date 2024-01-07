# django-appointment 📦

**v3.0.1 🆕**

## ___Release Notes for Version 3.0.1___

## Introduction 📜

Version 3.0.1 of django-appointment brings further refinements to the package, focusing on enhancing user interactions
within the administration panel, better error handling, and new AJAX-based functionalities. This minor version release
ensures a smoother experience for both staff members and superusers.

## New Features ✨

### Enhanced AJAX Functionality for Staff Members

- Added AJAX-based checks to determine if the logged-in user is a staff admin, enhancing overall system security and
  usability.

### Improved Error Handling and User Feedback

- Implemented better error handling in `fetchServices` and `populateServices` functions, ensuring users are adequately
  informed about the absence of services.
- Enhanced user experience by providing clearer error messages for staff members who do not offer any services or do not
  have a staff member profile.

### JavaScript Enhancements

- Added a new state `isUserStaffAdmin` in `AppState` to manage user roles more effectively within the admin panel.
- Updated the JavaScript code in `staff_index.js` to include new checks and functions for better management of user
  roles and permissions.

## Bug Fixes 🐛

- Fixed an issue where users without a `StaffMember` instance could attempt actions they were not permitted to, such as
  creating appointments.
- Addressed a bug where the absence of services offered by a staff member led to unhandled exceptions.

## Improvements 📈

- Enhanced `fetch_service_list_for_staff` view to handle cases where a user is a superuser but does not have
  a `StaffMember` instance.
- Improved the user interface to prevent actions (like right-click events for creating new appointments) for users who
  are not staff members.

## Breaking Changes 🚨

- No breaking changes introduced in this version.

## Previous Version Highlights (3.0.0) 🔙

- Version 3.0.0 introduced dynamic appointment management, user interface enhancements, dynamic label customization,
  updated documentation, library updates, and more.
- For a complete list of features and updates in the previous version, refer
  to [release notes for version 3.0.0](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/v3_0_0.md).

## Getting Started 🚀

If you're upgrading from a previous version or installing for the first time, follow the instructions below:

### Installation 📥:

```bash
pip install django-appointment==3.0.1
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

Version 3.0.0 continues our commitment to providing a robust and user-friendly appointment management solution. With
these updates, Django Appointment becomes more adaptable, secure, and community-focused.