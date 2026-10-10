# Booking browser tests

These tests use Pytest, pytest-django and Playwright with Chromium.

## Covered scenarios

- A new client books an appointment, verifies their email and receives
  confirmation. The test checks the created account and saved appointment.
- An authenticated non-staff client with an existing appointment books
  another slot without email verification. The test checks that the
  occupied slot is unavailable, no additional account is created, and
  the original appointment and its phone number are preserved.

Not covered by these browser tests: invalid verification codes, invalid
form input, booking with an existing email without authentication,
password setup, rescheduling and cancellation.

## Setup

Run commands from the repository root in an activated virtual environment.

The library supports Python 3.10 with compatible Django versions.
The commands below use the current requirements.txt.
Use Python 3.12 or newer for this setup.

Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-e2e.txt
```

Install Chromium on macOS:

```bash
python -m playwright install chromium
```

On Linux or in CI, install Chromium and its system dependencies:

```bash
python -m playwright install --with-deps chromium
```

## Run

Run both tests without opening a browser window:

```bash
python -m pytest e2e/test_booking.py -v
```

Show the browser:

```bash
python -m pytest e2e/test_booking.py -v --headed
```

Slow down browser actions for inspection:

```bash
python -m pytest e2e/test_booking.py -v --headed --slowmo=500
```

## Test isolation

pytest-django starts a live server using a separate test database.
The fixtures create the services, staff, working hours and client data.
There is no need to start runserver or prepare records manually.

Emails are captured in memory, and asynchronous email sending is disabled.
SMTP credentials and a running Django Q worker are not required.

The browser timezone and locale are fixed to UTC and en-US.

## Current limitation

Playwright's synchronous API runs an event loop in the test thread.
Django's synchronous database operations can therefore raise
SynchronousOnlyOperation during database setup and ORM checks.

The E2E fixture sets DJANGO_ALLOW_ASYNC_UNSAFE to disable this check
for the whole pytest session and restores its previous value afterward.

Run these E2E tests in their own pytest invocation, separately from other
tests. Do not enable this setting in application or production configuration.