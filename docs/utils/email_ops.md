# Django Appointment 📦: `email_operations.py`

This module provides functions to handle email-related operations in the Django appointment system.

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
  verification code and sends it to the specified email.
