# django-appointment 📦

**v3.13.0 🆕**

## ___Release Notes for Version 3.13.0___

## Introduction 📜

Version 3.13.0 is a feature release on top of 3.12.0. It makes the package's pages and emails much easier to
override: every staff page gets the same context and named blocks, overrides can live in `admin/` and `booking/`
folders, the calendar and the forms take settings instead of script or widget changes, and every email gets the
appointment's objects, full links and a subject you can change from a template. A DEBUG-only page previews every
email. The release also fixes a booking form that failed without saying why, staff members refused on two of their
own pages, and a management command left out of the published package.

There is no database change. Read the [migration guide](../migration_guides/latest.md) if you override the staff
pages, the schedule forms or the emails.

## New Features ✨

### Easier staff page overrides 🧩

- **The same context everywhere.** Every staff page now gets `page_title`, `page_description` and `back_url` (where
  its **Back** link goes). The service pages also get `mode` (`create`, `edit` or `view`), the day off, working hours
  and unavailability forms get `form_action` (the URL they post to), the staff list gets `admin_is_staff`, and the
  profile page gets `profile_user`, the staff member it shows (`user` still holds it too, as before).
- **Named blocks.** The **Back** link, the title and the buttons next to it are in `djappt_back`, `djappt_heading`
  and `djappt_actions`. An override can extend the default page and replace only those.
- **Folders.** Overrides are looked for in `custom/admin/` (staff pages) and `custom/booking/` (client pages) first,
  then in `custom/` as before. An error page is looked for in the folder of the page that shows it.
- **Names.** The thank-you, set-password and verification pages now also accept their default template's name
  (`default_thank_you.html`, `set_password.html`, `enter_verification_code.html`). The older names still work.
- **Messages in one place.** Every page shows the Django messages through `appointment/_messages.html`. Override it to
  restyle them everywhere, or with an empty file when your base template already shows them.
- **One confirm dialog.** Every staff page has the confirm dialog and its script. A button opens it with
  `data-djappt-confirm="<url>"` and the `data-confirm-title`, `data-confirm-message` and `data-confirm-action` texts,
  and the dialog POSTs to that URL.

### Schedule forms with plain field names 🗓️

The working hours and unavailability forms now post the model's field names with ISO values (`date`, `start_time`,
`end_time`, `day_of_week`), which is what the browser's date and time inputs send. A wrong value comes back as JSON
with the errors per field (status 400), and the default pages show each one under its field instead of in a modal.
The old `date_raw`, `start_time_raw` and `end_time_raw` fields are still read.

### Calendar options 📅

`APPOINTMENT_CALENDAR_OPTIONS` sets the staff calendar's height (`'fill'`, `'auto'` or a number of pixels, with
`fillRatio`, `bottomOffset` and `minHeight` for `'fill'`) and passes any other key to FullCalendar (`initialView`,
`firstDay`...). A page with a footer no longer needs to redefine the height function. The appointment modal's Close
button and field wrappers are now found by `data-djappt="close"` and `data-djappt="field"`.

### Forms that follow your styles 📝

- `APPOINTMENT_FORM_CLASSES` swaps the Bootstrap classes the package puts on its fields for yours, for example
  `{'form-control': 'input', 'form-select': 'select'}`.
- The service duration is two inputs, hours and minutes, instead of a text field to fill as `HH:MM:SS`.
- The services a staff member offers are checkboxes in the forms, so `{{ form.services_offered }}` draws them without
  extra work.
- The staff forms have short help texts; the longer ones stay in the Django admin.

### Emails 📧

- **The same context everywhere.** Every email now gets `company`, `site_url`, `current_year` and `dashboard_url`,
  and, when it is about an appointment, `appointment`, `appointment_request`, `service`, `staff_member`, `client`,
  `client_name`, `appointment_url` and `reschedule_url`. A template can now place the date or the service where it
  wants, and link to the appointment.
- **Full links in every email.** The links start with the address of the request that triggered the email. The staff
  notifications now get that request too, and a reminder keeps the address of the booking it was scheduled from.
- **Subjects from templates.** A `<name>.subject.txt` file next to an email template replaces its subject.
- **Default HTML emails** for setting a staff password and for the verification code. They were plain text unless you
  wrote your own template.
- **A "View Appointment" button** in the new appointment and reminder emails sent to staff.
- **Email preview.** With `DEBUG = True`, superusers can open `app-admin/email-preview/` to see every email built for
  the latest appointment: the subject, the template used, and the HTML and text parts.

### Translations 🌍

The new strings are in French and Spanish.

## Good to Know 📝

- `{{ form.services_offered }}` now draws checkboxes instead of a multiple select, and `{{ form.duration }}` draws two
  inputs. Templates that loop over the choices, or post a single `duration` value, keep working.
- The password and verification emails now use the package's HTML templates when you have no override. Before, they
  were sent as plain text.
- In the admin copy of the reminder, `first_name` is now empty: it was the client's name, in an email that isn't
  addressed to them. The client's first name is in `client_first_name`.

## Bug Fixes 🐛

- **The booking details form failed without a message.** A rejected field, such as a phone number in the wrong
  format, reloaded the page with nothing shown, so the **Finish** button seemed to do nothing. Each field now shows its
  error, with a summary at the top.
- **Staff members were refused on their own pages.** `add-staff-member/` and `update-user-info/` without an id
  answered `403` to a staff member. They now mean the logged-in user, like the delete URLs since 3.12.
- **The `cleanup_appointment_requests` command was missing.** Its folders had no `__init__.py`, so the published
  package left it out although the docs describe it.
- **A day off with an empty date crashed.** It gave a `500`; the form errors are now returned.
- **Working hours on Sunday were rejected.** Day `0` was read as "no day".
- **The reminder's two copies could share one context.** The admin copy changed the context after the client's email
  was queued; each copy now has its own.

## Breaking Changes 🚨

None. Every change keeps the old names, fields and folders working. See "Good to Know" for what looks different.

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
