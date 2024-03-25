# Django Appointment 📦: `date_time_ops.py`

This module contains various utility functions to assist in date and time-related operations in the Django appointment
system.

## Overview:

- [Module Metadata](#module-metadata)
- [Time Conversion](#time-conversion)
- [Date & Time Utilities](#date-time-utilities)
- [Weekday Operations](#weekday-operations)
- [General Utilities](#general-utilities)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.2.0

## Time Conversion:

- **convert_12_hour_time_to_24_hour_time**: Convert a 12-hour time format to a 24-hour time format.
- **convert_minutes_in_human_readable_format**: Convert minutes to a human-readable format.
- **convert_str_to_date**: Convert a string representation of a date to a Python `date` object.
- **convert_str_to_time**: Convert a string representation of time to a Python `time` object.

## Date Time Utilities:

- **get_ar_end_time**: Calculate the end time of an appointment request based on its start time and duration.
- **get_timestamp**: Obtain the current timestamp as a string without the decimal part.
- **time_difference**: Calculate the difference between two times.

## Weekday Operations:

- **get_weekday_num**: Determine the number associated with a given weekday name.

## General Utilities:

- **get_current_year**: Fetch the current year as an integer.
