# `template_helpers.py`

This module resolves which template to render: the user's override when there is a usable one, the packaged default
otherwise. See [Custom templates](../custom-templates.md) for the list of names you can override.

## Module Metadata:

**Author**: Adams Pierre David

## Functions:

- **get_custom_template(template_name, default_template)**:
    - Looks for `template_name` inside the directory named by `APPOINTMENT_CUSTOM_TEMPLATES_DIR` (default `custom`)
      and returns its path, falling back to `default_template`.
    - `template_name` may also be an iterable of accepted names, tried in order — this is how a template that is
      documented under more than one name is resolved.

- **get_email_template(template_name, default_template)**:
    - The same lookup, against the directory named by `APPOINTMENT_CUSTOM_EMAILS_DIR` (default `emails`).
    - Some callers pass `None` as `default_template`, which is how the emails that fall back to plain text signal
      that no HTML template is available.

## Fallback behaviour

A candidate is skipped and the next one tried when it does not exist, or when it exists but fails to compile — an
unclosed `{% if %}`, an unknown tag, a bad `{% load %}`. Compile failures are logged as a warning naming the
template, so a silently ignored override is visible in the logs. Errors that only surface while the page is being
rendered cannot be caught here and will still propagate.
