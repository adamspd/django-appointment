from datetime import date, timedelta

import pytest
from django.utils import timezone
from playwright.sync_api import expect

from appointment.models import WorkingHours

WEEKEND = {5, 6}  # Python weekday(): Saturday and Sunday


@pytest.fixture
def weekday_staff(booking_data):
    # The staff member works Monday to Friday only.
    staff = booking_data["staff"]
    WorkingHours.objects.filter(
        staff_member=staff, day_of_week__in=[0, 6]
    ).delete()
    staff.work_on_saturday = False
    staff.work_on_sunday = False
    staff.save()
    return booking_data


# The server uses UTC. Browsers west and east of it used to see the
# working days moved by one day (issue #352).
@pytest.mark.parametrize(
    "browser_timezone",
    ["America/New_York", "Australia/Sydney"],
)
def test_calendar_shows_working_days_in_any_browser_timezone(
    browser, live_server, weekday_staff, browser_timezone
):
    context = browser.new_context(timezone_id=browser_timezone, locale="en-US")
    page = context.new_page()
    service = weekday_staff["service"]

    try:
        with page.expect_response(
            lambda response: "/ajax/available_slots/" in response.url
        ):
            page.goto(f"{live_server.url}/en/request/{service.pk}/")
        expect(page.locator(".disabled-day").first).to_be_visible()
        # The browser's clock differs from the server's (UTC), so the page says so
        expect(page.locator("#djappt-tz-notice")).to_be_visible()

        cells = page.locator(".fc-daygrid-day")
        for i in range(cells.count()):
            cell = cells.nth(i)
            day = date.fromisoformat(cell.get_attribute("data-date"))
            classes = cell.get_attribute("class").split()
            assert ("disabled-day" in classes) == (day.weekday() in WEEKEND), (
                f"{day:%A %Y-%m-%d} has classes {classes}"
            )

        # Clicking a working day asks for that same date.
        target = timezone.localdate() + timedelta(days=2)
        while target.weekday() in WEEKEND:
            target += timedelta(days=1)
        cell = page.locator(
            f'.fc-daygrid-day:not(.fc-day-other)[data-date="{target}"]'
        )
        if cell.count() == 0:
            page.locator(".fc-next-button").click()

        with page.expect_response(
            lambda response: (
                "/ajax/available_slots/" in response.url
                and f"selected_date={target}" in response.url
            )
        ) as slots_response:
            cell.click()
        assert slots_response.value.status == 200

        # Picking a slot shows it in the browser's time too
        page.locator(
            f'.djangoAppt_appointment-slot[data-timeslot^="{target}T09:00"]'
        ).click()
        expect(page.locator("#djappt-local-time")).to_be_visible()
    finally:
        context.close()


def test_no_time_zone_notice_when_the_clocks_match(page, live_server, weekday_staff):
    # The default browser context uses UTC, like the server.
    service = weekday_staff["service"]
    with page.expect_response(
        lambda response: "/ajax/available_slots/" in response.url
    ):
        page.goto(f"{live_server.url}/en/request/{service.pk}/")
    expect(page.locator(".disabled-day").first).to_be_visible()
    expect(page.locator("#djappt-tz-notice")).to_be_hidden()
    expect(page.locator("#djappt-local-time")).to_be_hidden()
