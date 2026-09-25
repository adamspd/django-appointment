# Admin Views 👩‍💼

## Overview 🔍

The Django Appointment System's admin module comes packed with a set of views designed to manage appointments, staff
members, services, and more. Both superusers and staff members have unique access rights to ensure data integrity and
confidentiality.


---

## 🚨 Important Note 🚨

When extending the base template in your admin custom templates, ensure that you've included
the `{% block customMetaTag %}` inside the `<head>` section of your `BASE_TEMPLATE`. This block contains crucial meta
tags, such as the CSRF token, which is essential for the proper functioning of AJAX requests.

Example:

```html

<head>
    <title>My title</title>
    ...
    {% block customMetaTag %}
    {% endblock %}
    ...
</head>
```

Failure to include this block might result in errors during asynchronous operations due to a missing CSRF token.

---

## URL prefixes

Everything below is relative to wherever you mounted the package's URLconf, plus a prefix:

- administration pages live under **`app-admin/`**
- AJAX endpoints live under **`ajax/`**

So with `path('appointment/', include('appointment.urls'))`, the appointment calendar is at
`/appointment/app-admin/appointments/` and the slot lookup is at `/appointment/ajax/available_slots/`.

Two access levels are used throughout: **staff or superuser** and **superuser only**.

The first is Django's own `is_staff` flag, or `is_superuser`. Creating a [`StaffMember`](models.md#staffmember) sets
`is_staff` on that user, so every staff member qualifies — but so does any other Django staff user you have created
yourself, whether or not they have a `StaffMember` record. Views that act on a specific staff member's data narrow
this further with an ownership check: a staff member may only touch their own rows, while a superuser may touch
anyone's.

## __🛠 Detailed Functionality 🔧__

#### **Calendar & Appointments**:

- **View Appointments on Calendar**:
    - **Endpoint**: `app-admin/appointments/` and `app-admin/appointments/<str:response_type>/`
    - **Description**: Displays the calendar with all appointments. While superusers can see all appointments, staff
      members will only see their own. The response type can be either HTML (the default) or `json`.
    - **Methods**: GET · **Access**: staff or superuser

- **Display Specific Appointment Details**:
    - **Endpoint**: `app-admin/display-appointment/<int:appointment_id>/`
    - **Description**: Shows detailed information about a particular appointment. It fetches the appointment data based
      on the provided `appointment_id`.
    - **Methods**: GET · **Access**: staff or superuser

- **Delete Appointment**:
    - **Endpoint**: `app-admin/delete-appointment/<int:appointment_id>/`
    - **Description**: Deletes an appointment. Superusers can delete any appointment; staff members can only delete
      their own, and get a `403` page otherwise.
    - **Methods**: POST · **Access**: staff or superuser

#### **Staff Member Management**:

- **Add Staff Member Appointment Settings**:
    - **Endpoint**: `app-admin/add-staff-member-info/`
    - **Description**: Form for creating a `StaffMember` record — which services are offered, working times, weekend
      availability.
    - **Methods**: GET (display form), POST (submit form) · **Access**: superuser only

- **Create New Staff Member**:
    - **Endpoint**: `app-admin/create-new-staff-member/`
    - **Description**: Allows a superuser to create a new staff member account. The account details are captured through
      a form.
    - **Methods**: GET (display form), POST (submit form) · **Access**: superuser only

- **Add or Update Staff Member Appointment Information**:
    - **Endpoint**: `app-admin/add-staff-member/` and `app-admin/update-staff-member/<int:user_id>/`
    - **Description**: Adds, or updates for an existing staff member, the appointment-related settings (services
      offered, slot duration, lead and finish times, days worked).
    - **Methods**: GET (display form), POST (submit form) · **Access**: staff or superuser

- **Make Superuser a Staff Member**:
    - **Endpoint**: `app-admin/make-superuser-staff-member/`
    - **Description**: Converts a superuser account to have staff member privileges.
    - **Methods**: POST · **Access**: superuser only

- **Remove Staff Member Role from Superuser**:
    - **Endpoint**: `app-admin/remove-superuser-staff-member/`
    - **Description**: Removes the staff member privileges from a superuser account.
    - **Methods**: POST · **Access**: superuser only

- **Remove Staff Member**:
    - **Endpoint**: `app-admin/remove-staff-member/<int:staff_user_id>/`
    - **Description**: Allows a superuser to remove a staff member account. The account to be removed is identified
      by `staff_user_id`.
    - **Methods**: POST · **Access**: superuser only

#### **Service Management**:

- **Add New Service**:
    - **Endpoint**: `app-admin/add-service/`
    - **Description**: Allows a superuser to add a new service. The service details are captured through a form.
    - **Methods**: GET (display form), POST (submit form) · **Access**: superuser only

