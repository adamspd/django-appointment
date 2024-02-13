# permissions.py
# Path: appointment/utils/permissions.py

"""
Author: Adams Pierre David
Since: 2.0.0
"""


def check_entity_ownership(user, entity):
    """Check if a user owns an entity."""
    return entity.is_owner(user.pk) or user.is_superuser


def check_extensive_permissions(staff_user_id, user, entity):
    """Check if a user has permissions to make changes based on staff_user_id and entity ownership."""
    if (staff_user_id and int(staff_user_id) == user.pk) or user.is_superuser:
        if entity:
            return check_entity_ownership(user, entity)
        else:
            return True
    return False


def check_permissions(staff_user_id, user):
    """Check if a user has permissions to add based on staff_user_id."""
    if (staff_user_id and int(staff_user_id) == user.pk) or user.is_superuser:
        return True
    return False


def has_permission_to_delete_appointment(user, appointment):
    """
    Check if the user has permission to delete the given appointment.
    Returns True if the user has permission, False otherwise.
    """
    return check_extensive_permissions(appointment.get_staff_member().user_id, user, appointment)
