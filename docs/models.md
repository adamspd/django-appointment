- [Django Appointment System]()
    * [Models](#models)
        + [Service](#service)
        + [StaffMember](#staffmember)
        + [AppointmentRequest](#appointmentrequest)
        + [Appointment](#appointment)
        + [Config](#config)
        + [PaymentInfo](#paymentinfo)
        + [EmailVerificationCode](#emailverificationcode)
        + [DayOff](#dayoff)
        + [WorkingHours](#workinghours)

# Django Appointment 📦

## Models

> **Notes** ⚠️ : All the models have a `created_at` and `updated_at` field. These fields are automatically updated when the
> model is created or updated. They are not editable by the user.

### Service

The `Service` model encapsulates a service provided by the appointment system.

#### Fields:

- `name` (CharField): The name of the service.
- `description` (TextField): Description of the service.
- `duration` (DurationField): Duration of the service.
- `price` (DecimalField): Price of the service.
- `down_payment` (DecimalField): Down payment for the service.
- `image` (ImageField): Image representing the service.
- `currency` (CharField): Currency for the price.
- `background_color` (CharField): Background color for the service presentation.

#### Methods:

- `to_dict`: Returns a dictionary representation of the service.
- `get_duration_parts`: Returns the duration of the service as a tuple of days, hours, minutes, and seconds.
- `get_duration`: Returns the duration of the service in a human-readable format (as a string).
- `get_price`: Returns the price of the service.
- `get_currency_icon`: Returns the currency symbol.
- `get_price_text`: Returns a formatted price text (as a string) that you can use in your HTML code.
- `get_down_payment`: Returns the down payment amount for the service.
- `get_down_payment_text`: Returns a formatted down payment text that you can use in your HTML code.
- `get_image_url`: Returns the URL of the image associated with the service.
- `is_a_paid_service`: Returns whether the service is paid (true of false).
- `accepts_down_payment`: Returns whether the service accepts a down payment (true of false).

### StaffMember

The `StaffMember` model represents a staff member in the appointment system. A staff member is a user that offers
one or more services in the one defined by the admin. He can't edit/add/delete services but can choose which one he
offers. He can update his profile, change his working hours or add vacation days (days off).

#### Fields:

- `user` (OneToOneField): Related User model instance, will be granted Django's staff status.
- `services_offered` (ManyToManyField): Services offered by the staff member.
- `slot_duration` (PositiveIntegerField): Minimum time for an appointment in minutes.
- `lead_time` (TimeField): Time when the staff member starts working.
- `finish_time` (TimeField): Time when the staff member stops working.
- `appointment_buffer_time` (FloatField): Buffer time for the first available slot.
- `work_on_saturday` (BooleanField): Whether the staff member works on Saturday.
- `work_on_sunday` (BooleanField): Whether the staff member works on Sunday.

#### Methods:

- `get_slot_duration`: Returns the slot duration.
- `get_slot_duration_text`: Returns the slot duration in a human-readable format.
- `get_lead_time`: Returns the lead time defined by the staff member first else default one.
- `get_finish_time`: Returns the finish time defined by the staff member first else default one.
- `works_on_both_weekends_day`: Returns whether the staff member works on both weekend days.
- `get_staff_member_name`: Returns the name of the staff member.
- `get_staff_member_first_name`: Returns the first name of the staff member.
- `get_non_working_days`: Returns a list of non-working days.
- `get_weekend_days_worked_text`: Returns a string representation of the weekend days worked.
- `get_services_offered`: Returns the services offered by the staff member.
- `get_service_offered_text`: Returns a string representation of the services offered.
- `get_appointment_buffer_time`: Returns the appointment buffer time.
- `get_appointment_buffer_time_text`: Returns the appointment buffer time in a human-readable format.
- `get_days_off`: Returns the days off for the staff member.
- `get_working_hours`: Returns the working hours for the staff member.
- `update_upon_working_hours_deletion`: Updates the weekend working status upon deletion of working hours.
- `is_working_day`: Returns whether a given day is a working day (true or false).

### AppointmentRequest

The `AppointmentRequest` model represents an appointment request made by a client. It is not yet an appointment, and it
is not associated with the client. It is created when the client chooses a service, staff member, and date/time for the
appointment (See screenshot below).

![Choosing staff member and date/time for appointment](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/appointment_request.png?raw=true)

It will be linked to an appointment when the client enters their information. We make sure that the start time is before
the end time and on save, we generate an `id_request` if none exists, make sure that the appointment request date is
not in the past.

#### Fields:

- `date` (DateField): The date of the appointment request.
- `start_time` (TimeField): The starting time of the appointment.
- `end_time` (TimeField): The ending time of the appointment, set automatically by adding service duration.
- `service` (ForeignKey): The service being requested, linking to the `Service` model.
- `staff_member` (ForeignKey): The staff member assigned to the appointment, linking to the `StaffMember` model.
- `payment_type` (CharField): The type of payment for the appointment (e.g., 'full').
- `id_request` (CharField): An ID for the appointment request.

#### Methods:

- `get_service_name`: Returns the name of the service.
- `get_service_price`: Returns the price of the service.
- `get_service_down_payment`: Returns the down payment amount for the service.
- `get_service_image`: Returns the image of the service.
- `get_service_image_url`: Returns the URL of the service's image.
- `get_service_description`: Returns the description of the service.
- `get_id_request`: Returns the ID of the appointment request.
- `is_a_paid_service`: Returns whether the service is paid.
- `accepts_down_payment`: Returns whether the service accepts a down payment.

### Appointment

The `Appointment` model represents an appointment made by a client. It is created when the client confirms the
appointment request.

#### Fields:

- `client` (ForeignKey): The client who made the appointment, linking to the User model.
- `appointment_request` (OneToOneField): The appointment request that was confirmed.
- `phone` (PhoneNumberField): The client's phone number.
- `address` (CharField): A general address for the client (e.g., city and state).
- `want_reminder` (BooleanField): Indicates if the client wants a reminder.
- `additional_info` (TextField): Any additional information provided by the client.
- `paid` (BooleanField): Indicates if the appointment has been paid for.
- `amount_to_pay` (DecimalField): The amount to be paid for the appointment.
- `id_request` (CharField): An ID for the appointment.

#### Methods:

- `get_client_name`: Returns the full name of the client.
- `get_date`: Returns the date of the appointment.
- `get_start_time`: Returns the starting time of the appointment.
- `get_end_time`: Returns the ending time of the appointment.
- `get_service`: Returns the service associated with the appointment.
- `get_service_name`: Returns the name of the service.
- `get_service_duration`: Returns the duration of the service.
- `get_staff_member_name`: Returns the name of the staff member associated with the appointment.
- `get_staff_member`: Returns the staff member associated with the appointment.
- `get_service_price`: Returns the price of the service.
- `get_service_down_payment`: Returns the down payment amount for the service.
- `get_service_img`: Returns the image of the service.
- `get_service_img_url`: Returns the URL of the service's image.
- `get_service_description`: Returns the description of the service.
- `get_appointment_date`: Returns the date of the appointment.
- `is_paid`: Returns if the appointment has been paid for.
- `is_paid_text`: Returns a string representation of the paid status.
- `get_appointment_amount_to_pay`: Returns the amount to be paid for the appointment.
- `get_appointment_amount_to_pay_text`: Returns a formatted amount to pay text.
- `get_appointment_currency`: Returns the currency of the appointment price.
- `get_appointment_id_request`: Returns the ID of the appointment.
- `set_appointment_paid_status`: Sets the paid status of the appointment.
- `get_absolute_url`: Returns the absolute URL for the appointment.
- `get_background_color`: Returns the background color of the service.
- `is_valid_date`: Static method that checks if a given date is valid for an appointment.
- `is_owner`: Returns whether the given user is the owner of the appointment.
- `to_dict`: Returns a dictionary representation of the appointment.

### Config

The `Config` model represents configuration settings for the appointment system. There can only be one `Config` object
in the database. If you want to change the settings, you must edit the existing `Config` object.

#### Fields:

- `slot_duration` (PositiveIntegerField): Minimum time for an appointment in minutes.
- `lead_time` (TimeField): The time when work starts.
- `finish_time` (TimeField): The time when work stops.
- `appointment_buffer_time` (FloatField): The time between the current moment and the first available slot for the
  current day (does not affect the next day).
- `website_name` (CharField): The name of the website.
- `app_offered_by_label` (CharField): Label `offered by` on appointment's page. Can be anything you want
  i.e.: `choose photographer` or `choose dentist` etc... (See screenshot below).

![app_offered_by_label](https://github.com/adamspd/django-appointment/blob/main/docs/screenshots/offered_by.png?raw=true)

#### Methods:

- `delete`: Overrides the default delete method to prevent deletion of the `Config` object once created.
- `get_instance`: Class method that returns the single instance of the `Config` object or creates one if it doesn't
  exist.

### PaymentInfo

The `PaymentInfo` model represents payment information for an appointment.

#### Fields:

- `appointment` (ForeignKey): The appointment for which the payment information is associated, linking to
  the `Appointment` model.

#### Methods:

- `get_id_request`: Returns the ID of the associated appointment.
- `get_amount_to_pay`: Returns the amount to be paid for the associated appointment.
- `get_currency`: Returns the currency of the associated appointment's price.
- `get_name`: Returns the name of the service associated with the appointment.
- `get_img_url`: Returns the URL of the service's image associated with the appointment.
- `set_paid_status`: Sets the paid status of the associated appointment.
- `get_user_name`: Returns the first name of the client who made the appointment.
- `get_user_email`: Returns the email of the client who made the appointment.

### EmailVerificationCode

The `EmailVerificationCode` model represents an email verification code for a user when the email already exists in the
database or when a user wants to change email addresses.

#### Fields:

- `user` (ForeignKey): The user associated with the verification code, linking to the User model.
- `code` (CharField): The verification code itself.

#### Methods:

- `generate_code`: Class method that generates a unique code comprised of uppercase letters and digits. It then
  associates this code with the provided user and saves it in the database. This method returns the generated code.
- `check_code`: Compares the provided code with the stored code for the user and returns a boolean indicating if they
  match.

### DayOff

The `DayOff` model represents a day off for a staff member. It has to be set for both holidays and vacations. If not, 
clients will be able to book appointments on those days. `start_date` and `end_date` are checked to make sure that the
start date is before the end date.

#### Fields:

- `staff_member` (ForeignKey): The staff member who has the day off, linking to the `StaffMember` model.
- `start_date` (DateField): The start date of the day off.
- `end_date` (DateField): The end date of the day off.
- `description` (CharField): A brief description or reason for the day off.

#### Methods:

- `is_owner`: Returns a boolean indicating if the given user ID matches the user ID of the staff member associated with
  the day off.

### WorkingHours

The `WorkingHours` model represents the working hours for a staff member on a specific day of the week. 
`start_time` is checked to make sure that it is before `end_time`.

#### Fields:

- `staff_member` (ForeignKey): The staff member associated with the working hours, linking to the `StaffMember` model.
- `day_of_week` (PositiveIntegerField): The day of the week, with choices defined by `DAYS_OF_WEEK`.
- `start_time` (TimeField): The start time of the working hours.
- `end_time` (TimeField): The end time of the working hours.

#### Methods:

- `get_start_time`: Returns the start time of the working hours.
- `get_end_time`: Returns the end time of the working hours.
- `get_day_of_week_str`: Returns the name of the day.
- `is_owner`: Returns a boolean indicating if the given user ID matches the user ID of the staff member associated with
  the working hours.

#### Meta:

- `unique_together`: Ensures that each combination of `staff_member` and `day_of_week` is unique.

