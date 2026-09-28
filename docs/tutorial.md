# Django Appointment System: Screenshots and Tutorial

Welcome to the Django Appointment System! This guide will walk you through setting up and using the system, complete with screenshots and a video tutorial.

## Getting Started

After completing the initial setup steps - making migrations, migrating, running the server, and creating a superuser - you might want to create an appointment as a client. However, this is not possible initially as no services or staff members are yet configured.

### Adding a Service

Your first step is to add a service. Navigate to the admin page and add a service at
`/app-admin/add-service/`, under the prefix you mounted the package on. With the
`path('appointment/', include('appointment.urls'))` used in the
[installation guide](getting-started.md#installation), that is:

```
https://mysuperwebsite.com/appointment/app-admin/add-service/
```

![Creating Service](screenshots/creating_service.png)

### Attempting to Create an Appointment

If you attempt to create an appointment request now, it's still not possible as there are no staff members yet:

![Appointment Request without Staff Member](screenshots/appointment_request_w_sm.png)

Similarly, the staff calendar is empty:

![Appointment List without Staff Member](screenshots/appointment_list_admin.png)

### Adding a Staff Member

To add a staff member, visit:

![Staff Member List](screenshots/staff_member_list.png)

You can either add a new staff member or assign yourself as a staff member, especially if you are a superuser. In this example, I will use the `Staff me` button.

### Updating Your Profile

Once you have created a staff member profile, you need to specify the services you offer. After doing so, your initial profile page will look something like this:

![Initial Profile](screenshots/initial_profile.png)

To edit your appointment information, such as the services you offer, click `Edit` next to `Appointment Information`. Each service is a checkbox:

![Profile Edit](screenshots/adding_service_to_profile.png)

After selecting the services you offer, you may leave other fields blank if desired, and then click `Save`.

Additionally, add the days you wish to work with the `Add` button next to `Working Hours`. For demonstration purposes, I have chosen Saturdays and Sundays from 9 AM to 5 PM. The profile shows the whole week, with each day's hours as a bar.

Your updated profile should look like this:

![Profile after Editing](screenshots/profile_after_editing.png)

### Client's Perspective: Creating Appointments

Now, users can start creating appointments. The interface for clients would appear as follows:

![Appointment Request with Staff Member](screenshots/before_creating_appt_request.png)

Notice that only Saturdays and Sundays are selectable, with the only staff member (you) selected by default.

Let's pick a Saturday and the 3 PM slot. The summary on the right follows the choice, and `Next` becomes clickable:

![Creating Appointment Request](screenshots/creating_appt_request.png)

Next, add your personal information:

![Adding Personal Information](screenshots/adding_client_information.png)

### Payment Options

If the service is paid and a payment link is set in settings, the `Pay now` button will appear. If down payments are accepted, a `Down Payment` button will also be available. Otherwise, a `Finish` button will be displayed.

Upon completion, an account is created for the user, and an email is sent with appointment and account details, provided the email settings are correctly configured.

### Managing Appointments

As an admin, you can now view the newly created appointment in your staff member appointment list:

![Admin Appointments](screenshots/admin_appointments.png)

In the admin interface, you have various options to manage appointments, such as editing, adding new appointments, deleting, or rescheduling them by dragging and dropping.

### Video Tutorial

For a more comprehensive guide, including visual demonstrations of these steps, please watch the following video tutorial:

[Link to Short Video Demo](https://youtu.be/q1LSruYWKbk)
