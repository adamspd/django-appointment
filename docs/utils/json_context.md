# `json_context.py`

This module provides utility functions to handle JSON operations and context-related operations for the Django
appointment system.

## Overview:

- [Module Metadata](#module-metadata)
- [Functions](#functions)
    - [JSON Operations](#json-operations)
    - [Context Operations](#context-operations)
    - [Unauthorized Responses](#unauthorized-responses)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.2.0

## Functions:

### JSON Operations:

- **convert_appointment_to_json(request, appointments: list) -> list**:
    - Converts a queryset of Appointment objects to a JSON serializable format.

- **json_response(message, status=200, success=True, custom_data=None, error_code=None, **kwargs)**:
    - Returns a generic JSON response.

### Context Operations:

- **get_generic_context(request, admin=True)**:
    - Retrieves the generic context every rendered page receives: `BASE_TEMPLATE`, `user`, `is_superuser`, `locale`
      and `localized_formats`.
    - `BASE_TEMPLATE` is `APPOINTMENT_ADMIN_BASE_TEMPLATE` when `admin` is true and `APPOINTMENT_BASE_TEMPLATE`
      otherwise, which is how the client-facing pages and the administration pages can extend different bases.
    - `locale` is the active language stripped of its region (`fr-FR` becomes `fr`), because that is the form
      FullCalendar expects.
    - `localized_formats` is a dictionary the date and time pickers need, holding Django's `TIME_INPUT_FORMATS`,
      `DATE_INPUT_FORMATS` and `DATETIME_INPUT_FORMATS` for the active locale, plus `js_timepicker_display_format`
      and `js_datepicker_display_format` — the same formats translated into their Moment.js equivalents, built by
      [`date_time.py`](date_time.md).

- **get_generic_context_with_extra(request, extra, admin=True)**:
    - Retrieves the generic context for the admin pages with additional context information.

### Unauthorized Responses:

- **handle_unauthorized_response(request, message, response_type)**:
    - Handles unauthorized responses based on the specified response type (JSON or HTML).
