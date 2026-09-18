# `email_ops.py`

This module provides functions to handle email-related operations in the Django appointment system.

All of these look for a custom template before using the packaged default — see
[Custom templates](../custom-templates.md) for the names and the context each one receives.

## Overview:

- [Module Metadata](#module-metadata)
- [Email Message Retrieval](#email-message-retrieval)
- [Email Sending Operations](#email-sending-operations)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.1.0

## Email Message Retrieval:

- **get_thank_you_message**: Retrieve the appropriate email message based on the status of an appointment request. This
  involves determining whether the appointment has a payment URL, accepts a down payment, or neither.

## Email Sending Operations:

- **send_thank_you_email**: Send a thank-you email to the client after they book an appointment. The email content is
  determined based on the appointment request, client details, and optional additional details provided.

- **send_verification_email**: Forward an email verification code to a user's email address. The function generates a
  verification code and sends it to the specified email. Falls back to a plain text email when no custom
  `verification.html` template exists.

- **send_reset_link_to_staff_member**: Email a newly created staff member (or client) the link that lets them set
  their password. Creates a [`PasswordResetToken`](../models.md#passwordresettoken) and falls back to a plain text
  email when no custom `password_reset.html` template exists.

- **notify_admin_about_appointment**: Notify the site admins and the assigned staff member that a new appointment has
  been booked, with an ICS file attached. Each address is only notified once.

- **send_reschedule_confirmation_email**: Send the client the link confirming a requested reschedule, showing the old
  and the new slot side by side.

- **notify_admin_about_reschedule**: Notify the site admins and the assigned staff member that a client has requested
  a reschedule, with an updated ICS file attached.
