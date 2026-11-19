## Migration Guide for Version 3.14.2 🚀

Version 3.14.2 is a security release. It does **not** change the database, the settings, the supported Python and
Django versions or the template context, so there is no migration to generate.

### Coming from 3.14.x

1. **Upgrade the package**:

    ```bash
    pip install django-appointment==3.14.2
    ```

2. **Check any custom code that moves appointments.** Only if you call the `update_appt_date_time` endpoint or the
   `save_appt_date_time` service yourself: a staff member can now only reschedule their own appointments. The endpoint
   returns a 403 for anyone else's, and the service raises `PermissionDenied`. Superusers are not affected.

### Coming from 3.13.x

Follow the [3.14.0 migration guide](v3_14_0.md) and install 3.14.2 instead of 3.14.0.

### Coming from 3.12 or older

Follow the [3.13.0 migration guide](v3_13_0.md) and install 3.14.2 instead of 3.13.0.

### Important Notes 📝:

- See the [release notes](../release_notes/latest.md) for what the fix changes.
- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
