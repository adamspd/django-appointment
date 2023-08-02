Based on the provided code and the desired README format, here is a proposed README for the package:

---
- [Django Appointment System](#django-appointment-system)
  * [Database Operations](#database-operations)
    + [get_appointments_and_slots](#get-appointments-and-slots)
    + [get_user_by_email](#get-user-by-email)
    + [create_new_user](#create-new-user)
    + [create_and_save_appointment](#create-and-save-appointment)
    + [create_payment_info_and_get_url](#create-payment-info-and-get-url)
  * [Email Operations](#email-operations)
    + [get_thank_you_message](#get-thank-you-message)
    + [send_thank_you_email](#send-thank-you-email)
    + [send_verification_email](#send-verification-email)
  * [Session Operations](#session-operations)
    + [handle_existing_email](#handle-existing-email)
    + [get_appointment_data_from_session](#get-appointment-data-from-session)

# Django Appointment System

## Database Operations

These operations primarily focus on interacting with the database models in the Django application. 

### Get appointments and slots
Get appointments and available slots for a given date and service.

If a service is provided, the function retrieves appointments for that service on the given date. Otherwise, it retrieves all appointments for the given date.

### Get user by email
Get a user by their email address.

### Create new user
Create a new user and save it to the database.

### Create and save appointment
Create and save a new appointment based on the provided appointment request and client data.

### Create payment info and get url
Create a new payment information entry for the appointment and return the payment URL.

## Email Operations

These operations primarily focus on generating and sending emails based on various user interactions and system requirements.

### Get thank you message
Get the appropriate email message based on the appointment request.

### Send thank you email
Send a thank-you email to the client for booking an appointment.

### Send verification email
Send an email with a verification code to the user for email verification.

## Session Operations

These operations primarily focus on handling session data during user interactions with the system.

### Handle existing email
Handle the case where the email already exists in the database.

### Get appointment data from session
Get the appointment data from the session variables.

---

Note: This is just a high-level overview. For detailed descriptions of the functions and their inputs/outputs, refer directly to the function definitions in the code.