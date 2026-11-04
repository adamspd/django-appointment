import re
from datetime import datetime

from playwright.sync_api import expect

from appointment.models import Appointment


def open_booking_page(page, live_server, service, staff):
    with page.expect_response(
        lambda response: "/ajax/available_slots/" in response.url
    ):
        response = page.goto(
            f"{live_server.url}/en/request/{service.pk}/"
        )
        assert response is not None
        assert response.status == 200

    expect(page.locator("#staff_id")).to_have_value(str(staff.pk))
    expect(page.locator(".fc-daygrid-day").first).to_be_visible()


def select_slot(page, date, start_time, unavailable_start=None):
    date_iso = date.isoformat()

    # A date one week ahead can fall in the next month.
    day = page.locator(
        f'.fc-daygrid-day:not(.fc-day-other)[data-date="{date_iso}"]'
    )
    if day.count() == 0:
        page.locator(".fc-next-button").click()
    expect(day).to_be_visible()

    with page.expect_response(
        lambda response: (
            "/ajax/available_slots/" in response.url
            and f"selected_date={date_iso}" in response.url
        )
    ) as slots_response:
        day.click()

    assert slots_response.value.status == 200

    slot = page.locator(
        '.djangoAppt_appointment-slot'
        f'[data-timeslot^="{date_iso}T{start_time.isoformat()}"]'
    )
    expect(slot).to_be_visible()

    # Wait for the requested date's slots before checking the occupied one.
    if unavailable_start is not None:
        occupied_slot = page.locator(
            '.djangoAppt_appointment-slot'
            f'[data-timeslot^="{date_iso}T{unavailable_start.isoformat()}"]'
        )
        expect(occupied_slot).to_have_count(0)

    slot.click()
    page.get_by_role("button", name="Next", exact=True).click()


def test_new_client_can_book_appointment(
    page, live_server, booking_data, mailoutbox, django_user_model
):
    service = booking_data["service"]
    staff = booking_data["staff"]
    date = booking_data["date"]
    email = "new-client@example.com"

    expected_start = booking_data["start_time"]
    expected_end = (
        datetime.combine(date, expected_start) + service.duration
    ).time()

    assert not django_user_model.objects.filter(email=email).exists()

    open_booking_page(page, live_server, service, staff)
    select_slot(page, date, expected_start)

    page.get_by_label("Full Name").fill("Test Client")
    page.get_by_role(
        "textbox", name="Email *", exact=True
    ).fill(email)
    page.locator("#id_phone_0").select_option("US")
    page.locator("#id_phone_1").fill("2025550123")
    page.get_by_role("button", name="Finish", exact=True).click()

    expect(
        page.get_by_role("heading", name="Enter Verification Code")
    ).to_be_visible()

    # Read the code from the actual test email.
    verification_emails = [
        message
        for message in mailoutbox
        if email in message.to
        and message.subject == "Email Verification"
    ]
    assert len(verification_emails) == 1, (
        f"Expected 1 verification email, got {len(verification_emails)}"
    )

    match = re.search(
        r"Your verification code is ([A-Z0-9]{6})",
        verification_emails[0].body,
    )
    assert match is not None, "Verification code missing from email"

    page.get_by_label("Code", exact=True).fill(match.group(1))
    page.get_by_role("button", name="Submit", exact=True).click()

    expect(
        page.get_by_role("heading", name="See you soon!")
    ).to_be_visible()
    expect(
        page.locator(".appointment-details")
    ).to_contain_text(service.name)

    assert django_user_model.objects.filter(email=email).count() == 1
    assert Appointment.objects.count() == 1

    appointment = Appointment.objects.select_related(
        "client", "appointment_request"
    ).get()

    assert appointment.client.email == email
    assert appointment.client.get_full_name() == "Test Client"
    assert str(appointment.phone) == "+12025550123"

    appointment_request = appointment.appointment_request
    assert appointment_request.service_id == service.pk
    assert appointment_request.staff_member_id == staff.pk
    assert appointment_request.date == date
    assert appointment_request.start_time == expected_start
    assert appointment_request.end_time == expected_end


def test_authenticated_client_can_book_appointment(
    page,
    live_server,
    booking_data,
    authenticated_client,
    mailoutbox,
    django_user_model,
):
    service = booking_data["service"]
    staff = booking_data["staff"]
    date = booking_data["date"]
    user = authenticated_client["user"]
    previous_id = authenticated_client["previous_appointment"].pk

    previous_start = booking_data["start_time"]
    previous_end = (
        datetime.combine(date, previous_start) + service.duration
    ).time()
    previous_phone = "+12025550123"

    expected_start = authenticated_client["next_start"]
    expected_end = (
        datetime.combine(date, expected_start) + service.duration
    ).time()
    user_count_before = django_user_model.objects.count()

    assert not user.is_staff
    assert not user.is_superuser
    assert user.get_full_name() == "Returning Client"
    assert Appointment.objects.filter(client=user).count() == 1

    # Give the browser the authenticated Django session.
    page.context.add_cookies([
        {
            "name": authenticated_client["cookie_name"],
            "value": authenticated_client["cookie_value"],
            "url": live_server.url,
        }
    ])

    open_booking_page(page, live_server, service, staff)
    select_slot(
        page,
        date,
        expected_start,
        unavailable_start=previous_start,
    )

    # The form uses the existing client's identity.
    expect(page.get_by_label("Full Name")).to_have_value(
        "Returning Client"
    )
    expect(page.locator("#id_email")).to_have_count(0)
    expect(
        page.get_by_text(
            f"You're booking as {user.email}.", exact=True
        )
    ).to_be_visible()

    # A different phone number must belong only to the new appointment.
    page.locator("#id_phone_0").select_option("US")
    page.locator("#id_phone_1").fill("2025550124")
    page.get_by_role("button", name="Finish", exact=True).click()

    # Complete booking without entering a verification code.
    expect(
        page.get_by_role("heading", name="See you soon!")
    ).to_be_visible()
    expect(
        page.locator(".appointment-details")
    ).to_contain_text(service.name)

    verification_emails = [
        message
        for message in mailoutbox
        if user.email in message.to
        and message.subject == "Email Verification"
    ]
    assert verification_emails == []

    assert django_user_model.objects.count() == user_count_before
    assert django_user_model.objects.filter(email=user.email).count() == 1
    assert Appointment.objects.count() == 2
    assert Appointment.objects.filter(client=user).count() == 2

    appointment = Appointment.objects.select_related(
        "appointment_request"
    ).exclude(pk=previous_id).get()

    assert appointment.client_id == user.pk
    assert str(appointment.phone) == "+12025550124"

    appointment_request = appointment.appointment_request
    assert appointment_request.service_id == service.pk
    assert appointment_request.staff_member_id == staff.pk
    assert appointment_request.date == date
    assert appointment_request.start_time == expected_start
    assert appointment_request.end_time == expected_end

    # Re-read both objects to verify the original booking was preserved.
    previous = Appointment.objects.select_related(
        "appointment_request"
    ).get(pk=previous_id)

    assert previous.client_id == user.pk
    assert str(previous.phone) == previous_phone

    previous_request = previous.appointment_request
    assert previous_request.service_id == service.pk
    assert previous_request.staff_member_id == staff.pk
    assert previous_request.date == date
    assert previous_request.start_time == previous_start
    assert previous_request.end_time == previous_end