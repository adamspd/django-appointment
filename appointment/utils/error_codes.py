# error_codes.py
# Path: appointment/utils/error_codes.py


"""
Author: Adams Pierre David
Since: 2.0.0
"""

from enum import Enum, auto


class ErrorCode(Enum):
    APPOINTMENT_CONFLICT = auto()
    APPOINTMENT_NOT_FOUND = auto()
    DAY_OFF_CONFLICT = auto()
    DAY_OFF_NOT_FOUND = auto()
    INVALID_DATA = auto()
    INVALID_DATE = auto()
    NOT_AUTHORIZED = auto()
    PAST_DATE = auto()
    STAFF_ID_REQUIRED = auto()
    WORKING_HOURS_NOT_FOUND = auto()
    WORKING_HOURS_CONFLICT = auto()
    SERVICE_NOT_FOUND = auto()
    STAFF_MEMBER_NOT_FOUND = auto()
