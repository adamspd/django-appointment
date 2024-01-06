# Django Appointment 📦: `json_and_context_ops.py`

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
    - Retrieves the generic context for the admin pages.

- **get_generic_context_with_extra(request, extra, admin=True)**:
    - Retrieves the generic context for the admin pages with additional context information.

### Unauthorized Responses:

- **handle_unauthorized_response(request, message, response_type)**:
    - Handles unauthorized responses based on the specified response type (JSON or HTML).
