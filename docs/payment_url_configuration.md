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

Even if you're using a direct external URL for payment, you might need to pass in details like the amount, description,
and other meta-data to your payment gateway. Here's how you can retrieve this information:

**1.** When you set the `APPOINTMENT_PAYMENT_URL` to a direct URL, make sure to include placeholders for the information
   you'll be sending. For example:

```python
APPOINTMENT_PAYMENT_URL = "https://paymentgateway.com/your_payment_page?amount={amount}&description={description}"
```

**2.** Before redirecting the user to this URL, you'll need to replace these placeholders with the actual values. You can
   fetch the required details from the `PaymentInfo` model using the `object_id` and `id_request` values:

```python
from appointment.models import PaymentInfo

object_id = 1  # Replace with the actual object ID
id_request = "abc123"  # Replace with the actual ID request

payment_info = PaymentInfo.objects.get(id=object_id, id_request=id_request)
amount = payment_info.appointment.service.cost  # Or any other field you need
description = f"Payment for {payment_info.appointment.service.name}"  # As an example
```

**3.** Once you have retrieved the required details, replace the placeholders in the `APPOINTMENT_PAYMENT_URL`:

```python
APPOINTMENT_PAYMENT_URL = "https://paymentgateway.com/your_payment_page?amount={amount}&description={description}"
amount = 300  # Replace with actual value like payment_info.appointment.service.price
description = "Payment for service"  # Replace with actual value like payment_info.appointment.service.name

payment_url = APPOINTMENT_PAYMENT_URL.format(amount=amount, description=description)
```

**4.** This `payment_url` can now be used to redirect the user to the payment gateway with the correct transaction details.

Please note: The exact parameters (like `amount`, `description`, etc.) and their format depend on your payment gateway's
API documentation. Ensure that you're sending the correct information as required by your payment provider.

### 2. Internal Django View:

If you wish to handle the payment process within your Django application (e.g., to integrate with a specific payment
gateway's API or to add additional processing steps), you can create a custom Django view and set its URL pattern as
the `APPOINTMENT_PAYMENT_URL`.

For instance, if you name your URL pattern "appointment:process_payment", you would set:

```python
APPOINTMENT_PAYMENT_URL = "appointment:process_payment"
```

## Creating a Custom Django View for Payment:

Here's a basic outline of how you can set up a custom Django view to handle the payment process:

**1.** In your `urls.py`:

```python
from django.urls import path
from appointment import views

urlpatterns = [
    path('process_payment/<int:object_id>/<str:id_request>/', views.process_payment, name='process_payment'),
# ... other URL patterns ...
]
```

**2.** In your `views.py`:

```python
from django.shortcuts import render, get_object_or_404
from appointment.models import PaymentInfo

def process_payment(request, object_id, id_request):
  payment_info = get_object_or_404(PaymentInfo, id=object_id, id_request=id_request)
  
  # Here, you can extract necessary information from the payment_info object
  # and integrate with your payment gateway's API or perform other required tasks.

  # For demonstration purposes:
  amount_to_pay = payment_info.appointment.get_service_price()  # Just an example, adjust based on your model structure

  # Redirect to the payment gateway, render a payment form, or handle as needed:
  return render(request, 'payment_page.html', {'amount': amount_to_pay})

```

**3.** Ensure your view handles the payment process as required. You might need to integrate with a third-party payment
   gateway, handle transaction verification, etc. The provided `object_id` and `id_request` allow you to fetch all
   relevant details about the payment from the `PaymentInfo` model.
