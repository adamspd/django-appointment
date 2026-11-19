## Migration Guide for Version 3.14.0 🚀

Version 3.14.0 adds Brazilian Portuguese. It does **not** change the database, the settings, the supported Python and
Django versions or the template context, so there is no migration to generate.

### Coming from 3.13.x

1. **Upgrade the package**:

    ```bash
    pip install django-appointment==3.14.0
    ```

2. **Optional:** to offer Brazilian Portuguese, add it to your `LANGUAGES` setting:

    ```python
    LANGUAGES = [
        ('en', 'English'),
        ('pt-br', 'Brazilian Portuguese'),
    ]
    ```

### Coming from 3.12 or older

Follow the [3.13.0 migration guide](v3_13_0.md) and install 3.14.0 instead of 3.13.0.

### Important Notes 📝:

- See the [release notes](../release_notes/latest.md) for what is new.
- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
