# Django Appointment 📦

## Admin Views 👩‍💼

### Overview 🔍

The Django Appointment System's admin module comes packed with a set of views designed to manage appointments, staff
members, services, and more. Both superusers and staff members have unique access rights to ensure data integrity and
confidentiality.


---

### 🚨 Important Note 🚨

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

### __🛠 Detailed Functionality 🔧__

#### **Calendar & Appointments**:

- **View Appointments on Calendar**:
    - **Endpoint**: `appointments/` and `appointments/<str:response_type>/`
    - **Description**: Displays the calendar with all appointments. While superusers can see all appointments, staff
      members will only see their own. The response type can be either HTML or JSON.
    - **Methods**: GET

- **Display Specific Appointment Details**:
    - **Endpoint**: `display-appointment/<int:appointment_id>/`
    - **Description**: Shows detailed information about a particular appointment. It fetches the appointment data based
      on the provided `appointment_id`.
    - **Methods**: GET

- **Delete Appointment**:
    - **Endpoint**: `delete-appointment/<int:appointment_id>/`
    - **Description**: Allows superusers to delete an appointment. The appointment to be deleted is identified
      by `appointment_id`.
    - **Methods**: GET

#### **Staff Member Management**:

- **Create New Staff Member**:
    - **Endpoint**: `create-staff-member/`
    - **Description**: Allows a superuser to create a new staff member account. The account details are captured through
      a form.
    - **Methods**: GET (display form), POST (submit form)

- **Update Staff Member Information**:
    - **Endpoint**: `update-staff-member/<int:user_id>/`
    - **Description**: Allows updating the personal information of an existing staff member. Accessible to superusers.
    - **Methods**: GET (display form), POST (submit form)

- **Make Superuser a Staff Member**:
    - **Endpoint**: `make-superuser-staff-member/`
    - **Description**: Converts a superuser account to have staff member privileges.
    - **Methods**: GET

- **Remove Staff Member Role from Superuser**:
    - **Endpoint**: `remove-superuser-staff-member/`
    - **Description**: Removes the staff member privileges from a superuser account.
    - **Methods**: GET

- **Remove Staff Member**:
    - **Endpoint**: `remove-staff-member/<int:staff_user_id>/`
    - **Description**: Allows a superuser to remove a staff member account. The account to be removed is identified
      by `staff_user_id`.
    - **Methods**: GET

#### **Service Management**:

- **Add New Service**:
    - **Endpoint**: `add-service/`
    - **Description**: Allows a superuser to add a new service. The service details are captured through a form.
    - **Methods**: GET (display form), POST (submit form)

- **Update Existing Service**:
    - **Endpoint**: `update-service/<int:service_id>/`
    - **Description**: Superusers can edit the details of an existing service. The service to be edited is identified
      by `service_id`.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data)

- **Delete Service**:
    - **Endpoint**: `delete-service/<int:service_id>/`
    - **Description**: Allows a superuser to remove a service from the system. The service is identified
      by `service_id`.
    - **Methods**: GET

- **View All Services**:
    - **Endpoint**: `service-list/` and `service-list/<str:response_type>/`
    - **Description**: Displays a list of all services in the system.
        - **Methods**: GET

- **View One Service**:
  **Endpoint**: `view-service/<int:service_id>/<int:view>/`
    - **Description**: Displays detailed information about a particular service. The service is identified
      by `service_id`. The `view` parameter is mandatory and should be `1`. If `0`, the view is not displayed.
    - **Methods**: GET

#### **Profile & Personal Information**:

- **View User Profile**:
    - **Endpoint**: `user-profile/` and `user-profile/<int:staff_user_id>/`
    - **Description**: Users can view their profile information. While superusers can view any user's profile, staff
      members can only view their own.
    - **Methods**: GET

- **Update Personal Information**:
    - **Endpoint**: `update-user-info/` and `update-user-info/<int:staff_user_id>/`
    - **Description**: Allows a user to update their personal details, such as name and email. If the email is changed,
      it goes through a verification process.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data)

