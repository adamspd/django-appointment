import datetime
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model

from appointment.models import Service, StaffMember, WorkingHours

class Command(BaseCommand):
    help = "Load salon configuration from data/salon.json"

    def handle(self, *args, **options):
        salon_file = settings.BASE_DIR / "data" / "salon.json"

        with salon_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        salon = data["salon"]
        services = data["services"]
        staff = data["staff"]

        manager = data["manager"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded configuration for {salon['name']}"
            )
        )

        self.stdout.write(
            f"{len(services)} services and {len(staff)} staff members found."
        )

        for service_data in services:
            duration = datetime.timedelta(
                minutes=service_data["duration_minutes"]
            )

            service, created = Service.objects.update_or_create(
                name=service_data["name"],
                defaults={
                    "description": service_data["description"],
                    "duration": duration,
                    "price": service_data["price"],
                    "currency": service_data["currency"],
                },
            )

            action = "Created" if created else "Updated"

            self.stdout.write(
                f"{action}: {service.name}"
            )


        User = get_user_model()

        manager_user, manager_created = User.objects.update_or_create(
            username=manager["username"],
            defaults={
                "first_name": manager["first_name"],
                "last_name": manager["last_name"],
                "email": manager["email"],
                "is_staff": True,
                "is_superuser": True,
            },
        )

        manager_user.set_password(manager["password"])
        manager_user.save()

        manager_action = "Created" if manager_created else "Updated"

        self.stdout.write(
            f"{manager_action} manager: "
            f"{manager['first_name']} {manager['last_name']}"
        )

        service_map = {}

        for service_data in services:
            service = Service.objects.get(
                name=service_data["name"]
            )

            service_map[service_data["id"]] = service
        
        
        for staff_data in staff:
            user, user_created = User.objects.update_or_create(
                username=staff_data["username"],
                defaults={
                    "first_name": staff_data["first_name"],
                    "last_name": staff_data["last_name"],
                    "email": staff_data["email"],
                    "is_staff": True,
                },
            )

            user.set_password(salon["demo_staff_password"])
            user.save()

            staff_member, staff_created = StaffMember.objects.get_or_create(
                user=user
            )

            offered_services = [
                service_map[service_id]
                for service_id in staff_data["services"]
            ]

            staff_member.services_offered.set(offered_services)

            WorkingHours.objects.filter(
                staff_member=staff_member
            ).exclude(
                day_of_week__in=staff_data["working_days"]
            ).delete()            

            for day in staff_data["working_days"]:
                WorkingHours.objects.update_or_create(
                    staff_member=staff_member,
                    day_of_week=day,
                    defaults={
                        "start_time": staff_data["start_time"],
                        "end_time": staff_data["end_time"],
                    },
                )
            action = "Created" if staff_created else "Updated"

            self.stdout.write(
                f"{action} staff member: "
                f"{staff_data['first_name']} {staff_data['last_name']}"
            )