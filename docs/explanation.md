# Django Appointment System: Screenshots and Tutorial

Welcome to the Django Appointment System! This guide will walk you through setting up and using the system, complete with screenshots and a video tutorial.

## Getting Started

After completing the initial setup steps - making migrations, migrating, running the server, and creating a superuser - you might want to create an appointment as a client. However, this is not possible initially as no services or staff members are yet configured.

### Adding a Service

Your first step is to add a service. Navigate to the admin page and add a service at:
https://mysuperwebsite.com/app-admin/add-service/

![Creating Service](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/creating_service.png?raw=true)

### Attempting to Create an Appointment

If you attempt to create an appointment request now, it's still not possible as there are no staff members yet:

![Appointment Request without Staff Member](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/appointment_request_w_sm.png?raw=true)

Similarly, if you check the list of appointments, it will be empty and you'll get a warning:

![Appointment List without Staff Member](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/appointment_list_admin.png?raw=true)

### Adding a Staff Member

To add a staff member, visit:

![Staff Member List](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/staff_member_list.png?raw=true)

You can either add a new staff member or assign yourself as a staff member, especially if you are a superuser. In this example, I will demonstrate using the `Staff me` button.

### Updating Your Profile

Once you have created a staff member profile, you need to specify the services you offer. After doing so, your initial profile page will look something like this:

![Initial Profile](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/initial_profile.png?raw=true)

To edit your appointment information, such as the services you offer, click on the edit icon next to `Appointment Information`:

![Profile Edit](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/adding_service_to_profile.png?raw=true)

After selecting the services you offer, you may leave other fields blank if desired, and then click `Save`.

Additionally, select the days you wish to work by clicking the `add icon` next to `Working Hours`. For demonstration purposes, I have chosen Saturdays and Sundays from 9 AM to 5 PM.

Your updated profile should look like this:

![Profile after Editing](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/profile_after_editing.png?raw=true)

### Client's Perspective: Creating Appointments

Now, users can start creating appointments. The interface for clients would appear as follows:

![Appointment Request with Staff Member](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/before_creating_appt_request.png?raw=true)

Notice that only Saturdays and Sundays are selectable, with the only staff member (you) selected by default.

Let's create an appointment request for Saturday, January 13th, 2024, at 3:00 PM:

![Creating Appointment Request](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/creating_appt_request.png?raw=true)

Next, add your personal information:

![Adding Personal Information](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/adding_client_information.png?raw=true)

### Payment Options

If the service is paid and a payment link is set in settings, the `Pay now` button will appear. If down payments are accepted, a `Down Payment` button will also be available. Otherwise, a `Finish` button will be displayed.

Upon completion, an account is created for the user, and an email is sent with appointment and account details, provided the email settings are correctly configured.

## Scheduling Recurring Appointments

*(Note: Screenshots for this feature will be added later.)*

This section describes how clients can schedule appointments that repeat over time, and how these appointments appear to administrators or staff.

### Enabling Recurring Appointments (Client View):

When a client is making an appointment, they will have an option to make it a recurring event. This is typically done through a checkbox on the appointment form.

-   **UI Element**: Look for a checkbox labeled something like:
    `[ ] Make this a recurring appointment?`

-   **Frequency Selection**: If the checkbox is selected, further options will appear:
    -   A dropdown menu to select the recurrence frequency:
        -   Daily
        -   Weekly
        -   Monthly
    -   **For "Weekly" recurrence**: Day pickers (e.g., checkboxes for Monday, Tuesday, Wednesday, etc.) will allow the client to select which days of the week the appointment should repeat.
    -   An optional date input field labeled "Repeat until" where the client can specify an end date for the recurrence. If left blank, the appointment might recur indefinitely or up to a system-defined limit.

-   **Form Representation Example**:

    ```
    Service: Consultation
    Date: 2023-10-26
    Time: 10:00 AM
    Staff: Dr. Smith

    [x] Make this a recurring appointment?

    Frequency: [Weekly \v]
    Repeat on: [x] Mon  [ ] Tue  [x] Wed  [ ] Thu  [ ] Fri  [ ] Sat  [ ] Sun
    Repeat until: [2023-12-31] (optional)
    ```

### Understanding Recurrence Details (Client View):

After setting up a recurring appointment, the system should provide a clear summary of the recurrence schedule before final confirmation. This helps the client verify their settings.

-   **Confirmation Text Example**: "Your appointment for Consultation with Dr. Smith is scheduled for 10:00 AM, repeating every Monday and Wednesday, starting on 2023-10-26 until 2023-12-31."

### Viewing Recurring Appointments (Admin/Staff View):

In the admin or staff interface, recurring appointments should be clearly distinguishable from single, non-repeating appointments.

-   **Indicators**: This might be through a special icon, a note in the appointment details, or a separate view for recurring series. For example, an appointment entry might show "Repeats weekly (M, W) until 2023-12-31".
-   *(Details on managing recurring series, like editing or deleting the entire series versus a single instance, will be covered in advanced documentation.)*

### Managing Appointments

As an admin, you can now view the newly created appointment in your staff member appointment list:

![Admin Appointments](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/admin_appointments.png?raw=true)

In the admin interface, you have various options to manage appointments, such as editing, adding new appointments, deleting, or rescheduling them by dragging and dropping.

### Video Tutorial

For a more comprehensive guide, including visual demonstrations of these steps, please watch the following video tutorial:

[Link to Short Video Demo](https://youtu.be/q1LSruYWKbk)
