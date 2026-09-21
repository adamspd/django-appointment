# `date_time.py`

This module contains various utility functions to assist in date and time-related operations in the Django appointment
system.

## Overview:

- [Module Metadata](#module-metadata)
- [Time Conversion](#time-conversion)
- [JavaScript Display Formats](#javascript-display-formats)
- [Date & Time Utilities](#date-time-utilities)
- [Weekday Operations](#weekday-operations)
- [General Utilities](#general-utilities)

## Module Metadata:

**Author**: Adams Pierre David
**Since**: 1.2.0

## Time Conversion:

- **convert_12_hour_time_to_24_hour_time**: Convert a 12-hour time format to a 24-hour time format. *Deprecated since
  3.11.0, removed in 4.0.0 — times are now formatted through Django's localization framework.*
- **convert_24_hour_time_to_12_hour_time**: Convert a 24-hour time format to a 12-hour time format. *Deprecated since
  3.11.0, removed in 4.0.0 — times are now formatted through Django's localization framework.*
- **convert_minutes_in_human_readable_format**: Convert minutes to a human-readable format.
- **convert_str_to_date**: Convert a string representation of a date to a Python `date` object.
- **convert_str_to_time**: Convert a string representation of time to a Python `time` object.
- **convert_ap_str_time_to_12_hour_str_time**: Normalise an Associated Press style time — the shape Django's `P`
  time format produces in the `en` locale — into a plain 12-hour time. `10 a.m.` becomes `10:00 AM`, and the two
  special cases `noon` and `midnight` become `12:00 PM` and `12:00 AM`.

## JavaScript Display Formats:

The date and time pickers in the administration pages are Moment.js based, and Moment does not understand Django's
format characters. These two helpers translate the active locale's Django format into its Moment.js equivalent, so
the widget displays what the server is about to parse back. They are what fills `localized_formats` in the
[generic context](json_context.md), which the templates hand to the widgets.

- **js_timepicker_display_format**: Translate the locale's `TIME_FORMAT` into a Moment.js time format. Django's
  composite characters are expanded (`P` becomes `h:mm a`, `f` becomes `h:mm`), the single characters are mapped one
  for one (`g`→`h`, `G`→`H`, `h`→`hh`, `H`→`HH`, `i`→`mm`, `s`→`ss`), and anything else is passed through. The
  `fr_CA` format, which separates hours and minutes with a non-breaking space and a literal `h`, is special-cased to
  a plain `HH:mm` because Moment cannot use `h` as a separator.
- **js_datepicker_display_format**: Translate the locale's `DATE_FORMAT` into a Moment.js date format (`d`→`DD`,
  `j`→`D`, `D`→`ddd`, `l`→`dddd`, `m`→`MM`, `n`→`M`, `M`/`N`→`MMM`, `F`/`E`→`MMMM`, `y`→`YY`, `Y`→`YYYY`).
  Backslash-escaped characters in the Django format are kept literal, as Django itself treats them.

## Date Time Utilities:

- **combine_date_and_time**: Combine a `date` and a `time` into a single `datetime`.
- **get_ar_end_time**: Calculate the end time of an appointment request based on its start time and duration.
- **get_timestamp**: Obtain the current timestamp as a string without the decimal part.
- **time_difference**: Calculate the difference between two times.

## Weekday Operations:

- **get_weekday_num**: Determine the number associated with a given weekday name.

## General Utilities:

- **get_current_year**: Fetch the current year as an integer.

## Module Constants:

- **DATE_FORMATS**: Maps a language code to the Django date format string used to render a chosen date in that
  language. Adding a language here is all it takes to localise the date display — see the
  [internationalization guide](../internationalization.md).
