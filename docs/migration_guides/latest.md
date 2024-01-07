## Migration Guide for Version 3.0.1 🚀

Version 3.x.x of django-appointment is focused on enhancing functionality, documentation, and internationalization, with
no significant database schema changes introduced. This guide provides the steps to ensure a smooth upgrade from version
2.1.1 or any earlier versions post 2.0.0.

### Steps for Upgrading to Version 3.0.1:

1. **Backup Your Database**:
    - As a best practice, always back up your current database before performing an upgrade. This precaution ensures you
      can restore your application to its previous state if needed.

2. **Update Package**:
    - Upgrade to the latest version by running:
      ```bash
      pip install django-appointment==3.0.1
      ```

3. **Run Migrations** (if any):
    - Although no new migrations are expected for this release, it's always a good idea to run:
      ```bash
      python manage.py makemigrations
      python manage.py migrate
      ```
    - This ensures your database schema is up-to-date with the latest package version.

4. **Review and Test**:
    - After upgrading, thoroughly test your application to ensure all functionalities are working as expected with the
      new version.
    - Pay special attention to features affected by the updates in version 3.x.x, as detailed in the release notes.

### Troubleshooting:

- **Issues Post Migration**:
    - If you encounter issues after migration, consult the release notes for version 3.0.1 for specific updates that
      might affect your setup.
    - Check the Django logs for any error messages that can provide insights into issues.

### Important Notes 📝:

- No database schema changes were introduced in version 3.0.1, so the migration process should be straightforward.
- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
