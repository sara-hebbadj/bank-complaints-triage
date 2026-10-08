"""The complaint clock. Plain date arithmetic in code, never left to a model.

For a complaint received on day D:
- acknowledgement due: D + ACK_BUSINESS_DAYS business days (fictional bank target);
- internal escalation: D + ESCALATION_BUSINESS_DAYS business days if still open (fictional bank target);
- ombudsman date: D + 15 calendar days. From then on, if the bank has sent no written reply, the customer
  may take the complaint to Sanadak, the UAE financial ombudsman (sanadak.gov.ae, "resolution process").

Business days skip the weekend (Saturday and Sunday) and the holiday list in config.py. A message that
arrives on a weekend or holiday is treated as received on the next business day for business-day targets;
the 15 calendar days always count from the real receipt date (the customer-friendly reading).
"""

from __future__ import annotations

from datetime import date, timedelta

from .config import (
    ACK_BUSINESS_DAYS,
    DISPUTE_WINDOW_DAYS,
    ESCALATION_BUSINESS_DAYS,
    HOLIDAYS_2026,
    OMBUDSMAN_CALENDAR_DAYS,
    WEEKEND,
)


def is_business_day(day: date, holidays: set[date] = HOLIDAYS_2026) -> bool:
    return day.weekday() not in WEEKEND and day not in holidays


def add_business_days(start: date, days: int, holidays: set[date] = HOLIDAYS_2026) -> date:
    """The date `days` business days after `start` (start itself is day 0)."""
    current = start
    while not is_business_day(current, holidays):  # weekend/holiday receipt: the clock starts next business day
        current += timedelta(days=1)
    added = 0
    while added < days:
        current += timedelta(days=1)
        if is_business_day(current, holidays):
            added += 1
    return current


def complaint_clock(received: date, holidays: set[date] = HOLIDAYS_2026) -> dict:
    """The three dates the agent console shows for every complaint."""
    return {
        "received": received.isoformat(),
        "ack_due": add_business_days(received, ACK_BUSINESS_DAYS, holidays).isoformat(),
        "escalate_on": add_business_days(received, ESCALATION_BUSINESS_DAYS, holidays).isoformat(),
        "ombudsman_date": (received + timedelta(days=OMBUDSMAN_CALENDAR_DAYS)).isoformat(),
    }


def clock_status(clock: dict, today: date, acknowledged: bool = False, replied: bool = False) -> dict:
    """What the console should warn about today: overdue acknowledgement, escalation, ombudsman exposure."""
    ack_due = date.fromisoformat(clock["ack_due"])
    escalate_on = date.fromisoformat(clock["escalate_on"])
    ombudsman = date.fromisoformat(clock["ombudsman_date"])
    return {
        "ack_overdue": not acknowledged and today > ack_due,
        "needs_escalation": not replied and today >= escalate_on,
        "ombudsman_open": not replied and today >= ombudsman,  # the customer may now go to Sanadak
        "days_to_ombudsman": (ombudsman - today).days,
    }


def dispute_in_window(transaction_date: date, received: date) -> bool:
    """Fictional bank rule: card disputes are accepted up to DISPUTE_WINDOW_DAYS after the transaction."""
    return 0 <= (received - transaction_date).days <= DISPUTE_WINDOW_DAYS
