# django-appointment 📦

**v2.1.2 🆕**

## ___Release Notes for Version 2.1.2___

## Introduction 📜

Version 2.1.2 of django-appointment introduces a series of refinements and updates, enhancing both the functionality and
the user experience. This release focuses on improving documentation, workflow, community engagement, and
internationalization, alongside some crucial library updates and new dynamic features.

## New Features ✨

### Dynamic Label Customization in Appointment Pages (#19)

- Added a new configuration option `app_offered_by_label` in the `Config` model.
- Enables dynamic labeling in the appointment HTML page, showcasing the staff members or services offering the
  appointment.
- Default label is "Offered by", customizable to suit different service contexts.

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

### Breaking Changes 🚨

- None

## Previous Version Highlights (2.1.1) 🔙

- For details on the previous version's features and updates, please refer
  to [release notes for version 2.1.1](https://github.com/adamspd/django-appointment/tree/main/docs/release_notes/v2_1_1.md).

## Getting Started 🚀

If you're upgrading from a previous version or installing for the first time, follow the instructions below:

### Installation 📥:

```bash
pip install django-appointment==2.1.0
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

Version 2.1.2 continues our commitment to providing a robust and user-friendly appointment management solution. With
these updates, Django Appointment becomes more adaptable, secure, and community-focused.
