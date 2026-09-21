# Project structure

This application helps you to schedule appointments with your clients. It is a simple application that allows any client
to schedule an appointment for a service.

## Model Structure

The application has twelve (12) models:

1. [Service](models.md#service)
2. [StaffMember](models.md#staffmember)
3. [AppointmentRequest](models.md#appointmentrequest)
4. [AppointmentRescheduleHistory](models.md#appointmentreschedulehistory)
5. [Appointment](models.md#appointment)
6. [Config](models.md#config)
7. [PaymentInfo](models.md#paymentinfo)
8. [EmailVerificationCode](models.md#emailverificationcode)
9. [PasswordResetToken](models.md#passwordresettoken)
10. [DayOff](models.md#dayoff)
11. [Unavailability](models.md#unavailability)
12. [WorkingHours](models.md#workinghours)

## Service

It represents a service provided by the system, including details such as the name, description, duration, price, and an
image representing the service.
It also handles the currency and down payment information.
[More details here](models.md#service).

## StaffMember

This model is linked to a user and represents a staff member who offers services. It contains information about the
services offered, working hours, and availability on weekends.
[More details](models.md#staffmember).

## Appointment Request

Represents a request for an appointment made by a client.
It includes the date, start and end times, selected service,
staff member, and payment type for the appointment.

The appointment request is used to create the appointment. An appointment is considered having more information than
that, and since we don't want to overload the appointment model, we use the appointment request to store all
the information about the appointment.
[More details here](models.md#appointmentrequest).

## Appointment Reschedule History

Records each time a client asks to move an appointment. It keeps the date, time and staff member the appointment had
*before* the change, along with the reason given and whether the reschedule is still `pending` or has been
`confirmed`. This is what lets the confirmation email show "from" and "to" times, and what enforces the per-service
reschedule limit.
[More details here](models.md#appointmentreschedulehistory).

## Appointment

The appointment model is used to define the last step in the appointment scheduling.
A confirmed appointment is created when a client confirms an appointment request.
It includes the client information, appointment request details, and additional information such as phone number and
address.
[More details here](models.md#appointment).

## Config

Hold the configuration settings for the appointment system such as slot duration, working hours, and buffer time
between appointments.
[More details here](models.md#config).

## PaymentInfo

Contains payment information for an appointment, linked to a specific appointment.

The model provides several methods to access related appointment details, such as service name, price, currency, client
name, and email.
It also includes a method to update the payment status.

## EmailVerificationCode

The EmailVerificationCode model is used to represent an email verification code for a user when the email already exists
in the database.
Or when the user wants to change their email address.
The model includes a class method to generate a new verification code for a user.

## PasswordResetToken

A single-use, expiring token that lets a newly created client — or a newly created staff member — set their password
from a link sent by email. Creating a new token invalidates the user's previous ones, so only the latest link works.
[More details here](models.md#passwordresettoken).

## DayOff

The DayOff model is used to represent a day off for a staff member.
It includes the start date, the end date, an optional description, and the staff member associated with the day off.

## Unavailability

The Unavailability model blocks part of a single day for a staff member — a lunch break, a meeting, anything that
makes them unavailable without costing them the whole day. Where a day off removes entire days from the calendar, an
unavailability removes a time range from one day and leaves the rest of it bookable. The booking page filters these
out of the slots it offers.
[More details here](models.md#unavailability).

## WorkingHours

The WorkingHours model is used to represent the working hours for a staff member on a given day of the week.
It includes the day of the week, the start and end times, and the staff member associated with the working hours.

---

## Next steps

- [Configuration](configuration.md) — every setting you can override in `settings.py`.
- [Models reference](models.md) — full field and method documentation for each model.
