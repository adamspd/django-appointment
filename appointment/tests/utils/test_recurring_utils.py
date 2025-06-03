import datetime
from django.test import TestCase
from django.utils import timezone
from recurrence import Recurrence, Rule, DAILY, WEEKLY

from appointment.utils.recurring_utils import generate_recurring_occurrences

class TestGenerateRecurringOccurrences(TestCase):

    def test_generate_daily_occurrences_with_end_date(self):
        initial_start_naive = datetime.datetime(2024, 7, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        rule = Rule(freq=DAILY)
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        end_recurrence_naive = datetime.datetime(2024, 7, 3, 10, 0, 0)
        # For get_occurrences, dtend is exclusive for the next potential start.
        # So to include July 3, dtend should be July 3, 23:59:59 or July 4, 00:00:00
        # Or, if end_recurrence_datetime is the exact time of the last desired occurrence,
        # the logic in generate_recurring_occurrences should handle it.
        # The current implementation of generate_recurring_occurrences passes end_recurrence_datetime directly.
        # Recurrence.get_occurrences(dtstart, dtend) will include occurrences >= dtstart and <= dtend.
        end_recurrence_datetime = timezone.make_aware(end_recurrence_naive)

        service_duration = datetime.timedelta(hours=1)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            end_recurrence_datetime,
            service_duration
        )

        self.assertEqual(len(occurrences), 3) # July 1, July 2, July 3

        expected_dates = [
            (datetime.date(2024, 7, 1), datetime.time(10, 0, 0), datetime.time(11, 0, 0)),
            (datetime.date(2024, 7, 2), datetime.time(10, 0, 0), datetime.time(11, 0, 0)),
            (datetime.date(2024, 7, 3), datetime.time(10, 0, 0), datetime.time(11, 0, 0)),
        ]

        for i, occ in enumerate(occurrences):
            self.assertEqual(occ['date'], expected_dates[i][0])
            self.assertEqual(occ['start_time'], expected_dates[i][1])
            self.assertEqual(occ['end_time'], expected_dates[i][2])

    def test_generate_weekly_occurrences_with_count(self):
        initial_start_naive = datetime.datetime(2024, 7, 1, 14, 0, 0) # A Monday
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        rule = Rule(freq=WEEKLY, count=3)
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        service_duration = datetime.timedelta(minutes=30)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            service_duration=service_duration
        )

        self.assertEqual(len(occurrences), 3)

        expected_start_datetimes = [
            initial_start_datetime,
            initial_start_datetime + datetime.timedelta(weeks=1),
            initial_start_datetime + datetime.timedelta(weeks=2),
        ]

        for i, occ in enumerate(occurrences):
            expected_dt = expected_start_datetimes[i]
            self.assertEqual(occ['date'], expected_dt.date())
            self.assertEqual(occ['start_time'], expected_dt.time())
            self.assertEqual(occ['end_time'], (expected_dt + service_duration).time())

    def test_no_service_duration_raises_value_error(self):
        initial_start_naive = datetime.datetime(2024, 7, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)
        rule = Rule(freq=DAILY)
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        with self.assertRaises(ValueError) as context:
            generate_recurring_occurrences(
                initial_start_datetime,
                recurrence_rule,
                service_duration=None
            )
        self.assertTrue("service_duration must be provided" in str(context.exception))

    def test_no_end_date_or_count_defaults_to_one_year_limit(self):
        initial_start_naive = datetime.datetime(2024, 1, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        rule = Rule(freq=DAILY)
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        service_duration = datetime.timedelta(hours=1)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            end_recurrence_datetime=None,
            service_duration=service_duration
        )

        # Year 2024 is a leap year. dtend becomes initial_start_datetime + 365 days = 2025-01-01 10:00:00
        # get_occurrences(dtstart, dtend) includes dtstart and occurrences strictly before dtend if dtend is a specific time.
        # If dtend is 2025-01-01 10:00:00, the last occurrence will be on 2024-12-31 10:00:00.
        # This means 366 days for a leap year.
        expected_occurrences = 366
        if not (initial_start_datetime.year % 4 == 0 and (initial_start_datetime.year % 100 != 0 or initial_start_datetime.year % 400 == 0)):
            expected_occurrences = 365

        self.assertEqual(len(occurrences), expected_occurrences)

        self.assertEqual(occurrences[0]['date'], datetime.date(2024, 1, 1))
        self.assertEqual(occurrences[0]['start_time'], datetime.time(10, 0, 0))

        last_expected_date = initial_start_datetime.date() + datetime.timedelta(days=expected_occurrences - 1)
        self.assertEqual(occurrences[-1]['date'], last_expected_date)
        self.assertEqual(occurrences[-1]['start_time'], datetime.time(10, 0, 0))

    def test_rule_with_until_overrides_default_year_limit(self):
        initial_start_naive = datetime.datetime(2024, 1, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        until_date_naive = datetime.datetime(2024, 1, 5, 10, 0, 0) # End of Jan 5th
        until_date_aware = timezone.make_aware(until_date_naive)

        rule = Rule(freq=DAILY, until=until_date_aware)
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        service_duration = datetime.timedelta(hours=1)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            end_recurrence_datetime=None,
            service_duration=service_duration
        )

        # Jan 1, Jan 2, Jan 3, Jan 4, Jan 5. Total 5.
        self.assertEqual(len(occurrences), 5)
        self.assertEqual(occurrences[0]['date'], datetime.date(2024, 1, 1))
        self.assertEqual(occurrences[-1]['date'], datetime.date(2024, 1, 5))

    def test_end_recurrence_datetime_limits_before_rule_until(self):
        initial_start_naive = datetime.datetime(2024, 7, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        until_date_naive = datetime.datetime(2024, 7, 5, 10, 0, 0)
        until_date_aware = timezone.make_aware(until_date_naive)
        rule = Rule(freq=DAILY, until=until_date_aware) # Rule allows up to July 5
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        # Explicitly end earlier via end_recurrence_datetime argument
        end_recurrence_arg_naive = datetime.datetime(2024, 7, 3, 10, 0, 0)
        end_recurrence_arg_aware = timezone.make_aware(end_recurrence_arg_naive)

        service_duration = datetime.timedelta(hours=1)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            end_recurrence_arg_aware,
            service_duration
        )

        self.assertEqual(len(occurrences), 3) # July 1, July 2, July 3
        self.assertEqual(occurrences[-1]['date'], datetime.date(2024, 7, 3))

    def test_end_recurrence_datetime_limits_before_rule_count(self):
        initial_start_naive = datetime.datetime(2024, 7, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        rule = Rule(freq=DAILY, count=5) # Rule allows 5 occurrences
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        end_recurrence_arg_naive = datetime.datetime(2024, 7, 3, 10, 0, 0)
        end_recurrence_arg_aware = timezone.make_aware(end_recurrence_arg_naive)

        service_duration = datetime.timedelta(hours=1)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            end_recurrence_arg_aware,
            service_duration
        )

        self.assertEqual(len(occurrences), 3) # July 1, July 2, July 3
        self.assertEqual(occurrences[-1]['date'], datetime.date(2024, 7, 3))


    def test_rule_count_limits_before_end_recurrence_datetime(self):
        initial_start_naive = datetime.datetime(2024, 7, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        rule = Rule(freq=DAILY, count=3) # Rule allows 3 occurrences
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        # end_recurrence_datetime argument would allow more, but rule's count is stricter
        end_recurrence_arg_naive = datetime.datetime(2024, 7, 5, 10, 0, 0)
        end_recurrence_arg_aware = timezone.make_aware(end_recurrence_arg_naive)

        service_duration = datetime.timedelta(hours=1)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            end_recurrence_arg_aware,
            service_duration
        )

        self.assertEqual(len(occurrences), 3) # Limited by count=3
        self.assertEqual(occurrences[-1]['date'], datetime.date(2024, 7, 3))

    def test_rule_until_limits_before_end_recurrence_datetime(self):
        initial_start_naive = datetime.datetime(2024, 7, 1, 10, 0, 0)
        initial_start_datetime = timezone.make_aware(initial_start_naive)

        until_date_naive = datetime.datetime(2024, 7, 3, 10, 0, 0)
        until_date_aware = timezone.make_aware(until_date_naive)
        rule = Rule(freq=DAILY, until=until_date_aware) # Rule allows up to July 3
        recurrence_rule = Recurrence(dtstart=initial_start_datetime, rules=[rule])

        # end_recurrence_datetime argument would allow more, but rule's UNTIL is stricter
        end_recurrence_arg_naive = datetime.datetime(2024, 7, 5, 10, 0, 0)
        end_recurrence_arg_aware = timezone.make_aware(end_recurrence_arg_naive)

        service_duration = datetime.timedelta(hours=1)

        occurrences = generate_recurring_occurrences(
            initial_start_datetime,
            recurrence_rule,
            end_recurrence_arg_aware,
            service_duration
        )

        self.assertEqual(len(occurrences), 3) # Limited by UNTIL July 3
        self.assertEqual(occurrences[-1]['date'], datetime.date(2024, 7, 3))
