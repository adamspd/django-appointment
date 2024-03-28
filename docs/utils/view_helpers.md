# Django Appointment 📦: `views_utils.py`

This module provides utility functions to support the Django views in the appointment system.

## Overview:

- [Module Metadata](#module-metadata)
- [Functions](#functions)
    - [Locale Operations](#locale-operations)
    - [Request Type Checks](#request-type-checks)
    - [Random ID Generation](#random-id-generation)
    - [Timezone Operations](#timezone-operations)

## Module Metadata:

**Author**: Adams Pierre David  
**Since**: 1.2.0

## Functions:

### Locale Operations:

- **get_locale()**:
    - Returns the current locale based on the user's language settings. This function is primarily used in the
      JavaScript files.

### Request Type Checks:

- **is_ajax(request)**:
    - Determines whether the incoming request is an AJAX request.

### Random ID Generation:

- **generate_random_id()**:
    - Produces a random UUID in the form of a hexadecimal string.
