from datetime import datetime, timedelta


def generate_recurring_occurrences(initial_start_datetime, recurrence_rule, end_recurrence_datetime=None, service_duration=None):
    """
    Generates a list of occurrence dictionaries for a recurring appointment.

    :param initial_start_datetime: datetime object for the first occurrence.
    :param recurrence_rule: recurrence.fields.Recurrence object.
    :param end_recurrence_datetime: Optional datetime object to limit occurrences.
    :param service_duration: Optional timedelta object for the service duration.
    :return: List of dictionaries, each with 'date', 'start_time', and 'end_time'.
    """
    if not service_duration:
        # For now, let's raise an error. Logging a warning might also be an option.
        raise ValueError("service_duration must be provided to calculate end times for occurrences.")

    dtstart = initial_start_datetime

    # Determine dtend for fetching occurrences
    # If recurrence_rule has an UNTIL or COUNT, django-recurrence handles it.
    # If not, and end_recurrence_datetime is not provided, we need a sensible limit.
    # For now, if end_recurrence_datetime is None, we'll rely on the rule's own limits (if any)
    # or fetch up to a default future period if the rule is truly infinite.
    # This part might need refinement based on how django-recurrence handles infinite rules
    # without an explicit dtend in get_occurrences.

    # A practical approach for truly infinite rules without end_recurrence_datetime:
    # limit to a certain number of occurrences or a certain period.
    # For this initial implementation, we'll use end_recurrence_datetime if provided.
    # If recurrence_rule has no UNTIL or COUNT, and end_recurrence_datetime is None,
    # django-recurrence might return occurrences indefinitely or up to a certain internal limit.
    # It's safer to provide an explicit dtend for such cases.

    dtend = end_recurrence_datetime

    if not dtend and not recurrence_rule.until and not recurrence_rule.count:
        # Default to 1 year ahead if no end_recurrence_datetime and rule is potentially infinite
        # This is a sensible default to prevent fetching too many occurrences.
        # Alternatively, one could raise an error or limit by a number of occurrences.
        dtend = dtstart + timedelta(days=365)
        # Or, if django-recurrence handles its own default for truly infinite rules well,
        # dtend could remain None. Testing this behavior with the library is key.
        # For now, explicit dtend is safer.

    try:
        occurrences_datetimes = recurrence_rule.get_occurrences(dtstart, dtend)
    except Exception as e:
        # Log this error appropriately in a real application
        print(f"Error getting occurrences: {e}")
        return []

    formatted_occurrences = []
    for occ_datetime in occurrences_datetimes:
        if not isinstance(occ_datetime, datetime):
            # Ensure we are working with datetime objects
            # This can happen if get_occurrences returns date objects for all-day events,
            # but our initial_start_datetime implies specific times.
            # For now, assuming get_occurrences returns datetimes as per typical usage.
            print(f"Warning: Expected datetime object, got {type(occ_datetime)}. Skipping.")
            continue

        calculated_end_datetime = occ_datetime + service_duration
        formatted_occurrences.append({
            'date': occ_datetime.date(),
            'start_time': occ_datetime.time(),
            'end_time': calculated_end_datetime.time(),
        })

    return formatted_occurrences
