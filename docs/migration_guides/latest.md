## Migration Guide for Version 3.12.0 🚀

Version 3.12.0 does **not** change the database: no model, field or constraint is added, renamed or removed, so there
is no migration to generate. What changes is how the pages and emails look and are built. If you use the package's
pages and emails as they are, upgrading is only a `pip install`. If you override its templates, link its stylesheets,
or call its delete URLs from your own code, read the steps below.

### Before you start: supported versions

| Declared in `setup.cfg` | 3.11.0 | 3.12.0 |
|---|---|---|
| `python_requires` | `>=3.10` | `>=3.10` |
| Django | `>=4.2,<7.0` | `>=4.2,<7.0` |
| `icalendar` | `~=6.3.1` | **`>=7.3,<8.0`** |

`pip` upgrades `icalendar` to 7.x for you. If your own code uses `icalendar` too, check it against
7.x. The [compatibility matrix](../compatibility.md) has the tested Python and Django combinations.

### Steps for Upgrading to Version 3.12.0:

1. **Backup Your Database**:
    - As a best practice, always back up your current database before an upgrade, even one without migrations.

2. **Update Package**:
    - Upgrade to the latest version by running:
      ```bash
      pip install --upgrade django-appointment
      ```

3. **Check there is nothing to migrate**:
    - The package does not ship migration files, so confirm your own ones are up to date:
      ```bash
      python manage.py makemigrations appointment --check --dry-run
      ```
    - It should report "No changes detected". If it proposes changes, they come from an earlier upgrade you have not
      migrated yet, not from 3.12.0: read that version's migration guide first.

4. **Collect the static files**:
    - The pages use new stylesheets and scripts (`css/djappt.css`, `css/booking.css`, `css/services.css`,
      `css/staff.css`, `js/app_admin/*.js`…). If your site serves collected static files, run:
      ```bash
      python manage.py collectstatic
      ```
    - Browsers may keep the old CSS for a while: reload with the cache disabled when you check the pages.

5. **Check your base templates**:
    - Every package page now extends `appointment/layout.html`, which extends your `APPOINTMENT_BASE_TEMPLATE` (client
      pages) or `APPOINTMENT_ADMIN_BASE_TEMPLATE` (staff pages) and wraps the page in `<div class="djappt">`. Your
      base must still load Bootstrap 5 (CSS and JS) and jQuery, and define the blocks the pages fill: `title`,
      `description`, `keyword`, `author`, `customMetaTag`, `customCSS`, `scriptHead`, `body` and `customJS`.
    - The package CSS only applies inside that wrapper, so it no longer restyles your navbar, footer or other pages.
      If one of your own pages relied on a package rule leaking out (a font, a margin on `body`), move that rule into
      your own CSS.
    - The staff profile page (`user-profile/<id>/`) sets `user` in its context to the staff member whose profile it
      is, as it always has. If your admin base shows the logged-in user or picks its links with `user`, switch those
      to `request.user`, or the sidebar shows the staff member instead of you on that page.

6. **Review your template overrides**:
    - Overrides are found exactly as before (`templates/appointment/…`, `templates/administration/…`, and the
      custom names listed in [Custom templates](../custom-templates.md)). But they were copied from the old pages, so
      they keep the old look, and their markup no longer matches the new stylesheets.
    - An override that extends `BASE_TEMPLATE` and fills `{% block body %}` keeps working as before. To get the new
      wrapper and styles, extend `appointment/layout.html` and fill `{% block djappt_content %}` instead, then copy
      the parts you changed onto the new default template.
    - Pages that relied on removed libraries now need to load them themselves: the staff pages no longer load Font
      Awesome, and the working hours, day off and unavailability forms no longer load Bootstrap 4, the tempusdominus
      picker, moment.js or jQuery UI (they use the browser's date and time pickers). They still send the same data
      to the same URLs.
    - The stylesheets the pages no longer use (`appointments.css`, `app_admin/btn.css`, `app_admin/user_profile.css`
      and the others listed under Deprecations in the [release notes](../release_notes/latest.md)) are still shipped
      for overrides that link them. They will be removed in a future major version, so plan to drop those links.

7. **Check anything that calls the delete and remove URLs**:
    - `delete_service`, `delete_appointment`, `delete_day_off`, `delete_unavailability`, `delete_working_hours`,
      `remove_staff_member`, and the "make me a staff member" / "remove me" actions now accept **POST** only and
      answer a GET with `405`.
    - The package's pages already send a POST. If a template or script of yours links to one of them, turn the link
      into a small form:
      ```html
      <form method="post" action="{% url 'appointment:delete_day_off' day_off_id=day_off.id %}">
          {% csrf_token %}
          <button type="submit">Delete</button>
      </form>
      ```
      or use `modal/confirm_modal.html` with `js/modal/show_modal.js`, which submits one for you.

8. **Check your emails**:
    - The four package emails (booking confirmation, new appointment request, reminder, reschedule) have a new
      design, extend `email_sender/base_email.html`, and come with a `.txt` version for the plain-text part. Your
      own email templates in `templates/emails/` are used as before; add a `.txt` next to one
      (`emails/thank_you.txt` for `emails/thank_you.html`) to control its plain-text part, otherwise it is derived
      from the HTML.
    - `ADMINS` may now be a list of email addresses, the form Django 6 recommends (`ADMINS = ['admin@example.com']`).
      With that form, 3.11 failed on every booking; 3.12 accepts both it and `('Name', 'email')` pairs.

9. **Review and Test**:
    - Book an appointment from start to finish, then open the staff calendar, an appointment, the service list, a
      staff profile and the working hours, day off and unavailability forms, and save one of each.
    - Check the pages at a phone width too: the layout now follows the width your base template gives it, not only
      the window.
    - If you link to the default thank-you page (`thank-you/<appointment_id>/`) from somewhere else, such as an
      email or a payment page opened in another browser, test it: visitors not logged in as the client now get a
      `404` there.

### Optional follow-ups

- **Your colours**: set `--djappt-accent` (and the other `--djappt-*` variables if you want) on `.djappt` in your
  own CSS to match your brand. See [Colours](../custom-templates.md#colours).
- **Translations**: French and Spanish are now complete. If you maintain your own translation, run `makemessages` in
  your project to pick up the new and reworded strings; the emails' sentences are now whole, with the names inside.

### Troubleshooting:

- **The pages look unstyled or half old, half new**:
    - Run `collectstatic` again and reload with the cache disabled. An override of the page itself keeps the old
      markup: compare it with the new default template.
- **The staff sidebar shows another user on a profile page**:
    - Your admin base uses `user`; use `request.user` (step 5).
- **A delete button answers `405 Method Not Allowed`**:
    - Something sends a GET to a delete URL; make it a POST (step 7).
- **Issues Post Upgrade**:
    - Consult the [release notes](../release_notes/latest.md) for the details of each change, and check the Django
      logs for error messages.

### Important Notes 📝:

- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
- Upgrading from the 3.10 series or older? Read the [3.11 migration guide](v3_11_0.md) first: that release added a
  model, so it needs a migration.
