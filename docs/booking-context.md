# Keeping booking context

Sometimes a site wants to keep a few values from the moment a client books, such as the campaign that brought them
(`utm_source`, `utm_campaign`, ...). django-appointment sends a signal each time a client's appointment request is
saved. Your code listens for it, reads what it needs from the web request, and stores it in the request's
`booking_context` field. The package checks every value before it is saved.

## The signal

`appointment.signals.appointment_request_created` is sent by the public booking view (`appointment_request_submit`)
right after the client's `AppointmentRequest` is saved. It is not sent when staff create an appointment from the admin
calendar, because that request comes from a staff member's browser, not the client's.

Listeners receive:

- `sender`: the `AppointmentRequest` class.
- `appointment_request`: the saved `AppointmentRequest`.
- `request`: the `HttpRequest` it came from, so you can read the query string, the session or cookies.

If a listener raises an error, the error is logged and the booking goes on as normal.

## Recipe: keep campaign values

1. List the keys you allow in your settings. Nothing can be stored until you do:

    ```python
    APPOINTMENT_BOOKING_CONTEXT_KEYS = ['utm_source', 'utm_campaign']
    ```

2. Save the values when the client lands on your site, under your own consent rules. The booking form posts to its
   own URL, so the campaign values are usually gone by then. Keep them in the session:

    ```python
    # myapp/middleware.py
    CAMPAIGN_KEYS = ('utm_source', 'utm_campaign')


    def campaign_middleware(get_response):
        def middleware(request):
            if user_gave_consent(request):  # your own rule
                for key in CAMPAIGN_KEYS:
                    if key in request.GET:
                        request.session[key] = request.GET[key][:200]
            return get_response(request)
        return middleware
    ```

3. Listen for the signal and store the values on the appointment request:

    ```python
    # myapp/signals.py
    from django.dispatch import receiver
    from appointment.signals import appointment_request_created

    from .middleware import CAMPAIGN_KEYS


    @receiver(appointment_request_created)
    def keep_campaign(sender, appointment_request, request, **kwargs):
        context = {key: request.session[key] for key in CAMPAIGN_KEYS if key in request.session}
        if context:
            appointment_request.booking_context = context
            appointment_request.save(update_fields=['booking_context'])
    ```

    Import `myapp.signals` in your app's `AppConfig.ready()` so the listener is connected.

4. Read it back from a confirmed appointment with `appointment.get_booking_context()`. Staff who can view appointment
   requests or appointments in the Django admin see it there, read only.

## What the package checks

Every time an appointment request is saved, `booking_context` must be empty or a flat object where:

- every key is in `APPOINTMENT_BOOKING_CONTEXT_KEYS` (an unknown key is an error, it is not dropped quietly);
- every value is text, at most 200 characters;
- no value has control characters, new lines or invisible characters.

If not, `save()` raises a `ValidationError` and nothing is stored. Inside a signal listener, that error is logged and
the booking goes on. The field can't be set from any form, including the Django admin: only your code can write it.
The package never reads the URL, cookies or the session to fill it, and doesn't put it in emails, calendar files or
JSON responses.

If you'd rather keep more than this allows, use your own model instead, linked to `AppointmentRequest` by a
`OneToOneField`, and create it from the same listener.

## Things to keep in mind

- These values come from the browser and can be faked. Never use them for authorization, identity, pricing,
  eligibility or fraud checks.
- Your site owns consent, retention and access to this data. Don't store personal data, session IDs or whole cookies
  unless you have a reason and the consent to do so.
- Keep your listener fast. It runs inside the booking request.
