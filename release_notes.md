# django-appointment

**v1.1.2**

# Release Notes for Version 1.1.2

## Introduction

Version 1.1.2 continues the commitment to improving the package with bug fixes, enhancements, and updates to user communication. This release includes significant fixes for handling multiple usernames, slot availability, and a revised email template for appointment confirmations.

## Bug Fixes

### Slot Availability Fix

- Fixed an issue where booking the second slot did not correctly block the first slot if it was booked later. This fix ensures that both slots are handled correctly, and one does not affect the availability of the other.

### Username Handling Fix

- Addressed a situation where the creation of a username based on the email address could lead to a conflict if the username already existed. The fix introduces a suffix mechanism to handle multiple usernames and ensure uniqueness.

### Testing Enhancements

- Added specific tests to reproduce and verify the slot availability issue, strengthening the robustness of the codebase.
- Included tests to validate the unique username creation logic, improving code quality and reliability.

## Updates

### Email Template Update

- Updated the email template that is sent when an appointment is booked. The revised template provides a more concise and user-centric message, enhancing communication with clients.

## Previous Version Highlights (1.1.1)

Please refer to the release notes for version 1.1.1 for details on slot availability fixes, testing enhancements, and previous core features.

## Getting Started

If you haven't already installed the package, or if you're upgrading from a previous version, follow the instructions below:

### Installation:

```bash
pip install django-appointment==1.1.2
```

### Database Migration:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Support & Feedback

We value your feedback and are committed to continuous improvement. For support, documentation, and further details, please refer to the provided resources.

## Conclusion

Version 1.1.2 builds on previous releases with focused improvements and user communication enhancements. By addressing key issues in slot availability, username handling, and email template design, this release ensures a more seamless experience for both developers and users.

For detailed documentation and instructions on how to use the package, please refer to the accompanying README files and online resources.