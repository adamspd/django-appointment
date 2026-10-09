import os
from datetime import datetime, time, timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from appointment.models import (
    Appointment,
    AppointmentRequest,
    Service,
    StaffMember,
    WorkingHours,
)


@pytest.fixture(scope="session", autouse=True)
def allow_sync_django_in_e2e():
    # Enable synchronous ORM calls for this E2E test session.
    previous = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
        else:
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = previous


@pytest.fixture(autouse=True)
def configure_e2e(settings, monkeypatch):
    settings.USE_DJANGO_Q_FOR_EMAILS = False

    # The email helper checks EMAIL_HOST directly in os.environ.
    monkeypatch.setenv("EMAIL_HOST", "localhost")

    cache.clear()
    try:
        yield
    finally:
        cache.clear()


@pytest.fixture
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "timezone_id": "UTC",
        "locale": "en-US",
    }


@pytest.fixture
def booking_data(transactional_db, django_user_model):
    # Book at the start of the staff member's working day.
    start_time = time(9, 0)
    finish_time = time(18, 0)

    service = Service.objects.create(
        name="Test Cleaning",
        duration=timedelta(hours=1),
        price=0,
    )

    staff_user = django_user_model.objects.create_user(
        username="test_staff",
        email="staff@example.com",
        first_name="Test",
        last_name="Staff",
    )

    staff = StaffMember.objects.create(
        user=staff_user,
        lead_time=start_time,
        finish_time=finish_time,
        slot_duration=30,
        appointment_buffer_time=0,
        work_on_saturday=True,
        work_on_sunday=True,
    )
    staff.services_offered.add(service)

    for day in range(7):
        WorkingHours.objects.create(
            staff_member=staff,
            day_of_week=day,
            start_time=start_time,
            end_time=finish_time,
        )

    return {
        "service": service,
        "staff": staff,
        "date": timezone.localdate() + timedelta(days=7),
        "start_time": start_time,
    }


@pytest.fixture
def authenticated_client(booking_data, django_user_model, client, settings):
    user = django_user_model.objects.create_user(
        username="returning_client",
        email="returning-client@example.com",
        first_name="Returning",
        last_name="Client",
    )

    service = booking_data["service"]
    date = booking_data["date"]
    start_time = booking_data["start_time"]
    end_time = (
        datetime.combine(date, start_time) + service.duration
    ).time()

    # An existing appointment occupies the first slot.
    previous_request = AppointmentRequest.objects.create(
        service=service,
        staff_member=booking_data["staff"],
        date=date,
        start_time=start_time,
        end_time=end_time,
    )
    previous_appointment = Appointment.objects.create(
        client=user,
        appointment_request=previous_request,
        phone="+12025550123",
    )

    # Prepare authentication without testing a separate login flow.
    client.force_login(user)

    return {
        "user": user,
        "previous_appointment": previous_appointment,
        "next_start": end_time,
        "cookie_name": settings.SESSION_COOKIE_NAME,
        "cookie_value": client.cookies[settings.SESSION_COOKIE_NAME].value,
    }