- **Email Change Verification**:
    - **Endpoint**: `email_change_verification_code/`
    - **Description**: When a user changes their email, they need to verify the new email through a code. This endpoint
      handles the verification process.
    - **Methods**: GET (it displays a verification code form), POST (submit verification code)

#### **Days Off Management**:

- **Add a Day Off**:
    - **Endpoint**: `add-day-off/` and `add-day-off/<int:staff_user_id>/`
    - **Description**: Allows users to add a new day off. Staff members can only add for themselves, while superusers
      can add for any user.
    - **Methods**: GET (display form), POST (submit form)

- **Update a Day Off**:
    - **Endpoint**: `update-day-off/<int:day_off_id>/`, `update-day-off/<int:day_off_id>/<int:staff_user_id>/`
    - **Description**: Allows users to modify an existing day off. Staff members can only update their own days off,
      while superusers can update for any user.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data)

- **Delete a Day Off**:
    - **Endpoint**: `delete-day-off/<int:day_off_id>/`, `delete-day-off/<int:day_off_id>/<int:staff_user_id>/`
    - **Description**: Enables users to remove a day off. Staff members can only delete their own days off, while
      superusers can delete any day off.
    - **Methods**: GET

- **Description**: Enables users to remove a day off. Staff members can only delete their own days off, while superusers
  can delete any day off.
- **Methods**: GET

#### **Working Hours Management**:

- **Add New Working Hours**:
    - **Endpoint**: `add-working-hours/` and `add-working-hours/<int:staff_user_id>/`
    - **Description**: Users can set new working hours. Superusers can set for any user, while staff members can only
      set their own.
    - **Methods**: GET (display form), POST (submit form)

- **Update Working Hours**:
    - **Endpoint**: `update-working-hours/`, `update-working-hours/<int:working_hours_id>/`,
      and `update-working-hours/<int:working_hours_id>/<int:staff_user_id>/`
    - **Description**: Allows users to modify their working hours. If the working hours record doesn't exist, an error
      page is displayed.
    - **Methods**: GET (display form with pre-filled data), POST (submit updated data)

- **Delete Working Hours**:
    - **Endpoint**: `delete-working-hours/`, `delete-working-hours/<int:working_hours_id>/`,
      and `delete-working-hours/<int:working_hours_id>/<int:staff_user_id>/`
    - **Description**: Users can remove a working hours' entry.
      Superusers can delete any entry, while staff members can only delete their own.
    - **Methods**: GET

#### **Ajax Endpoints**:

- **Get Available Slots**:
    - **Endpoint**: `available_slots/`
    - **Description**: Provides AJAX functionality to get available slots for appointments.
    - **Methods**: POST

- **Request Next Available Slot**:
    - **Endpoint**: `request_next_available_slot/<int:service_id>/`
    - **Description**: Fetches the next available slot for a given service via AJAX. The service is identified
      by `service_id`.
    - **Methods**: GET

- **Update Appointment Minimal Information**:
    - **Endpoint**: `update_appt_min_info/`
    - **Description**: This AJAX endpoint allows updating minimal information of an appointment, such as time or status.
    - **Methods**: POST

- **Update Appointment Date and Time**:
    - **Endpoint**: `update_appt_date_time/`
    - **Description**: An AJAX endpoint for updating the date and time of an existing appointment.
    - **Methods**: POST

- **Validate Appointment Date**:
    - **Endpoint**: `validate_appointment_date/`
    - **Description**: Provides AJAX functionality to validate the selected date for an appointment.
    - **Methods**: POST

- **Delete Appointment (Ajax)**:
    - **Endpoint**: `delete_appointment/`
    - **Description**: This endpoint provides an AJAX way to delete appointments.
    - **Methods**: POST

### Note on updating personal info

When a staff member or superuser updates their personal information, and the email of the staff member changes, the
email will be verified again. This is to ensure that a user cannot change another staff member's email without
verification.
