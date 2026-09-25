# Views

The client-facing views live in `appointment/views.py`. The staff and superuser views are documented separately in
[Admin views](admin_views.md).

## Ajax endpoints

### get available slots ajax
This view function handles AJAX requests to get available slots for a selected date.

#### Args:
- `request` (django.http.HttpRequest): The request instance. Reads three values from the query string:
  `selected_date`, `staff_member`, and the optional `service_id`. When `service_id` is given, the service's real
  duration is used as the overlap-check window, so a service longer than the slot step no longer offers slots it
  cannot finish in.

#### Returns:
- `django.http.JsonResponse`: A JSON response carrying `message` and `success`, plus `date_chosen` (the date
  rendered in the active locale), `date_iso`, `staff_member`, and `available_slots` — a list of
  `[iso_datetime, localized_time]` pairs such as `[["2026-07-29T09:30:00", "9:30 a.m."], ...]`. Failures add an
  `errorCode` and, for a day off, a non-working day or a fully booked day, `no_availability: true`.

### get next available date ajax
This view function handles AJAX requests to get the next available date for a service. It scans forward day by day
from today, stopping at the first date with a free slot or after **90 days**.

#### Args:
- `request` (django.http.HttpRequest): The request instance. Reads `staff_member` from the query string.
- `service_id` (int): The ID of the service.

#### Returns:
- `django.http.JsonResponse`: A JSON response containing `next_available_date` as an ISO date. When nothing is free
  within the 90-day window it returns a failure carrying the `NEXT_AVAILABILITY_NOT_FOUND`
  [error code](utils/error_codes.md); when no staff member was selected, `STAFF_ID_REQUIRED`.

### get non working days ajax
This view function handles AJAX requests to get the days a staff member does not work, so the calendar can render
them as un-selectable.

#### Args:
- `request` (django.http.HttpRequest): The request instance. Reads `staff_member` from the query string.

#### Returns:
- `django.http.JsonResponse`: A JSON response containing the list of non-working days, or an error when no staff
  member was selected.

## Booking flow

### appointment request
This view function handles requests to book an appointment for a service.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `service_id` (int): The ID of the service. Optional.
- `staff_member_id` (int): The ID of a staff member to pre-select. Optional.

#### Returns:
- `django.http.HttpResponse`: The rendered HTML page.

### appointment request submit
This view function handles the submission of the appointment request form.

#### Args:
- `request` (django.http.HttpRequest): The request instance.

#### Returns:
- `django.http.HttpResponse`: The rendered HTML page.

### appointment client information
This view function handles client information submission for an appointment. Authenticated users have their
appointment created directly; anonymous users are sent through email verification first.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `appointment_request_id` (int): The ID of the appointment request.
- `id_request` (str): The unique ID of the appointment request.

#### Returns:
- `django.http.HttpResponse`: The rendered HTML page.

### create appointment
This function creates a new appointment, notifies the admin, and redirects to the payment page or the thank you page.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `appointment_request_obj` (appointment.models.AppointmentRequest): The AppointmentRequest instance.
- `client_data` (dict): The client data.
- `appointment_data` (dict): The appointment data.

#### Returns:
- `django.http.HttpResponseRedirect`: The redirect response.

### redirect to payment or thank you page
This function redirects to the payment page or the thank you page based on the configuration. The payment page is
only used when `APPOINTMENT_PAYMENT_URL` is set **and** the service is a paid one.

#### Args:
- `appointment` (appointment.models.Appointment): The Appointment instance.

#### Returns:
- `django.http.HttpResponseRedirect`: The redirect response.

### verify user and login
This function verifies the user's email and logs the user in.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `user`: The User instance.
- `code` (str): The verification code.

#### Returns:
- `bool`: True if the user is verified and logged in, False otherwise.

### enter verification code
This view function handles the submission of the email verification code.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `appointment_request_id` (int): The ID of the appointment request.
- `id_request` (str): The unique ID of the appointment request.

#### Returns:
- `django.http.HttpResponse`: The rendered HTML page.

### default thank you
This view function handles the default thank you page. It also sends the confirmation email to the client, on the first
visit after a booking or a reschedule only.

The page is shown to the browser that booked or rescheduled the appointment (the booking and reschedule views record
it in the session), to the client's account, to the appointment's staff member and to superusers. Anyone else gets a
`404`, so appointment ids can't be tried in turn.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `appointment_id` (int): The ID of the appointment.

#### Returns:
- `django.http.HttpResponse`: The rendered HTML page.

## Password setup

### set passwd
This view function handles the password creation link emailed to a newly created client or staff member. The token is
validated through [`PasswordResetToken`](models.md#passwordresettoken) and invalidated once the password is set.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `uidb64` (str): The base64-encoded user ID.
- `token` (str): The password reset token.

#### Returns:
- `django.http.HttpResponse`: The rendered form, success, or error page.

## Rescheduling

### prepare reschedule appointment
This view function renders the slot picker for rescheduling an existing appointment. It refuses the request with a
`403` page when the reschedule limit has been reached, and it only offers a different staff member when
`allow_staff_change_on_reschedule` is enabled in [Config](models.md#config).

!!! warning "How the limit is actually applied"
    The limit is checked by `can_appointment_be_rescheduled`, which counts the reschedule history entries created in
    the **last 5 minutes** — so it behaves as a rate limit, not as a lifetime cap. It compares that count against
    `Service.reschedule_limit` when the service has `allow_rescheduling` enabled, and against
    `Config.default_reschedule_limit` otherwise. Note that a service with `allow_rescheduling` disabled is therefore
    not blocked from rescheduling; it simply falls back to the global default limit.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `id_request` (str): The unique ID of the appointment request.

#### Returns:
- `django.http.HttpResponse`: The rendered HTML page.

### reschedule appointment submit
This view function handles the submission of the rescheduling form. It records an
[`AppointmentRescheduleHistory`](models.md#appointmentreschedulehistory) entry in the `pending` state and emails the
client a confirmation link.

#### Args:
- `request` (django.http.HttpRequest): The request instance.

#### Returns:
- `django.http.HttpResponse`: The rendered HTML page.

### confirm reschedule
This view function confirms a pending reschedule from the link sent by email, moves the appointment to its new slot,
flips the history entry to `confirmed` (rewriting it to hold the slot the appointment just left), and notifies the
admin and the staff member. The link is only valid for **5 minutes** after the reschedule was requested.

#### Args:
- `request` (django.http.HttpRequest): The request instance.
- `id_request` (str): The unique ID of the reschedule history entry.

#### Returns:
- `django.http.HttpResponseRedirect`: A redirect to the thank-you page for the moved appointment. A stale or
  already-used link renders the `404` page instead, with a `404` status.
