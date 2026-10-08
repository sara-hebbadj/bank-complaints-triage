"""The fixed lists the whole system shares: 8 teams, 77 Banking77 intents mapped to a team, and reason codes.

These are business decisions, written as plain data so a reviewer can read and change them.
"""

from __future__ import annotations

TEAMS = {
    "cards": "Cards (delivery, activation, PIN, card not working, wallets)",
    "payments": "Payments (transfers, top-ups, receiving money)",
    "atm_cash": "ATM and cash (withdrawals, swallowed cards, ATM support)",
    "fees_fx": "Fees and exchange rates",
    "disputes": "Card disputes and chargebacks",
    "fraud_security": "Fraud and security (lost or stolen cards, unrecognised payments, scams)",
    "accounts_kyc": "Accounts and identity checks (KYC, personal details, closing accounts)",
    "customer_care": "Customer care: service complaints, vulnerable customers, anything unclear (human triage)",
}

# Every Banking77 intent belongs to exactly one team. "other" (not a Banking77 intent) -> customer care.
_TEAM_INTENTS = {
    "cards": [
        "activate_my_card", "apple_pay_or_google_pay", "card_about_to_expire", "card_acceptance", "card_arrival",
        "card_delivery_estimate", "card_linking", "card_not_working", "change_pin", "contactless_not_working",
        "declined_card_payment", "disposable_card_limits", "get_disposable_virtual_card", "get_physical_card",
        "getting_spare_card", "getting_virtual_card", "order_physical_card", "pending_card_payment", "pin_blocked",
        "reverted_card_payment?", "supported_cards_and_currencies", "virtual_card_not_working", "visa_or_mastercard",
    ],
    "payments": [
        "automatic_top_up", "balance_not_updated_after_bank_transfer",
        "balance_not_updated_after_cheque_or_cash_deposit", "beneficiary_not_allowed", "cancel_transfer",
        "declined_transfer", "failed_transfer", "pending_top_up", "pending_transfer", "receiving_money",
        "top_up_by_cash_or_cheque", "top_up_failed", "top_up_limits", "top_up_reverted", "topping_up_by_card",
        "transfer_into_account", "transfer_not_received_by_recipient", "transfer_timing", "verify_top_up",
    ],
    "atm_cash": ["atm_support", "card_swallowed", "declined_cash_withdrawal", "pending_cash_withdrawal"],
    "fees_fx": [
        "card_payment_fee_charged", "card_payment_wrong_exchange_rate", "cash_withdrawal_charge", "exchange_charge",
        "exchange_rate", "exchange_via_app", "extra_charge_on_statement", "fiat_currency_support",
        "top_up_by_bank_transfer_charge", "top_up_by_card_charge", "transfer_fee_charged",
        "wrong_exchange_rate_for_cash_withdrawal",
    ],
    "disputes": ["Refund_not_showing_up", "request_refund", "transaction_charged_twice",
                 "wrong_amount_of_cash_received"],
    "fraud_security": [
        "card_payment_not_recognised", "cash_withdrawal_not_recognised", "compromised_card",
        "direct_debit_payment_not_recognised", "lost_or_stolen_card", "lost_or_stolen_phone",
    ],
    "accounts_kyc": [
        "age_limit", "country_support", "edit_personal_details", "passcode_forgotten", "terminate_account",
        "unable_to_verify_identity", "verify_my_identity", "verify_source_of_funds", "why_verify_identity",
    ],
    "customer_care": [],
}
TEAM_OF_INTENT = {intent: team for team, intents in _TEAM_INTENTS.items() for intent in intents}
INTENTS = sorted(TEAM_OF_INTENT)  # the 77 Banking77 labels
OTHER = "other"


def team_for_intent(intent: str) -> str:
    return TEAM_OF_INTENT.get(intent, "customer_care")


def normalise_intent(label: str) -> str:
    """Map a model's spelling ('reverted card payment', 'refund_not_showing_up') to a Banking77 label."""
    key = "".join(ch for ch in str(label).lower() if ch.isalnum())
    for intent in INTENTS:
        if "".join(ch for ch in intent.lower() if ch.isalnum()) == key:
            return intent
    return OTHER


# Reason codes for acknowledgements. Each points to one clause of the (fictional) policy in data/policies/.
REASON_CODES = {
    "RC-DUP": ("5.2", "Card payment charged twice"),
    "RC-AMT": ("5.3", "Card payment charged at the wrong amount"),
    "RC-NRV": ("5.4", "Goods or service paid by card not received or not as described"),
    "RC-RFD": ("5.5", "Merchant refund or deposit release not received"),
    "RC-SUB": ("5.6", "Charged again after cancelling a recurring payment"),
    "RC-ATM": ("5.7", "ATM did not dispense the right amount, or a withdrawal is stuck"),
    "RC-LST": ("6.1", "Lost, stolen or compromised card, phone or account"),
    "RC-UNR": ("6.2", "Transaction the customer does not recognise"),
    "RC-PHI": ("6.3", "Phishing, scam call or fake message"),
    "RC-FEE": ("7.1", "Fee, charge or exchange-rate complaint"),
    "RC-PAY": ("8.1", "Transfer, top-up or direct debit failed, delayed or not received"),
    "RC-DLY": ("8.2", "Card delivery or replacement delay"),
    "RC-SVC": ("8.3", "Service quality: staff, branch, call centre or app"),
    "RC-ACC": ("8.4", "Account access, identity check or account closure problem"),
}
DISPUTE_REASONS = {  # extracted dispute reason -> reason code
    "charged_twice": "RC-DUP",
    "wrong_amount": "RC-AMT",
    "not_received": "RC-NRV",
    "refund_not_received": "RC-RFD",
    "cancelled_recurring": "RC-SUB",
    "atm_cash": "RC-ATM",
    "not_recognised": "RC-UNR",
}


def clause_for(code: str) -> str:
    return REASON_CODES[code][0] if code in REASON_CODES else ""
