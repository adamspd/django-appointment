# Django Appointment 📦: `session_operations.py`

This module offers utility functions to manage session-based operations related to appointments in the Django appointment system.

## Overview:

- [Module Metadata](#module-metadata)
- [Functions](#functions)
  - [Handling Email Operations](#handling-email-operations)
  - [Session Data Retrieval](#session-data-retrieval)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.1.0

## Functions:

### Handling Email Operations:

- **login_or_create_user_by_mail(request, client_data, appointment_data, appointment_request_id, id_request)**:
  - Called when an unauthenticated user submit an appointment request. If the provided email is not the database, a new account is created. In both cases, a verification code email is sent and the client is redirected to the verification page.

- **handle_email_change(request, user, email)**:
  - Manages email changes by sending a verification email to the new email and handling session data accordingly.

### Session Data Retrieval:

- **get_appointment_data_from_session(request)**:
  - Retrieves the appointment-related data from session variables.
