## Migration Guide for Version 2.1.0 🚀

Version 2.1.0 introduces significant changes to the database schema. Before upgrading, please review the changes below
and follow the recommended steps to ensure a smooth migration.

### Changes in Version 2.1.0:

1. **New Fields**:
    - A non-nullable `staff_member` field has been added to the `appointmentrequest` model.
    - The `created_at` and `updated_at` fields have been added to the `config` model.
    - A `background_color` field has been added to the `service` model.

2. **Field Modifications**:
    - The `phone` field in the `appointment` model has been modified to be non-nullable.

3. **New Models**:
    - Three new models have been introduced: `StaffMember`, `DayOff`, and `WorkingHours`.

### Recommended Migration Steps:

1. **Backup**: Before attempting to migrate, make sure to backup your current database. This will allow you to restore
   the previous state in case anything goes wrong.

2. **Review New Fields**:
    - Ensure that there are no rows in the `appointmentrequest` table with a NULL `staff_member`.
    - Ensure that the `phone` field in all rows of the `appointment` table is not NULL. If there are any, you may need
      to manually update them or set a default value.

3. **Run Migrations**:
    - After reviewing and making necessary data adjustments, run the migrations using the
      command: `python manage.py migrate appointment`.

4. **Post-Migration Checks**:
    - Verify that all new fields and models have been correctly added to the database.
    - Check the application functionality related to the modified models to ensure data integrity and correct behavior.

### If You Mistakenly Upgraded Without Preparations:

1. **Restore Backup**: If you have a backup of your database, restore it to revert to the previous state before the
   migration attempt.

2. **Manual Field Adjustments**: If you don't have a backup:
    - When prompted about the `staff_member` field, you can set a default value by selecting option 1 and
      inputting `None`.
    - For the `created_at` and `updated_at` fields, set the default value to `timezone.now`.
    - For the `phone` field in the `appointment` model, set a default value by selecting option 1 and inputting an empty
      string `""`.

3. **Retry Migration**: After making the necessary adjustments, you can then attempt the migration again using the
   command: `python manage.py migrate appointment`.

### Important Notes 📝:

- The migration process described above has the potential to disrupt your application if not executed correctly. Ensure
  thorough testing before deploying these changes to a live environment.

- Make sure to read the error messages during migration. They provide valuable insights into potential issues and how to
  address them.
