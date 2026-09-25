# Custom Email and Page Templates

This system allows you to override default email templates and page templates with your own custom designs while
maintaining backward compatibility.

## How It Works

The system checks for your custom templates first, then falls back to the default templates if yours don't exist. This
means:

- **No custom templates?** Everything works exactly as before
- **Custom templates?** Your designs are used instead of the defaults
- **Missing some custom templates?** Only the ones you created are used, others fall back to defaults

## Setup

### 1. Configure Your Settings

Add these optional settings to your `settings.py`:

```python
# Custom template directories (optional - these are the defaults)
APPOINTMENT_CUSTOM_TEMPLATES_DIR = 'custom'  # Directory for page templates
APPOINTMENT_CUSTOM_EMAILS_DIR = 'emails'  # Directory for email templates

# Make sure your templates directory is configured
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # Your templates directory
        ],
        'APP_DIRS': True,
        # ... rest of your template config
    },
]
```

### 2. Create Your Directory Structure

```
your_project/
├── templates/
│   ├── custom/          # HTML Page templates (configurable via APPOINTMENT_CUSTOM_TEMPLATES_DIR)
│   │   ├── appointments.html
│   │   ├── appointment_client_information.html
│   │   ├── verification_code.html
│   │   ├── thank_you_page.html
│   │   ├── rescheduling_thank_you.html
│   │   ├── password_form.html
│   │   ├── password_success.html
│   │   ├── password_error.html
│   │   ├── 304_already_submitted.html
│   │   ├── 403_forbidden.html
│   │   ├── 403_forbidden_rescheduling.html
│   │   ├── 404_not_found.html
│   │   ├── staff_index.html
│   │   ├── display_appointment.html
│   │   ├── manage_staff_member.html
│   │   ├── manage_staff_personal_info.html
│   │   ├── email_change_verification_code.html
│   │   ├── manage_service.html
│   │   ├── service_list.html
│   │   ├── staff_list.html
│   │   ├── user_profile.html
│   │   ├── manage_day_off.html
│   │   ├── manage_unavailability.html
│   │   └── manage_working_hours.html
│   └── emails/          # Email templates (configurable via APPOINTMENT_CUSTOM_EMAILS_DIR)
│       ├── thank_you.html
│       ├── password_reset.html
│       ├── verification.html
│       ├── reminder_email.html
│       ├── new_appointment_admin_notification.html
│       ├── reschedule.html
│       └── reschedule_admin.html
└── settings.py
```

You only create the files you actually want to override — everything else keeps using the defaults.

## Your Base Template

The package pages don't draw your site's navbar or footer. They render inside your own base template, through a small
package layout:

```
your page override or package page
  └── extends appointment/layout.html   (package, shared by every page, no site chrome)
        └── extends APPOINTMENT_BASE_TEMPLATE / APPOINTMENT_ADMIN_BASE_TEMPLATE   (your base)
```

```python
APPOINTMENT_BASE_TEMPLATE = 'base.html'  # booking, thank-you and error pages
APPOINTMENT_ADMIN_BASE_TEMPLATE = 'staff_base.html'  # staff pages (optional, defaults to the same file)
```

Your base must define the `customMetaTag` (inside `<head>`), `customCSS`, `title`, `description`, `body` and
`customJS` blocks, and load jQuery and Bootstrap 5 (CSS and JS) before `customJS`. Put your navbar and footer around
`{% block body %}`. Without these settings, the package falls back to `base_templates/base.html`, a bare page with no
navbar.

The layout fills your `body` block with a `<div class="djappt">` wrapper, and the pages put their content in its
`djappt_content` block. The package CSS only styles what's inside that wrapper: it never changes your navbar, footer or
other pages, and your own CSS keeps working around it.

Don't override `appointment/layout.html`: it holds what every package page needs. To change a page, override it as
shown below; to change the page shell, change your base. Your page overrides can extend `appointment/layout.html` too
(put the content in `{% block djappt_content %}` so it gets the wrapper), or extend `BASE_TEMPLATE` directly as before.

## Available Templates

### Page Templates (Custom Directory)

These are the HTML pages users see in their browser.

Every page below also receives the generic context: `BASE_TEMPLATE`, `user`, `is_superuser`, `locale` and
`localized_formats`. Only the page-specific variables are listed.

`localized_formats` is what the date and time pickers are configured from — it holds Django's `TIME_INPUT_FORMATS`,
`DATE_INPUT_FORMATS` and `DATETIME_INPUT_FORMATS` for the active locale, plus `js_timepicker_display_format` and
`js_datepicker_display_format`, the Moment.js equivalents. Keep using it in any template of yours that renders a
picker, or the widget will fall back to a format the server may not parse back.

#### Booking flow

