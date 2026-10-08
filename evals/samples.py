"""Fixed, reproducible subsets (seed 42) used by the evaluation.

- banking77_subset(): 10 test messages per intent = 770 (the LLM runs on these to cap cost; every model is
  compared on the same 770).
- complaint_relabel_candidates(): 100 of those 770 relabelled complaint / not complaint by hand
  (data/banking77_complaint_labels.csv): 4 from each of 15 complaint-prone intents + 2 from each of
  20 neutral intents.
"""

from __future__ import annotations

import random

from bank_triage.classic import load_banking77

PER_INTENT = 10
COMPLAINT_PRONE = [
    "transaction_charged_twice", "extra_charge_on_statement", "card_payment_fee_charged", "Refund_not_showing_up",
    "wrong_amount_of_cash_received", "card_arrival", "pending_transfer", "transfer_not_received_by_recipient",
    "declined_card_payment", "cash_withdrawal_charge", "card_payment_wrong_exchange_rate", "top_up_reverted",
    "failed_transfer", "balance_not_updated_after_bank_transfer", "card_payment_not_recognised",
]
NEUTRAL = [
    "activate_my_card", "age_limit", "apple_pay_or_google_pay", "atm_support", "change_pin", "country_support",
    "edit_personal_details", "exchange_rate", "fiat_currency_support", "get_physical_card", "getting_spare_card",
    "order_physical_card", "passcode_forgotten", "receiving_money", "supported_cards_and_currencies",
    "terminate_account", "top_up_limits", "transfer_timing", "verify_my_identity", "visa_or_mastercard",
]


def banking77_subset() -> list[dict]:
    texts, labels = load_banking77("test")
    rows = [{"id": f"B{i:04d}", "text": text, "intent": label}
            for i, (text, label) in enumerate(zip(texts, labels, strict=True))]
    rng = random.Random(42)
    picked = []
    for intent in sorted(set(labels)):
        group = [row for row in rows if row["intent"] == intent]
        picked += rng.sample(group, PER_INTENT)
    return sorted(picked, key=lambda row: row["id"])


def complaint_relabel_candidates() -> list[dict]:
    subset = banking77_subset()
    chosen = []
    for intents, per_intent in ((COMPLAINT_PRONE, 4), (NEUTRAL, 2)):
        for intent in intents:
            chosen += [row for row in subset if row["intent"] == intent][:per_intent]
    return chosen
