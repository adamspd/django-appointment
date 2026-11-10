## Migration Guide for Version 3.13.1 🚀

Version 3.13.1 is a bug fix release for 3.13.0. It does **not** change the database, the settings, the supported
Python and Django versions or the template context, so there is no migration to generate.

### Coming from 3.13.0

1. **Upgrade the package**:

    ```bash
    pip install django-appointment==3.13.1
    ```

2. **Collect the static files**, since the fix is in the package's JavaScript and CSS:

    ```bash
    python manage.py collectstatic
    ```

3. **Only if you override `administration/staff_index.html`:** remove `position: absolute` (and `z-index`) from the
   inline `style` of `#customContextMenu`, keeping `display: none`. The package CSS now positions the menu; an inline
   `position: absolute` would keep it opening away from the cursor on some layouts.

### Coming from 3.12 or older

Follow the [3.13.0 migration guide](v3_13_0.md) and install 3.13.1 instead of 3.13.0. Step 3 above applies too if you
override the staff calendar page.

### Important Notes 📝:

- See the [release notes](../release_notes/latest.md) for what the fix changes.
- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