| Template Name                         | When Used                                      | Page-specific Context Variables                                                                                                                                                                                                  | Original Template                                 |
|---------------------------------------|------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `appointments.html`                   | Slot picker, for both booking and rescheduling | `service`, `staff_member`, `all_staff_members`, `page_title`, `page_description`, `available_slots`, `date_chosen`, `locale`, `timezoneTxt`, `label` — plus `rescheduled_date`, `page_header`, `ar_id_request` when rescheduling | `appointment/appointments.html`                   |
| `appointment_client_information.html` | Client information form page                   | `ar`, `APPOINTMENT_PAYMENT_URL`, `form`, `client_data_form`, `service_name`, `has_required_email_reminder_config`                                                                                                                | `appointment/appointment_client_information.html` |
| `verification_code.html`              | Email verification code entry page             | `appointment_request_id`, `id_request`                                                                                                                                                                                           | `appointment/enter_verification_code.html`        |
| `thank_you_page.html`                 | Thank you page after appointment booking       | `appointment`                                                                                                                                                                                                                    | `appointment/default_thank_you.html`              |
| `rescheduling_thank_you.html`         | Thank you page after rescheduling              | (generic context only)                                                                                                                                                                                                           | `appointment/rescheduling_thank_you.html`         |

#### Password reset

| Template Name           | When Used                        | Page-specific Context Variables                            | Original Template               |
|-------------------------|----------------------------------|------------------------------------------------------------|---------------------------------|
| `password_form.html`    | Password reset form page         | `form`, `page_title`, `page_message`, `page_description`   | `appointment/set_password.html` |
| `password_success.html` | After successful password reset  | `page_title`, `page_message`, `page_description`           | `appointment/thank_you.html`    |
| `password_error.html`   | When password reset fails        | `page_title`, `page_message`, `page_description`           | `appointment/thank_you.html`    |

#### Error pages

| Template Name                     | When Used                                                        | Page-specific Context Variables         | Original Template                             |
|-----------------------------------|------------------------------------------------------------------|-----------------------------------------|-----------------------------------------------|
| `304_already_submitted.html`      | Client re-submits an appointment request that was already sent   | `service_id`                            | `error_pages/304_already_submitted.html`      |
| `403_forbidden.html`              | User tries to act on something they don't own                    | `message`, `back_url`, `BASE_TEMPLATE`  | `error_pages/403_forbidden.html`              |
| `403_forbidden_rescheduling.html` | Appointment can't be rescheduled (not allowed, or limit reached) | `url`                                   | `error_pages/403_forbidden_rescheduling.html` |
| `404_not_found.html`              | Appointment, service, or reschedule link not found               | `error_message` (reschedule links only) | `error_pages/404_not_found.html`              |

#### Administration

| Template Name                         | When Used                                         | Page-specific Context Variables                                                                                                                                                                       | Original Template                                    |
|---------------------------------------|---------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| `staff_index.html`                    | Staff/admin calendar dashboard                    | `appointments` (JSON string)                                                                                                                                                                          | `administration/staff_index.html`                    |
| `display_appointment.html`            | Detail page for a single appointment              | `appointment`, `page_title`, `page_description`                                                                                                                                                       | `administration/display_appointment.html`            |
| `manage_staff_member.html`            | Add or edit a staff member's appointment settings | `form`                                                                                                                                                                                                | `administration/manage_staff_member.html`            |
| `manage_staff_personal_info.html`     | Add or edit a staff member's personal information | `form`, `btn_text`                                                                                                                                                                                    | `administration/manage_staff_personal_info.html`     |
| `email_change_verification_code.html` | Verification code entry after an email change     | (generic context only)                                                                                                                                                                                | `administration/email_change_verification_code.html` |
| `manage_service.html`                 | Add, edit, or view a service                      | `form`, `btn_text`, `page_title`, `service` (not when adding), `offered_by_me` (view mode only)                                                                                                       | `administration/manage_service.html`                 |
| `service_list.html`                   | List of all services                              | `services`                                                                                                                                                                                            | `administration/service_list.html`                   |
| `staff_list.html`                     | List of all staff members, shown to a superuser   | `staff_members`, `btn_staff_me`, `btn_staff_me_link`                                                                                                                                                  | `administration/staff_list.html`                     |
| `user_profile.html`                   | A staff member's profile page                     | `superuser`, `user`, `staff_member`, `days_off`, `unavailabilities`, `working_hours`, `services_offered`, `staff_member_not_found`, `buffer_time_help_text`, `slot_duration_help_text`, `service_msg` | `administration/user_profile.html`                   |
| `manage_day_off.html`                 | Add or edit a day off                             | `button_text`, `day_off_form`                                                                                                                                                                         | `administration/manage_day_off.html`                 |
| `manage_unavailability.html`          | Add or edit an unavailability                     | `button_text`, `unavailability_form`, `staff_user_id`, `entity_instance` and `entity_id` (edit only)                                                                                                  | `administration/manage_unavailability.html`          |
| `manage_working_hours.html`           | Add or edit working hours                         | `button_text`, `working_hours_form`, `staff_user_id`, `entity_instance` and `entity_id` (edit only)                                                                                                   | `administration/manage_working_hours.html`           |

