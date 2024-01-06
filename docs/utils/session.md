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

- **handle_existing_email(request, client_data, appointment_data, appointment_request_id, id_request)**:
  - Manages the scenario when the email already exists in the database. This function sends a verification email to the existing user and redirects the client to enter the verification code.

- **handle_email_change(request, user, email)**:
  - Manages email changes by sending a verification email to the new email and handling session data accordingly.

### Session Data Retrieval:

- **get_appointment_data_from_session(request)**:
  - Retrieves the appointment-related data from session variables.
