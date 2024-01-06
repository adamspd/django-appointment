# Django Appointment 📦: `permissions_handler.py`

This module provides utility functions to handle user permissions and ownership checks for the Django appointment system.

## Overview:

- [Module Metadata](#module-metadata)
- [Functions](#functions)
  - [Ownership Checks](#ownership-checks)
  - [Permission Checks](#permission-checks)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.2.0

## Functions:

### Ownership Checks:

- **check_entity_ownership(user, entity)**:
  - Checks if a user owns a particular entity or if the user has superuser privileges.

### Permission Checks:

- **check_extensive_permissions(staff_user_id, user, entity)**:
  - Determines if a user has permissions to make changes based on the provided staff_user_id and entity ownership.

- **check_permissions(staff_user_id, user)**:
  - Determines if a user has permissions to add based on the provided staff_user_id.