- **Update Existing Service**:
    - **Endpoint**: `app-admin/update-service/<int:service_id>/`
    - **Description**: Superusers can edit the details of an existing service. The service to be edited is identified
      by `service_id`.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data) · **Access**: superuser only

- **Delete Service**:
    - **Endpoint**: `app-admin/delete-service/<int:service_id>/`
    - **Description**: Allows a superuser to remove a service from the system. The service is identified
      by `service_id`.
    - **Methods**: POST · **Access**: superuser only

- **View All Services**:
    - **Endpoint**: `app-admin/service-list/` and `app-admin/service-list/<str:response_type>/`
    - **Description**: Displays a list of all services in the system. The response type can be HTML (the default) or
      `json`.
    - **Methods**: GET · **Access**: staff or superuser

- **View One Service**:
    - **Endpoint**: `app-admin/view-service/<int:service_id>/<int:view>/`
    - **Description**: Displays detailed information about a particular service. The service is identified
      by `service_id`. The `view` parameter is mandatory and should be `1` to render the form read-only; any other
      value renders it as an editable update form.
    - **Methods**: GET · **Access**: superuser only

#### **Profile & Personal Information**:

- **View User Profile**:
    - **Endpoint**: `app-admin/user-profile/` and `app-admin/user-profile/<int:staff_user_id>/`
    - **Description**: Users can view their profile information. While superusers can view any user's profile, staff
      members can only view their own. A superuser hitting the bare URL gets the list of all staff members instead.
    - **Methods**: GET · **Access**: staff or superuser

- **Update Personal Information**:
    - **Endpoint**: `app-admin/update-user-info/` and `app-admin/update-user-info/<int:staff_user_id>/`
    - **Description**: Allows a user to update their personal details, such as name and email. If the email is changed,
      it goes through a verification process.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data) · **Access**: staff or superuser

- **Email Change Verification**:
    - **Endpoint**: `verification-code/` — note this one sits at the root of the URLconf, not under `app-admin/`
    - **Description**: When a user changes their email, they need to verify the new email through a code. This endpoint
      handles the verification process.
    - **Methods**: GET (it displays a verification code form), POST (submit verification code) · **Access**: staff or
      superuser

#### **Days Off Management**:

- **Add a Day Off**:
    - **Endpoint**: `app-admin/add-day-off/<int:staff_user_id>/`
    - **Description**: Allows users to add a new day off. Staff members can only add for themselves, while superusers
      can add for any user.
    - **Methods**: GET (display form), POST (submit form) · **Access**: staff or superuser

- **Update a Day Off**:
    - **Endpoint**: `app-admin/update-day-off/<int:day_off_id>/` and
      `app-admin/update-day-off/<int:day_off_id>/<int:staff_user_id>/`
    - **Description**: Allows users to modify an existing day off. Staff members can only update their own days off,
      while superusers can update for any user.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data) · **Access**: staff or superuser

- **Delete a Day Off**:
    - **Endpoint**: `app-admin/delete-day-off/<int:day_off_id>/` and
      `app-admin/delete-day-off/<int:day_off_id>/<int:staff_user_id>/`
    - **Description**: Enables users to remove a day off. Staff members can only delete their own days off, while
      superusers can delete any day off.
    - **Methods**: POST · **Access**: staff or superuser

#### **Unavailability Management**:

An [`Unavailability`](models.md#unavailability) blocks a time range on a single day, leaving the rest of that day
bookable — use a day off to remove whole days instead. Slots overlapping one are dropped from the booking page.

- **Add an Unavailability**:
    - **Endpoint**: `app-admin/add-unavailability/<int:staff_user_id>/`
    - **Description**: Adds an unavailability for the given staff member. Staff members can only add their own, while
      superusers can add for any user. There is no variant of this URL without `staff_user_id`.
    - **Methods**: GET (display form), POST (submit form) · **Access**: staff or superuser

- **Update an Unavailability**:
    - **Endpoint**: `app-admin/update-unavailability/<int:unavailability_id>/` and
      `app-admin/update-unavailability/<int:unavailability_id>/<int:staff_user_id>/`
    - **Description**: Modifies an existing unavailability. Staff members can only update their own, while superusers
      can update anyone's. An unknown `unavailability_id` renders the `404` page.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data) · **Access**: staff or superuser

- **Delete an Unavailability**:
    - **Endpoint**: `app-admin/delete-unavailability/<int:unavailability_id>/` and
      `app-admin/delete-unavailability/<int:unavailability_id>/<int:staff_user_id>/`
    - **Description**: Removes an unavailability. Staff members can only delete their own, while superusers can delete
      any.
    - **Methods**: POST · **Access**: staff or superuser

!!! note "What the add and update forms post"
    Both submit the date and times as pre-formatted hidden fields alongside the localized ones the user sees:
    `date_raw` (`YYYY-MM-DD`), `start_time_raw` and `end_time_raw` (`HH:MM:SS`), plus `description`. The view parses
    those raw values, so a replacement form must keep them. The start-before-end check is done by the view, which
    answers a rejected submission with a `400` JSON response carrying the `INVALID_DATA`
    [error code](utils/error_codes.md).

#### **Working Hours Management**:

- **Add New Working Hours**:
    - **Endpoint**: `app-admin/add-working-hours/` and `app-admin/add-working-hours/<int:staff_user_id>/`
    - **Description**: Users can set new working hours. Superusers can set for any user, while staff members can only
      set their own.
    - **Methods**: GET (display form), POST (submit form) · **Access**: staff or superuser

- **Update Working Hours**:
    - **Endpoint**: `app-admin/update-working-hours/<int:working_hours_id>/` and
      `app-admin/update-working-hours/<int:working_hours_id>/<int:staff_user_id>/`
    - **Description**: Allows users to modify their working hours. If the working hours record doesn't exist, an error
      page is displayed.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data) · **Access**: staff or superuser

