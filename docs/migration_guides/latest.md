## Migration Guide for the 3.10 series 🚀

Version 3.10 adds four new model fields, so unlike 3.0.1 this upgrade **does** require a migration. No existing field
changes meaning, and no data is rewritten — every new field has a default that preserves the previous behaviour for
existing rows.

### Steps for Upgrading to Version 3.10.x:

1. **Backup Your Database**:
    - As a best practice, always back up your current database before performing an upgrade. This precaution ensures
      you can restore your application to its previous state if needed.

2. **Update Package**:
    - Upgrade to the latest version by running:
      ```bash
      pip install --upgrade django-appointment
      ```

3. **Run Migrations**:
    - This package intentionally does not ship migration files, so generate them against your own project first:
      ```bash
      python manage.py makemigrations appointment
      python manage.py migrate
      ```
    - The new fields are:

      | Model         | Field                        | Default | Effect                                             |
      |---------------|------------------------------|---------|----------------------------------------------------|
      | `Config`      | `default_to_service_duration` | `True`  | Availability accounts for each service's duration  |
      | `Config`      | `slot_gap_time`              | `NULL`  | No rest time enforced between appointments         |
      | `Service`     | `use_service_duration_as_slot` | `True` | Per-service fallback when the Config flag is off   |
      | `StaffMember` | `slot_gap_time`              | `NULL`  | Falls back to the Config value                     |

4. **Review your slot availability**:
    - `default_to_service_duration` defaults to `True`, which means services longer than your configured slot
      duration will now correctly reserve the time they need. If you were relying on the previous behaviour — where a
      long service only blocked one slot — your availability will legitimately look tighter after upgrading. Set the
      flag to `False` in the Config model to opt back out per service.

5. **Review and Test**:
    - After upgrading, thoroughly test your application to ensure all functionalities are working as expected with
      the new version.
    - Pay particular attention to appointment booking, since that is where the slot changes are visible.

### Optional follow-ups

- **Cleanup task**: if `django_q` is in your `INSTALLED_APPS`, a daily cleanup of abandoned appointment requests is
  now scheduled automatically the first time the app starts. Set `APPOINTMENT_CLEANUP_DAYS` if 7 days is not the
  retention you want, and run `python manage.py cleanup_appointment_requests --dry-run` first if you'd like to see
  what it would remove.
- **Custom templates**: nothing to do unless you want them. If you had previously forked a template, you can now
  override it by name instead — see [Custom templates](../custom-templates.md).

### Troubleshooting:

- **Issues Post Migration**:
    - If you encounter issues after migration, consult the [release notes](../release_notes/latest.md) for the
      specific updates that might affect your setup.
    - Check the Django logs for any error messages that can provide insights into issues.

### Important Notes 📝:

- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
- Upgrading from a version before 2.0.0? Read the [2.1.0 migration guide](v2_1_0.md) first — that release did change
  the schema significantly.
