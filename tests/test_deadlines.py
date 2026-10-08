"""The complaint clock: business days, weekends, holidays and the 15-calendar-day ombudsman date."""

from datetime import date

from bank_triage.deadlines import (
    add_business_days,
    clock_status,
    complaint_clock,
    dispute_in_window,
    is_business_day,
)

NO_HOLIDAYS: set[date] = set()


def test_weekend_is_saturday_and_sunday():
    assert not is_business_day(date(2026, 10, 3), NO_HOLIDAYS)  # Saturday
    assert not is_business_day(date(2026, 10, 4), NO_HOLIDAYS)  # Sunday
    assert is_business_day(date(2026, 10, 2), NO_HOLIDAYS)  # Friday is a working day in the UAE since 2022


def test_two_business_days_from_a_wednesday():
    assert add_business_days(date(2026, 10, 7), 2, NO_HOLIDAYS) == date(2026, 10, 9)  # Wed -> Fri


def test_business_days_skip_the_weekend():
    assert add_business_days(date(2026, 10, 8), 2, NO_HOLIDAYS) == date(2026, 10, 12)  # Thu -> Mon


def test_weekend_receipt_starts_the_clock_on_monday():
    assert add_business_days(date(2026, 10, 3), 2, NO_HOLIDAYS) == date(2026, 10, 7)  # Sat -> Mon is day 0


def test_holidays_are_skipped():
    holidays = {date(2026, 10, 9)}
    assert add_business_days(date(2026, 10, 7), 2, holidays) == date(2026, 10, 12)


def test_national_day_holidays_in_the_default_list():
    # 1, 2 and 3 December 2026 are holidays (Tue-Thu): Mon 30 Nov + 2 business days = Fri 4 Dec, then Mon 7 Dec
    assert add_business_days(date(2026, 11, 30), 2) == date(2026, 12, 7)


def test_ombudsman_date_is_15_calendar_days_even_on_a_weekend():
    clock = complaint_clock(date(2026, 10, 3), NO_HOLIDAYS)  # Saturday
    assert clock["ombudsman_date"] == "2026-10-18"
    assert clock["ack_due"] == "2026-10-07"
    assert clock["escalate_on"] == "2026-10-12"


def test_clock_status_flags():
    clock = complaint_clock(date(2026, 10, 1), NO_HOLIDAYS)
    status = clock_status(clock, date(2026, 10, 6))
    assert status["ack_overdue"] and not status["needs_escalation"] and not status["ombudsman_open"]
    late = clock_status(clock, date(2026, 10, 16))
    assert late["needs_escalation"] and late["ombudsman_open"] and late["days_to_ombudsman"] == 0
    assert not clock_status(clock, date(2026, 10, 16), acknowledged=True, replied=True)["ombudsman_open"]


def test_dispute_window_is_120_days():
    assert dispute_in_window(date(2026, 6, 10), date(2026, 10, 8))
    assert not dispute_in_window(date(2026, 6, 9), date(2026, 10, 8))
    assert not dispute_in_window(date(2026, 10, 9), date(2026, 10, 8))  # a future date is not valid
