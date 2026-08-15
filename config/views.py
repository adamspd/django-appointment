import json

from django.conf import settings
from django.shortcuts import render

from appointment.models import Service


def home(request):
    salon_file = settings.BASE_DIR / "data" / "salon.json"

    with salon_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    salon = data["salon"]
    services = Service.objects.all()

    context = {
        "salon": salon,
        "services": services,
    }

    return render(request, "home.html", context)