"""Dispute details: a regex extractor (baseline), cleaning of the LLM's JSON, and field scoring helpers.

Fields: card_last4, merchant, amount (AED, as charged), transaction_date (ISO), dispute_reason.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from .guards import ARABIC_DIGITS, normalise
from .taxonomy import DISPUTE_REASONS

MONTHS = {  # month words in English, French and Arabic, all normalised (no accents, no hamza)
    **{name: number for number, name in enumerate(
        ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
         "november", "december"], 1)},
    **{name: number for number, name in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)},
    **{name: number for number, name in enumerate(
        ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre",
         "novembre", "decembre"], 1)},
    **{normalise(name): number for number, name in enumerate(
        ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر",
         "ديسمبر"], 1)},
}
YESTERDAY = ["yesterday", "hier", normalise("أمس"), normalise("امبارح"), normalise("البارحة")]

REASON_RULES = [  # checked in this order; first match wins
    ("cancelled_recurring", ["cancel", "ألغيت", "ملغي", "الإلغاء", "resilie", "resiliation", "abonnement"]),
    ("charged_twice", ["twice", "two times", "double", "مرتين", "deux fois", "doublon"]),
    ("not_recognised", ["recognise", "recognize", "never made", "wasn't me", "unknown", "لا أعرف", "ما سويت",
                        "غير معروف", "لست أنا", "ne reconnais pas", "jamais faite", "inconnu", "pas moi"]),
    ("not_received", ["never arrived", "nothing delivered", "never provided", "not delivered", "لم يصل الطلب",
                      "ما وصلني", "لم يقدموها", "jamais arrivee", "rien de livre", "jamais fourni"]),
    ("wrong_amount", ["instead of", "only", "agreed to pay", "wrong amount", "بدلا", "المفروض", "الفاتورة",
                      "اتفقت", "au lieu de", "n'etait que", "accepte de payer", "mauvais montant"]),
    ("refund_not_received", ["refund", "استرداد", "يرجعون", "rembours"]),
    ("atm_cash", ["atm", "cash machine", "الصراف", "distributeur"]),
]


def rule_reason(text: str) -> str | None:
    lowered = normalise(text)
    for reason, cues in REASON_RULES:
        if any(normalise(cue) in lowered for cue in cues):
            return reason
    return None


AMOUNT_RE = re.compile(
    r"(?:aed|dhs|dirhams?|درهم\w*)\s*(\d[\d ,.٫]*\d|\d)|(\d[\d ,.٫]*\d|\d)\s*(?:aed|dhs|dirhams?|درهم\w*)")


def parse_number(raw: str, french: bool) -> float | None:
    raw = raw.translate(ARABIC_DIGITS).replace("٫", ".").replace(" ", " ").strip()
    if french:
        raw = raw.replace(" ", "").replace(",", ".")
    else:
        raw = raw.replace(",", "").replace(" ", "")
    try:
        return float(raw)
    except ValueError:
        return None


def rule_amount(text: str) -> float | None:
    """The first amount next to a currency word (the charged amount comes first in most messages)."""
    lowered = normalise(text)
    match = AMOUNT_RE.search(lowered)
    if not match:
        return None
    french = bool(re.search(r"\d,\d{2}\b", match.group(0))) or " " in (match.group(1) or match.group(2)).strip()
    return parse_number(match.group(1) or match.group(2), french)


def rule_last4(text: str) -> str | None:
    lowered = normalise(text)
    match = re.search(r"(?:ends? in|ending(?: in)?|\.\.\.|finissant par|se termine par|تنتهي ب\w*|بالرقم)\s*(\d{4})\b",
                      lowered)
    return match.group(1) if match else None


def rule_date(text: str, received: date) -> str | None:
    lowered = normalise(text)
    if any(word in lowered for word in YESTERDAY):
        return (received - timedelta(days=1)).isoformat()
    day = month = None
    year = received.year
    if found := re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b", lowered):  # 02/10/2026 or 2/10 (day first)
        day, month = int(found.group(1)), int(found.group(2))
        year = int(found.group(3) or year)
    for found in re.finditer(r"\b(\d{1,2})\s+([^\W\d_]+)", lowered):  # 2 October / 2 octobre / 2 أكتوبر
        if month is None and found.group(2) in MONTHS:
            day, month = int(found.group(1)), MONTHS[found.group(2)]
    for found in re.finditer(r"\b([a-z]{3,9})\.? (\d{1,2})\b", lowered):  # Oct 2
        if month is None and found.group(1) in MONTHS:
            day, month = int(found.group(2)), MONTHS[found.group(1)]
    if month is None:
        return None
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def rule_merchant(text: str, known_merchants: list[str]) -> str | None:
    """The longest known merchant name (from the transactions table) that appears in the message."""
    lowered = normalise(text)
    hits = [name for name in known_merchants if normalise(name) in lowered]
    return max(hits, key=len) if hits else None


def rule_extract(text: str, received: date, known_merchants: list[str]) -> dict:
    return {"card_last4": rule_last4(text), "merchant": rule_merchant(text, known_merchants),
            "amount": rule_amount(text), "transaction_date": rule_date(text, received),
            "dispute_reason": rule_reason(text)}


def clean_llm_fields(raw: dict) -> dict:
    """Make the LLM's JSON safe and comparable: 4-digit last4, float amount, ISO date, known reason."""
    last4 = re.sub(r"\D", "", str(raw.get("card_last4") or "").translate(ARABIC_DIGITS))
    amount = raw.get("amount")
    try:
        amount = float(str(amount).translate(ARABIC_DIGITS).replace(",", "")) if amount is not None else None
    except ValueError:
        amount = None
    when = str(raw.get("transaction_date") or "")
    reason = raw.get("dispute_reason")
    return {"card_last4": last4 if len(last4) == 4 else None,
            "merchant": (str(raw["merchant"]).strip() or None) if raw.get("merchant") else None,
            "amount": amount,
            "transaction_date": when if re.fullmatch(r"\d{4}-\d{2}-\d{2}", when) else None,
            "dispute_reason": reason if reason in DISPUTE_REASONS else None}


def merchant_similarity(a: str | None, b: str | None) -> float:
    """Share of the shorter name's words found in the other name (0 to 1), ignoring case, accents and symbols."""
    if not a or not b:
        return 0.0
    words_a = set(re.findall(r"[^\W_]+", normalise(a)))
    words_b = set(re.findall(r"[^\W_]+", normalise(b)))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / min(len(words_a), len(words_b))


def field_correct(field: str, predicted, gold) -> bool:
    if field == "amount":
        return (predicted is None and gold is None) or (
            predicted is not None and gold is not None and abs(float(predicted) - float(gold)) < 0.01)
    if field == "merchant":
        return merchant_similarity(predicted, gold) >= 0.5
    return predicted == gold
