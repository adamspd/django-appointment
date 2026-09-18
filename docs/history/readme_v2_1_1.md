# This is the documentation for Django Appointment version 2.1.1 📦

⚠️ **IMPORTANT**: If upgrading from a version before 2.0.0, please note significant database changes were introduced in
Version 2.0.0 introduces significant database changes. Please read
the [migration guide](../migration_guides/latest.md) before
updating.

Detailed documentation can be found in
the [docs' directory](../project-structure.md).
For changes and migration information, please refer to the [release
notes](../release_notes/v2_1_1.md).

## Added Features in version 2.0.0

- **Database Changes ⚠️**: Significant modifications to the database schema. Before updating, ensure you follow the
  migration steps outlined in
  the [migration guide](../migration_guides/v2_1_0.md).

1. Introduced a staff feature allowing staff members in a team or system to manage their own appointments.
2. Implemented an admin feature panel enabling staff members and superusers (admins) to manage the system.
3. Added buffer time between the current time and the first available slot for the day.
4. Defined working hours for each staff member, along with the specific days they are available during the week.
5. Specified days off for staff members to represent holidays or vacations.
6. Staff members can now define their own configuration settings for the appointment system, such as slot duration,
   working hours, and buffer time between appointments. However, only admins have the privilege to add/remove services.

### Breaking Changes in version 2.1.1:

- None

### New Features 🆕

See the [release notes](../release_notes/v2_1_1.md#updates)
for more information.

### Fixes 🆕

See the [release notes](../release_notes/v2_1_1.md#bug-fixes)
for more information.
