# django-appointment 📦

**v2.1.5 🆕**

## ___Release Notes for Version 2.1.5___

## Introduction 📜

Version 2.1.5 of django-appointment introduces a series of refinements and updates, enhancing both the functionality and
the user experience. This release focuses on improving documentation, workflow, community engagement, and
internationalization, alongside some crucial library updates and new dynamic features.

## New Features ✨

### Dynamic Appointment Management

- AJAX-based appointment creation and update functionalities.
- Enhanced endpoints for efficient appointment management.

### User Interface Enhancements and JavaScript Refactor

- Major updates to staff_index.js for improved interactivity and responsiveness.
- New CSS for a more responsive and user-friendly interface in appointment and calendar views.

### Dynamic Label Customization in Appointment Pages (#19)

- Added a new configuration option `app_offered_by_label` to the `Config` model.
- This feature allows for dynamic labeling in the appointment HTML page to showcase the staff members or services
  offering the appointment.
- The default value is "Offered by", which can be customized to fit different contexts, such as "Provided by" or "
  Choose Photographer" for photography services.

### Updated Documentation and Workflow Enhancements (#25, #26, #27)

- Documentation has been made more user-friendly and clearer.
- Workflow processes updated for more streamlined development and issue tracking.

### Community Engagement and Standards (#21, #22, #23, #24)

- `CODE_OF_CONDUCT.md` introduced to foster a respectful and inclusive community environment.
- `CONTRIBUTING.md` created to guide contributors through the contribution process.
- `SECURITY.md` established for addressing security protocols and reporting.
- Issue templates for bug reports and feature requests refined for better community feedback and contributions.

### Library Updates and Security Patches (#14, #15, #18)

- Dependencies like `phonenumbers` and `django` updated to their latest versions for enhanced performance and security.

### Enhanced Project Visibility (#16)

- GitHub Badges added to the README for improved project metrics visibility like build status and versioning.

### Translation Refinements (#31)

- Inconsistencies in translations removed, improving the internationalization aspect.

### Provided an endpoint to delete an appointment (#49)

- Added an endpoint to delete an appointment. Either with an ajax call or a simple request.

## Bug Fixes 🐛

---

- Fixed a bug where a stack trace was displayed when a user that is staff but didn't have a staff member profile tried
  to access its appointment's page list (/app-admin/user-event/)

  #### Description of the bug
  If a staff (Django-related role) is authenticated and tries to retrieved this endpoint :
  `/app-admin/user-event/` he'll get the following error if debug = true
    ```
      Traceback (most recent call last):
      File ".../django/core/handlers/exception.py", line 55, in inner
        response = get_response(request)
                   ^^^^^^^^^^^^^^^^^^^^^
      File ".../django/core/handlers/base.py", line 197, in _get_response
        response = wrapped_callback(request, *callback_args, **callback_kwargs)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File ".../appointment/decorators.py", line 26, in wrapper
        return func(request, *args, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File ".../appointment/decorators.py", line 39, in wrapper
        return func(request, *args, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File ".../appointment/views_admin.py", line 39, in get_user_appointments
        appointments = fetch_user_appointments(request.user)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File ".../appointment/services.py", line 44, in fetch_user_appointments
        staff_member_instance = user.staffmember
                                ^^^^^^^^^^^^^^^^
      File ".../django/utils/functional.py", line 268, in inner
        return func(_wrapped, *args)
               ^^^^^^^^^^^^^^^^^^^^^
      File ".../django/db/models/fields/related_descriptors.py", line 492, in __get__
        raise self.RelatedObjectDoesNotExist(
        client.models.UserClient.staffmember.RelatedObjectDoesNotExist: UserClient has no staffmember.
    ```
  If debug = false, the user will get a 500 error
  #### To Reproduce
  ##### Steps to reproduce the behavior:

      Create a user/account (user1)
      Login as admin/superuser (admin) and add user1 to staff.
      Login as user1 and go to /appointment/app-admin/user-event/
      See error

  #### Expected behavior
  Not an error but a redirection or anything more concise than just an error or a 5xx code return.

---

### Breaking Changes 🚨

- None

## Previous Version Highlights (2.1.1) 🔙

- For details on the previous version's features and updates, please refer
  to [release notes for version 2.1.1](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/v2_1_1.md).

## Getting Started 🚀

If you're upgrading from a previous version or installing for the first time, follow the instructions below:

### Installation 📥:

```bash
pip install django-appointment==2.1.5
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

Version 2.1.5 continues our commitment to providing a robust and user-friendly appointment management solution. With
these updates, Django Appointment becomes more adaptable, secure, and community-focused.
