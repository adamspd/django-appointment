# cleanup_appointment_requests.py
# Path: appointment/management/commands/cleanup_appointment_requests.py

"""
Management command to manually run the cleanup_old_appointment_requests task.

Usage:
    python manage.py cleanup_appointment_requests
    python manage.py cleanup_appointment_requests --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from appointment.models import AppointmentRequest
from appointment.tasks import cleanup_old_appointment_requests
from appointment.settings import APPOINTMENT_CLEANUP_DAYS


class Command(BaseCommand):
    help = 'Manually run cleanup of old unassociated AppointmentRequests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Cleanup Appointment Requests'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=APPOINTMENT_CLEANUP_DAYS)
        self.stdout.write('\nCleanup Configuration:')
        self.stdout.write(f'  - Cleanup Days: {APPOINTMENT_CLEANUP_DAYS}')
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
        self.stdout.write(f'  - Cutoff Date: {cutoff_str}')

        # Count all appointment requests
        total_requests = AppointmentRequest.objects.count()
        msg = f'\nTotal AppointmentRequests in database: {total_requests}'
        self.stdout.write(msg)

        # Count requests with appointments
        requests_with_appointments = AppointmentRequest.objects.exclude(
            appointment__isnull=True
        ).count()
        msg = f'  - With associated Appointment: {requests_with_appointments}'
        self.stdout.write(msg)

        # Count requests without appointments
        requests_without_appointments = AppointmentRequest.objects.filter(
            appointment__isnull=True
        ).count()
        msg = (
            f'  - Without associated Appointment: '
            f'{requests_without_appointments}'
        )
        self.stdout.write(msg)

        # Find old unassociated requests
        old_unassociated = AppointmentRequest.objects.filter(
            created_at__lt=cutoff_date,
            appointment__isnull=True
        )
        count_to_delete = old_unassociated.count()

        msg = f'\nOld Unassociated Requests (to be cleaned): {count_to_delete}'
        self.stdout.write(msg)

        if count_to_delete > 0:
            self.stdout.write('\nDetails of requests that would be deleted:')
            for req in old_unassociated[:10]:  # Show first 10
                created_str = req.created_at.strftime("%Y-%m-%d %H:%M:%S")
                msg = (
                    f'  - ID: {req.id}, Created: {created_str}, '
                    f'Service: {req.service.name}, Date: {req.date}'
                )
                self.stdout.write(msg)
            if count_to_delete > 10:
                self.stdout.write(f'  ... and {count_to_delete - 10} more')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n[DRY RUN] No items were deleted.')
            )
            msg = 'Run without --dry-run to actually perform the cleanup.'
            self.stdout.write(msg)
        else:
            self.stdout.write('\nRunning cleanup task...')
            try:
                result = cleanup_old_appointment_requests()
                msg = '\n✓ Cleanup task completed successfully!'
                self.stdout.write(self.style.SUCCESS(msg))
                deleted = result["deleted_count"]
                msg = f'  - Deleted: {deleted} AppointmentRequest(s)'
                self.stdout.write(msg)
                self.stdout.write(f'  - Cutoff Date: {result["cutoff_date"]}')
            except Exception as e:
                msg = f'\n✗ Error during cleanup: {e}'
                self.stdout.write(self.style.ERROR(msg))
                raise

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
