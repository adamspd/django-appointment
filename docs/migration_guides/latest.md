## Migration Guide for Version 3.13.0 🚀

Version 3.13.0 does **not** change the database: no model, field or constraint is added, renamed or removed, so there
is no migration to generate. It raises the minimum Python and Pillow versions. Check those first.

### Before you start: supported versions

| Declared in `setup.cfg` | 3.12.0 | 3.13.0 |
|---|---|---|
| `python_requires` | `>=3.10` | **`>=3.11`** |
| Django | `>=4.2,<7.0` | `>=4.2,<7.0` |
| `Pillow` | `>=10.4,<13.0` | **`>=13.0,<14.0`** |
| Tested combinations | Python 3.10 – 3.14, Django 4.2 – 6.1 | **Python 3.11 – 3.14, Django 4.2 – 6.1** |

Python 3.10 is no longer accepted. `pip` will refuse to install 3.13.0 on it rather than installing something
broken, so if you are still on 3.10, stay on 3.12.0 until you can upgrade the interpreter. Pillow 13 fixes several
security vulnerabilities and does not support Python 3.10, so upgrading the interpreter is the only way to get those
fixes.

The [compatibility matrix](../compatibility.md) has the full grid of tested Python and Django combinations.

### Steps for Upgrading to Version 3.13.0:

1. **Check your Python version**:
    - Run `python --version` in the environment that serves your site. It must be 3.11 or newer. If you build a
      Docker image, check the base image too (`python:3.10-slim` has to move to 3.11 or newer).

2. **Check your Pillow pin**:
    - If your own requirements pin Pillow (`Pillow==12.3.0`, `Pillow<13`), raise it to `13.0` or newer, or remove it
      and let `pip` pick the version. Otherwise `pip` will report a conflict.

3. **Backup Your Database**:
    - As a best practice, always back up your current database before an upgrade, even one without migrations.

4. **Update Package**:
    - Upgrade to the latest version by running:
      ```bash
      pip install --upgrade django-appointment
      ```
    - Confirm Pillow was upgraded:
      ```bash
      python -c "import PIL; print(PIL.__version__)"
      ```
      It should print `13.0.0` or newer.

5. **Check there is nothing to migrate**:
    - The package does not ship migration files, so confirm your own ones are up to date:
      ```bash
      python manage.py makemigrations appointment --check --dry-run
      ```
    - It should report "No changes detected". If it proposes changes, they come from an earlier upgrade you have not
      migrated yet, not from 3.13.0: read that version's migration guide first.

6. **Review and Test**:
    - Add or edit a service with an image, then book an appointment from start to finish.
    - If your own code uses Pillow too, check it against Pillow 13: see
      [Pillow's 13.0.0 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html) for what
      changed.

### Troubleshooting:

- **`pip` says the package requires a different Python**:
    - Your environment runs Python 3.10 or older. Upgrade the interpreter (step 1), or stay on 3.12.0 for now.
- **`pip` reports a conflict on Pillow**:
    - Something in your requirements pins Pillow below 13.0 (step 2).
- **Issues Post Upgrade**:
    - Consult the [release notes](../release_notes/latest.md) for the details of each change, and check the Django
      logs for error messages.

### Important Notes 📝:

- As with any upgrade, testing in a development or staging environment before applying changes to your production
  environment is highly recommended.
- Upgrading from 3.11 or older? Read the [3.12 migration guide](v3_12_0.md) first: that release changed how the
  pages and emails are built.
- Upgrading from the 3.10 series or older? Read the [3.11 migration guide](v3_11_0.md) too: that release added a
  model, so it needs a migration.
