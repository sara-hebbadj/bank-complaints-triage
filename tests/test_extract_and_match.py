"""Regex extraction, cleaning of LLM fields, and matching a dispute to a transaction in DuckDB."""

import json
from datetime import date

from bank_triage import extract
from bank_triage.config import DATA_DIR


def test_rule_extraction_in_three_languages(store):
    merchants = store.merchants()
    received = date(2026, 10, 8)
    en = extract.rule_extract("I was charged twice at Zest Grocery on 2 October: AED 1,212.50. Card ending 4821.",
                              received, merchants)
    assert en == {"card_last4": "4821", "merchant": "Zest Grocery", "amount": 1212.5,
                  "transaction_date": "2026-10-02", "dispute_reason": "charged_twice"}
    ar = extract.rule_extract("انخصم مني ١٨٦٫٥٠ درهم مرتين في Oasis Fuel أمس", received, merchants)
    assert ar["amount"] == 186.5 and ar["transaction_date"] == "2026-10-07" and ar["merchant"] == "Oasis Fuel"
    fr = extract.rule_extract("Souk Online a prélevé 1 755,20 AED le 10/09/2026 pour un service jamais fourni.",
                              received, merchants)
    assert fr["amount"] == 1755.2 and fr["transaction_date"] == "2026-09-10" and fr["dispute_reason"] == "not_received"


def test_clean_llm_fields_rejects_bad_values():
    cleaned = extract.clean_llm_fields({"card_last4": "card 48", "amount": "1,050", "transaction_date": "2 Oct",
                                        "dispute_reason": "angry", "merchant": " Zest "})
    assert cleaned == {"card_last4": None, "merchant": "Zest", "amount": 1050.0, "transaction_date": None,
                       "dispute_reason": None}


def test_merchant_similarity_ignores_case_and_accents():
    assert extract.merchant_similarity("DESERT BLOOM CAFE", "Desert Bloom Café") == 1.0
    assert extract.merchant_similarity("Pharmacy", "Al Noor Pharmacy") == 1.0
    assert extract.merchant_similarity("ديزرت بلوم", "Desert Bloom Café") == 0.0


def test_every_templated_dispute_matches_its_transaction(store):
    disputes = [json.loads(line) for line in (DATA_DIR / "disputes.jsonl").read_text(encoding="utf-8").splitlines()]
    for dispute in disputes[:12]:
        gold = dispute["gold"]
        match = store.match(dispute["customer_id"], gold)
        assert match and match["txn_id"] in gold["txn_ids"], dispute["id"]


def test_a_wrong_last4_does_not_hide_the_transaction(store):
    dispute = json.loads((DATA_DIR / "disputes.jsonl").read_text(encoding="utf-8").splitlines()[0])
    fields = {**dispute["gold"], "card_last4": "0000"}
    assert store.match(dispute["customer_id"], fields)["txn_id"] in dispute["gold"]["txn_ids"]


def test_no_match_without_enough_evidence(store):
    assert store.match("C001", {"merchant": "Nowhere Shop", "amount": 0.01, "transaction_date": None}) is None
