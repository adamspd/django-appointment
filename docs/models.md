- [Django Appointment System](#django-appointment-system)
  * [Models](#models)
    + [Service](#service)
    + [AppointmentRequest](#appointmentrequest)
    + [Appointment](#appointment)
    + [Config](#config)
    + [PaymentInfo](#paymentinfo)
    + [EmailVerificationCode](#emailverificationcode)


# Django Appointment System

## Models

### Service
Represents a service provided by the appointment system.

#### Attributes:
- `name` (str): The name of the service. (i.e. 'House Cleaning')
- `description` (str): The description of the service (optional, i.e. '1 cleaner etc...').
- `duration` (datetime.timedelta): The duration of the service. (i.e. '01:00:00' for 1 hour).
- `price` (decimal.Decimal): The price of the service. (i.e. 100.00).
- `down_payment` (decimal.Decimal): The down payment for the service (default 0).
- `currency` (str): The currency code for the price (default 'USD').
- `image` (django.db.models.ImageField): The image associated with the service (optional).

#### Methods:
- `get_name()`: Get the name of the service.
- `get_description()`: Get the description of the service.
- `get_duration()`: Get the duration of the service in human-readable format.
- `get_price()`: Get the price of the service.
- `get_price_text()`: Get the formatted text of the service price.
- `get_down_payment()`: Get the down payment for the service.
- `get_currency()`: Get the currency code for the price.
- `get_image()`: Get the image associated with the service.
- `get_image_url()`: Get the URL of the image associated with the service.
- `get_created_at()`: Get the creation timestamp of the service.
- `get_updated_at()`: Get the last update timestamp of the service.
- `is_a_paid_service()`: Check if the service is a paid service.
- `accepts_down_payment()`: Check if the service accepts down payment.

### AppointmentRequest
Represents an appointment request made by a client.

#### Attributes:
- `date` (datetime.date): The date of the appointment request.
- `start_time` (datetime.time): The start time of the appointment request.
- `end_time` (datetime.time): The end time of the appointment request.
- `service` (Service): The service associated with the appointment request.
- `payment_type` (str): The payment type of the appointment request ('full' or 'down', default 'full').
- `id_request` (str): The unique ID for the appointment request.

#### Methods:
- `get_date()`: Get the date of the appointment request.
- `get_start_time()`: Get the start time of the appointment request.
- `get_end_time()`: Get the end time of the appointment request.
- `get_service()`: Get the service associated with the appointment request.
- `get_service_name()`: Get the name of the service associated with the appointment request.
- `get_service_duration()`: Get the duration of the service associated with the appointment request.
- `get_service_price()`: Get the price of the service associated with the appointment request.
- `get_service_down_payment()`: Get the down payment for the service associated with the appointment request.
- `get_service_image()`: Get the image associated with the service of the appointment request.
- `get_service_image_url()`: Get the URL of the image associated with the service of the appointment request.
- `get_service_description()`: Get the description of the service associated with the appointment request.
- `get_id_request()`: Get the unique ID for the appointment request.
- `is_a_paid_service()`: Check if the service associated with the appointment request is a paid service.
- `accepts_down_payment()`: Check if the service associated with the appointment request accepts down payment.
- `get_payment_type()`: Get the payment type of the appointment request.
- `get_created_at()`: Get the creation timestamp of the appointment request.
- `get_updated_at()`: Get the last update timestamp of the appointment request.

### Appointment
Represents an appointment made by a client.

#### Attributes:
- `client` (AppointmentClientModel): The client associated with the appointment.
- `appointment_request` (AppointmentRequest): The appointment request associated with the appointment.
- `phone` (str): The phone number of the client for the appointment (optional).
- `address` (str): The address of the client for the appointment (optional).
- `want_reminder` (bool): Flag indicating if the client wants a reminder for the appointment (default False).
- `additional_info` (str): Additional information provided by the client for the appointment (optional).
- `paid` (bool): Flag indicating if the appointment is paid (default False).
- `amount_to_pay` (decimal.Decimal): The amount to pay for the appointment (optional).
- `id_request` (str): The unique ID for the appointment.

#### Methods:
- `get_client()`: Get the client associated with the appointment.
- `get_start_time()`: Get the start time of the appointment.
- `get_end_time()`: Get the end time of the appointment.
- `get_service_name()`: Get the name of the service associated with the appointment.
- `get_service_price()`: Get the price of the service associated with the appointment.
- `get_service_down_payment()`: Get the down payment for the service associated with the appointment.
- `get_service_img()`: Get the image associated with the service of the appointment.
- `get_service_img_url()`: Get the URL of the image associated with the service of the appointment.
- `get_service_description()`: Get the description of the service associated with the appointment.
- `get_appointment_date()`: Get the date of the appointment.
- `get_phone()`: Get the phone number of the client for the appointment.
- `get_address()`: Get the address of the client for the appointment.
- `get_want_reminder()`: Check if the client wants a reminder for the appointment.
- `get_additional_info()`: Get the additional information provided by the client for the appointment.
- `is_paid()`: Check if the appointment is paid.
- `get_appointment_amount_to_pay()`: Get the amount to pay for the appointment.
- `get_appointment_currency()`: Get the currency code for the appointment.
- `get_appointment_id_request()`: Get the unique ID for the appointment.
- `get_created_at()`: Get the creation timestamp of the appointment.
- `get_updated_at()`: Get the last update timestamp of the appointment.
- `set_appointment_paid_status(status: bool)`: Set the paid status of the appointment.

### Config
Represents configuration settings for the appointment system.

#### Attributes:
- `slot_duration` (int): Minimum time for an appointment in minutes (recommended 30, optional -> '00:30:00').
- `lead_time` (datetime.time): Time when the appointment system starts working (optional, i.e. 08:00:00).
- `finish_time` (datetime.time): Time when the appointment system stops working (optional, i.e. 17:00:00).
- `appointment_buffer_time` (float): Time between now and the first available slot for the current day
                                     (doesn't affect tomorrow, optional, i.e. '1.5' for 1 hour and 30 minutes).
- `website_name` (str): Name of the website (optional, default used: 'Website').

#### Methods:
- None

### PaymentInfo
Represents payment information for an appointment.

#### Attributes:
- `appointment` (Appointment): The appointment associated with the payment information.

#### Methods:
- `get_id_request()`: Get the unique ID for the appointment associated with the payment information.
- `get_amount_to_pay()`: Get the amount to pay for the appointment associated with the payment information.
- `get_currency()`: Get the currency code for the appointment associated with the payment information.
- `get_name()`: Get the name of the service associated with the appointment of the payment information.
- `get_img_url()`: Get the URL of the image associated with the service of the appointment of the payment information.
- `set_paid_status(status: bool)`: Set the paid status of the appointment associated with the payment information.
- `get_user_name()`: Get the first name of the client associated with the appointment of the payment information.
- `get_user_email()`: Get the email of the client associated with the appointment of the payment information.

### EmailVerificationCode
Represents an email verification code for a user.

#### Attributes:
- `user` (AppointmentClientModel): The user associated with the email verification code.
- `code` (str): The email verification code.

#### Methods:
- None