- **Delete Working Hours**:
    - **Endpoint**: `app-admin/delete-working-hours/<int:working_hours_id>/` and
      `app-admin/delete-working-hours/<int:working_hours_id>/<int:staff_user_id>/`
    - **Description**: Users can remove a working hours' entry.
      Superusers can delete any entry, while staff members can only delete their own.
    - **Methods**: POST · **Access**: staff or superuser

#### **Ajax Endpoints**:

All of these live under the `ajax/` prefix.

- **Get Available Slots**:
    - **Endpoint**: `ajax/available_slots/`
    - **Description**: Provides AJAX functionality to get available slots for appointments. Reads `selected_date`,
      `staff_member` and the optional `service_id` from the query string; passing `service_id` checks availability
      against the service's real duration rather than the slot step.
    - **Methods**: GET · **Access**: public

- **Request Next Available Slot**:
    - **Endpoint**: `ajax/request_next_available_slot/<int:service_id>/`
    - **Description**: Fetches the next available slot for a given service via AJAX. The service is identified
      by `service_id`, and the staff member by the `staff_member` query parameter. The search gives up after 90
      days and answers with the `NEXT_AVAILABILITY_NOT_FOUND` [error code](utils/error_codes.md).
    - **Methods**: GET · **Access**: public

- **Get Staff Member Non-working Days**:
    - **Endpoint**: `ajax/request_staff_info/`
    - **Description**: Returns the days a staff member does not work, so the calendar can grey them out. Reads
      `staff_member` from the query string.
    - **Methods**: GET · **Access**: public

- **Fetch Services for a Staff Member**:
    - **Endpoint**: `ajax/fetch_service_list_for_staff/`
    - **Description**: Returns the services a staff member offers, used when creating or editing an appointment from
      the admin calendar. Reads `staff_member` and optionally `appointmentId` from the query string.
    - **Methods**: GET · **Access**: staff or superuser

- **Fetch Staff List**:
    - **Endpoint**: `ajax/fetch_staff_list/`
    - **Description**: Returns every staff member as `{id, name}`, used to populate the staff picker.
    - **Methods**: GET · **Access**: superuser only

- **Is User Staff Admin**:
    - **Endpoint**: `ajax/is_user_staff_admin/`
    - **Description**: Reports whether the logged-in user has a `StaffMember` record (superusers always count), so the
      calendar UI can hide actions the user cannot perform.
    - **Methods**: GET · **Access**: staff or superuser

- **Update Appointment Minimal Information**:
    - **Endpoint**: `ajax/update_appt_min_info/`
    - **Description**: This AJAX endpoint allows updating minimal information of an appointment, such as time or status.
    - **Methods**: POST · **Access**: staff or superuser

- **Update Appointment Date and Time**:
    - **Endpoint**: `ajax/update_appt_date_time/`
    - **Description**: An AJAX endpoint for updating the date and time of an existing appointment.
    - **Methods**: POST · **Access**: staff or superuser

- **Validate Appointment Date**:
    - **Endpoint**: `ajax/validate_appointment_date/`
    - **Description**: Provides AJAX functionality to validate the selected date for an appointment.
    - **Methods**: POST · **Access**: staff or superuser

- **Delete Appointment (Ajax)**:
    - **Endpoint**: `ajax/delete_appointment/`
    - **Description**: Deletes an appointment from a JSON body containing `appointment_id`. Superusers can delete any
      appointment; staff members only their own, and get a `403` JSON response otherwise.
    - **Methods**: POST · **Access**: staff or superuser

## Note on updating personal info

When a staff member or superuser updates their personal information, and the email of the staff member changes, the
email will be verified again. This is to ensure that a user cannot change another staff member's email without
verification.