> **Note:** `user-profile/` serves two different templates. A superuser visiting it without a `staff_user_id` gets
> `staff_list.html`; everyone else, and a superuser visiting a specific member, gets `user_profile.html`. Override
> whichever you need — they are independent.
>
> The three `manage_*` forms post their values back as pre-formatted hidden fields (`date_raw`, `start_time_raw`,
> `end_time_raw`, and `day_of_week` for working hours) alongside the localized ones the user sees. A replacement
> template must keep those, or the view will not be able to parse the submission.
>
> Every delete and remove action (`delete_service`, `delete_appointment`, `delete_day_off`, `delete_unavailability`,
> `delete_working_hours`, `remove_staff_member`) and the staff-me toggle (`btn_staff_me_link`) only accept **POST**;
> a GET returns `405`. Use a small `<form method="post">` with `{% csrf_token %}`, or the default
> `modal/confirm_modal.html` with `js/modal/show_modal.js`, which submits one for you.

### Email Templates (Emails Directory)

These are HTML emails sent to users:

| Template Name                             | When Sent                             | Fallback Behavior          | Context Variables                                                                                                                                                                 |
|-------------------------------------------|---------------------------------------|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `thank_you.html`                          | Appointment confirmation              | Uses default HTML template | `first_name`, `message_1`, `current_year`, `company`, `more_details`, `account_details`, `message_2`, `month_year`, `day`, `activation_link`, `main_title`, `reschedule_link`     |
| `password_reset.html`                     | Staff member password setup           | Plain text email           | `first_name`, `current_year`, `company`, `activation_link`, `account_details`, `username`, `login_instruction`, `user`, `website_name`                                            |
| `verification.html`                       | Email address verification            | Plain text email           | `user`, `first_name`, `verification_code`, `company`                                                                                                                              |
| `reminder_email.html`                     | 24h appointment reminder (Django Q)   | Uses default HTML template | `first_name`, `appointment`, `reschedule_link`, `recipient_type` (`'client'` or `'admin'`)                                                                                        |
| `new_appointment_admin_notification.html` | Admin/staff notified of a new booking | Uses default HTML template | `recipient_name`, `client_name`, `appointment`, `is_staff_member`, `staff_member_name`                                                                                            |
| `reschedule.html`                         | Reschedule confirmation request       | Uses default HTML template | `is_confirmation`, `first_name`, `old_date`, `reschedule_date`, `old_start_time`, `start_time`, `old_end_time`, `end_time`, `confirmation_link`, `company`                        |
| `reschedule_admin.html`                   | Admin notification of reschedule      | Uses default HTML template | `is_confirmation`, `client_name`, `service_name`, `reason_for_rescheduling`, `old_date`, `reschedule_date`, `old_start_time`, `start_time`, `old_end_time`, `end_time`, `company` |

> **Accepted aliases:** for historical reasons the two reschedule emails are also looked up under their internal
> names, which take precedence if both files exist:
>
> - `reschedule.html` — also accepted as `reschedule_confirmation_email.html`
> - `reschedule_admin.html` — also accepted as `notify_admin_about_reschedule_email.html`
>
> Use the short names for new projects.

> **Plain-text part:** every HTML email is also sent with a plain-text version. It is rendered from a `.txt` template
> with the same name next to the HTML one when there is one (`emails/thank_you.txt` for `emails/thank_you.html`, with
> the same context), and derived from the HTML otherwise.

## Template Examples

The following are just examples. You can customize them as you see fit. Or you can create your own designs from scratch.

### Client Information Form (`templates/custom/appointment_client_information.html`)

```html
{% extends "your_base_template.html" %}
{% load i18n %}

{% block title %}Client Information{% endblock %}

{% block content %}
<div class="client-info-container">
    <h1>Your Information</h1>

    <div class="appointment-summary">
        <h3>Appointment Summary</h3>
        <p><strong>Service:</strong> {{ service_name }}</p>
        <p><strong>Date:</strong> {{ ar.date }}</p>
        <p><strong>Time:</strong> {{ ar.start_time }} - {{ ar.end_time }}</p>
    </div>

    <form method="post" class="client-form">
        {% csrf_token %}

        <div class="form-section">
            <h3>Personal Information</h3>
            {{ client_data_form.as_p }}
        </div>

        <div class="form-section">
            <h3>Appointment Details</h3>
            {{ form.as_p }}
        </div>

        {% if ar.service.is_a_paid_service %}
        <div class="payment-section">
            <h3>Payment Option</h3>
            <input type="radio" name="payment_type" value="full" id="full_payment" checked>
            <label for="full_payment">Full Payment ({{ ar.service.get_price_text }})</label>

            {% if ar.service.accepts_down_payment %}
            <input type="radio" name="payment_type" value="down" id="down_payment">
            <label for="down_payment">Down Payment ({{ ar.service.get_down_payment_text }})</label>
            {% endif %}
        </div>
        {% endif %}

        <button type="submit" class="submit-btn">Continue</button>
    </form>
</div>
{% endblock %}
```

