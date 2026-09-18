# compat.py
# Path: appointment/compat.py

"""
Compatibility helpers for the range of Django versions this package supports.

Author: Adams Pierre David
Since: 3.11.0
"""

import django
from django.db import models

# CheckConstraint's `check` argument was renamed to `condition` in Django 5.1 and removed in Django 6.0.
CHECK_CONSTRAINT_CONDITION_KWARG = 'condition' if django.VERSION >= (5, 1) else 'check'


def check_constraint(*, condition, name, **kwargs):
    """Build a CheckConstraint using whichever keyword the running Django version accepts.

    :param: condition (Q): The condition the rows must satisfy.
    :param: name (str): The name of the constraint.
    :return: models.CheckConstraint
    """
    return models.CheckConstraint(**{CHECK_CONSTRAINT_CONDITION_KWARG: condition}, name=name, **kwargs)
