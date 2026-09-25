from django.shortcuts import render

from appointment.models import Service


def home(request):
    """Demo project only: list the services so the booking pages are one click away."""
    return render(request, 'demo/home.html', {'services': Service.objects.all()})
