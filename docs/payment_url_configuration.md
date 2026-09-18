# Appointment Payment URL Configuration

When integrating the appointment system into your project, one key aspect to configure is the payment URL. This URL
determines where the user is redirected for payment processing after an appointment is created.

## Configuration Options:

### 1. Direct Payment Gateway URL:

If you have a direct URL to a payment gateway or an external payment page, you can set
the `APPOINTMENT_PAYMENT_URL` to that URL. For instance:

```python
APPOINTMENT_PAYMENT_URL = "https://paymentgateway.com/your_payment_page"
```

When this option is used, the system will redirect the user directly to the specified URL for payment.

### Retrieving Payment Details for Direct Payment Gateway URL:

!!! warning "The external URL is used verbatim"
    When `APPOINTMENT_PAYMENT_URL` is an external link, the package redirects to it **exactly as written** — it does
    not format placeholders, append query parameters, or pass the appointment along in any way. A URL such as
    `.../pay?amount={amount}` is sent to the browser with the literal `{amount}` still in it.

    If your gateway needs per-appointment details such as the amount or a description, use the
    [internal Django view](#2-internal-django-view) approach below: it is the only option that receives the
    appointment's identifiers, and your own view can then build the gateway URL and redirect on to it.

A direct URL is therefore only suitable when the payment page is generic — for example a fixed "pay your deposit"
page where the client enters the amount themselves, or a gateway page you have already pre-configured.

### 2. Internal Django View:

If you wish to handle the payment process within your Django application (e.g., to integrate with a specific payment
gateway's API or to add additional processing steps), you can create a custom Django view and set its URL pattern as
the `APPOINTMENT_PAYMENT_URL`.

Set it to the URL pattern's dotted `namespace:name`. For instance, if your pattern is named `process_payment`
inside an app whose `app_name` is `payments`, you would set:

```python
APPOINTMENT_PAYMENT_URL = "payments:process_payment"
```

The package treats the value as a reverse target when it contains a `:` and no `/`; anything else is treated as
an external link.

## Creating a Custom Django View for Payment:

Here's a basic outline of how you can set up a custom Django view to handle the payment process:

**1.** In your `urls.py`. The package reverses the URL with exactly two keyword arguments, `object_id` and
`id_request`, so your pattern must accept both under those names:

```python
# payments/urls.py
from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('process-payment/<int:object_id>/<str:id_request>/', views.process_payment, name='process_payment'),
    # ... other URL patterns ...
]
```

**2.** In your `views.py`:

```python
from django.shortcuts import get_object_or_404, render

from appointment.models import PaymentInfo


def process_payment(request, object_id, id_request):
    # `id_request` belongs to the appointment, not to PaymentInfo, hence the `appointment__` lookup.
    payment_info = get_object_or_404(PaymentInfo, id=object_id, appointment__id_request=id_request)

    appointment = payment_info.appointment

    # Everything you are likely to need is reachable from the PaymentInfo instance:
    amount_to_pay = payment_info.get_amount_to_pay()  # or appointment.get_appointment_amount_to_pay()
    currency = payment_info.get_currency()
    description = payment_info.get_name()  # the service name
    client_name = payment_info.get_user_name()
    client_email = payment_info.get_user_email()

    # Build your gateway URL, call its API, or render your own payment form:
    return render(request, 'payment_page.html', {
        'amount': amount_to_pay,
        'currency': currency,
        'description': description,
        'appointment': appointment,
    })
```

**3.** Once the payment succeeds, mark the appointment as paid so the rest of the system stays in sync:

```python
payment_info.set_paid_status(True)
```

**4.** Ensure your view handles the payment process as required. You might need to integrate with a third-party payment
   gateway, handle transaction verification, etc. The provided `object_id` and `id_request` allow you to fetch all
   relevant details about the payment from the `PaymentInfo` model.

!!! note "Model gotchas"
    - `PaymentInfo` has no `id_request` **field** — it has a `get_id_request()` method that proxies the appointment's.
      Filter on `appointment__id_request`.
    - `Appointment` has no `service` attribute either; the service is reached through the appointment request. Use the
      `Appointment` and `PaymentInfo` accessor methods (`get_service_name()`, `get_appointment_amount_to_pay()`, ...)
      rather than traversing relations by hand. See the [models reference](models.md#paymentinfo).
