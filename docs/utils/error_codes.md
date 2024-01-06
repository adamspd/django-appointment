# Django Appointment 📦: `error_codes.py`

This module defines a set of error codes used across the Django appointment system for better error handling and
reporting.

## Overview:

- [Module Metadata](#module-metadata)
- [Error Codes](#error-codes)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.2.0

## Error Codes:

- **APPOINTMENT_CONFLICT**: Denotes a conflict with an existing appointment.
- **APPOINTMENT_NOT_FOUND**: Indicates that the specified appointment was not found.
- **DAY_OFF_CONFLICT**: Denotes a conflict with an existing day-off entry.
- **DAY_OFF_NOT_FOUND**: Indicates that the specified day-off entry was not found.
- **INVALID_DATA**: Denotes that the provided data is invalid.
- **INVALID_DATE**: Indicates that the provided date is invalid.
- **NOT_AUTHORIZED**: Denotes that the user is not authorized to perform the requested action.
- **PAST_DATE**: Indicates that the provided date is in the past.
- **STAFF_ID_REQUIRED**: Denotes that a staff ID is required but was not provided.
- **WORKING_HOURS_NOT_FOUND**: Indicates that the specified working hours entry was not found.
- **WORKING_HOURS_CONFLICT**: Denotes a conflict with an existing working hours' entry.
- **SERVICE_NOT_FOUND**: Indicates that the specified service was not found.
- **STAFF_MEMBER_NOT_FOUND**: Indicates that the specified staff member was not found.