### Password Reset Form (`templates/custom/password_form.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ page_title }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 500px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }

        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .form-group {
            margin: 20px 0;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }

        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }

        button {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
        }

        button:hover {
            background: #0056b3;
        }

        .alert {
            padding: 12px;
            margin: 15px 0;
            border-radius: 4px;
            border: 1px solid;
        }

        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border-color: #f5c6cb;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
            border-color: #c3e6cb;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>{{ page_title }}</h1>
    <p>{{ page_description }}</p>

    {% if messages %}
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }}">{{ message }}</div>
    {% endfor %}
    {% endif %}

    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Set Password</button>
    </form>
</div>
</body>
</html>
```

### Password Reset Email (`templates/emails/password_reset.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Password Setup - {{ company }}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to {{ company }}</h1>
    </div>

    <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <p style="font-size: 18px; margin-bottom: 20px;">Hello {{ first_name }},</p>

        <p>You've been added as a staff member to {{ company }}. To get started, you'll need to set up your
            password.</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ activation_link }}"
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 15px 30px; text-decoration: none; 
                          border-radius: 25px; display: inline-block; font-weight: bold;
                          font-size: 16px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                Set My Password
            </a>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #667eea;">
            <h4 style="margin-top: 0; color: #667eea;">Your Login Details</h4>
            <p style="margin: 5px 0;"><strong>Username:</strong> <code
                    style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">{{ username }}</code></p>
            <p style="margin: 5px 0;"><strong>Email:</strong> {{ user.email }}</p>
            <p style="margin-bottom: 0; font-size: 14px; color: #666;">You can use either your username or email to log
                in</p>
        </div>

        <div style="border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px;">
            <p style="font-size: 14px; color: #666;">If the button doesn't work, copy and paste this link:</p>
            <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                {{ activation_link }}
            </p>
        </div>
    </div>

    <div style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
        {{ company }} &copy; {{ current_year }}
    </div>
</div>
</body>
</html>
```

### Email Verification (`templates/emails/verification.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Email Verification - {{ company }}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Email Verification</h1>
    </div>

    <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <p style="font-size: 18px; margin-bottom: 20px;">Hello {{ first_name }},</p>

        <p>Please use this verification code to confirm your email address:</p>

        <div style="text-align: center; margin: 30px 0;">
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                           border: 3px solid #28a745; padding: 25px; border-radius: 15px; 
                           display: inline-block; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);">
                    <span style="font-size: 36px; font-weight: bold; color: #28a745; 
                               letter-spacing: 8px; font-family: monospace;">{{ verification_code }}</span>
            </div>
        </div>

        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; color: #856404; font-size: 14px;">
                <strong>⏰ This code will expire soon</strong> - please use it right away to verify your email address.
            </p>
        </div>

        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            If you didn't request this verification, you can safely ignore this email.
        </p>
    </div>

    <div style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
        {{ company }} &copy; {{ current_year }}
    </div>
</div>
</body>
</html>
```

## Important Notes

1. **Template names are fixed** - You must use the exact names listed above
2. **Directory names are configurable** - Change `APPOINTMENT_CUSTOM_TEMPLATES_DIR` and `APPOINTMENT_CUSTOM_EMAILS_DIR` in your `settings.py` if you prefer different folder names.
3. **Partial implementation is fine** - You can create only some templates; others will use defaults
4. **Context variables** - Use the provided context variables in your templates
5. **Form requirements** - Keep form field names and IDs intact for proper functionality
6. **Fallback behavior** - A template that is missing, or that fails to compile (an unclosed `{% if %}`, an unknown
   tag, a bad `{% load %}`), is skipped and the default is used instead. Compile failures are logged as a warning
   naming the template, so check your logs if an override seems to be ignored. Errors that only surface while the
   page is being rendered — a template filter raising on the data it is given, for example — cannot be caught this
   way and will still propagate.

## Testing Your Templates

1. Create your custom templates
2. Trigger the relevant actions (booking, password reset, etc.)
3. Check that your templates are being used
4. Verify fallback works by temporarily renaming your template files

Your custom templates give you complete control over the look and feel while maintaining the system's functionality.
