"""The triage pipeline for one message: guard -> classify -> route -> extract -> match -> clock -> draft -> check.

Two modes share the same rules in code:
- mode "llm":     the LLM classifies, extracts dispute details and drafts the acknowledgement.
- mode "classic": TF-IDF (or embeddings) + keyword rules + regex extraction + a fixed template. No LLM.
  This is also the fallback when an LLM call fails.

Rules that never depend on a model: masking of card numbers and codes, fraud -> security team,
vulnerable customer -> human with priority, the complaint clock, the allowed reason codes and clauses,
and the final check that a draft asks for no secrets and promises no outcome.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime

from . import classic, extract, guards, prompts
from .config import CLASSIC_MIN_CONFIDENCE, PROMPT_VERSION, model_id
from .deadlines import complaint_clock
from .llm import parse_json
from .taxonomy import DISPUTE_REASONS, OTHER, REASON_CODES, clause_for, normalise_intent, team_for_intent
from .transactions import TransactionStore

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def input_hash(text: str) -> str:
    return hashlib.sha256(guards.normalise(text).strip().encode("utf-8")).hexdigest()


def route(intent: str, confidence: float, fraud: bool, vulnerable: bool, dispute: bool,
          min_confidence: float) -> tuple[str, str]:
    """(team, why). The order is a business rule: fraud first, then vulnerable customers, then card disputes,
    then the intent. (The dispute rule was added after the first baseline run, see README "What failed".)"""
    if fraud:
        return "fraud_security", "fraud rule"
    if vulnerable:
        return "customer_care", "vulnerable-customer rule"
    if dispute:
        return "disputes", "dispute rule"
    if intent == OTHER:
        return "customer_care", "no matching intent"
    if confidence < min_confidence:
        return "customer_care", "low confidence: human triage"
    return team_for_intent(intent), f"intent {intent}"


def rule_reason_code(case: dict, text: str) -> str:
    """Reason code chosen by keyword rules (the classic mode, and the fallback for an invalid LLM code)."""
    fields = case.get("dispute_fields") or {}
    if fields.get("dispute_reason") in DISPUTE_REASONS:
        return DISPUTE_REASONS[fields["dispute_reason"]]
    if case["fraud"]:
        if any(word in guards.normalise(text) for word in ("sms", "link", "email", "e-mail", "رابط", "رسالة", "lien")):
            return "RC-PHI"
        return "RC-UNR" if case["is_dispute"] else "RC-LST"
    return {"fees_fx": "RC-FEE", "payments": "RC-PAY", "accounts_kyc": "RC-ACC", "atm_cash": "RC-ATM",
            "disputes": "RC-AMT"}.get(case["team"], "RC-SVC")


TEMPLATE_DRAFT = {  # the safe fixed text (classic mode, model failure, or a draft blocked by the output check)
    "en": "Thank you for contacting Gulf Horizon Bank. We have received your message and passed it to the right "
          "team, who will review it.",
    "ar": "شكراً لتواصلك مع بنك الأفق الخليجي. استلمنا رسالتك وأحلناها إلى الفريق المختص لمراجعتها.",
    "fr": "Merci d'avoir contacté Gulf Horizon Bank. Nous avons bien reçu votre message et l'avons transmis à "
          "l'équipe concernée, qui va l'examiner.",
}
FOOTER = {
    "en": {"ref": "Reference: {case_id}. Reason code: {code} (Complaints Policy, clause {clause}).",
           "clock": "If you have not received a written reply by {ombudsman_date}, you may take your complaint to "
                    "Sanadak, the UAE financial ombudsman (sanadak.gov.ae).",
           "safe": "Gulf Horizon Bank will never ask for your PIN, OTP, CVV or password."},
    "ar": {"ref": "الرقم المرجعي: {case_id}. رمز السبب: {code} (سياسة الشكاوى، البند {clause}).",
           "clock": "إذا لم يصلك رد كتابي بحلول {ombudsman_date}، يمكنك رفع شكواك إلى \"سندك\"، أمين المظالم المالي "
                    "في دولة الإمارات (sanadak.gov.ae).",
           "safe": "لن يطلب منك بنك الأفق الخليجي أبداً الرقم السري أو رمز التحقق أو رمز CVV أو كلمة المرور."},
    "fr": {"ref": "Référence : {case_id}. Code motif : {code} (politique de réclamations, clause {clause}).",
           "clock": "Si vous n'avez pas reçu de réponse écrite d'ici le {ombudsman_date}, vous pourrez saisir "
                    "Sanadak, le médiateur financier des Émirats arabes unis (sanadak.gov.ae).",
           "safe": "Gulf Horizon Bank ne vous demandera jamais votre code PIN, votre code OTP, votre cryptogramme "
                   "ou votre mot de passe."},
}


def footer(case: dict) -> str:
    words = FOOTER[case["language"]]
    lines = [words["ref"].format(case_id=case["case_id"], code=case["reason_code"], clause=case["policy_clause"])]
    if case.get("clock"):
        lines.append(words["clock"].format(ombudsman_date=case["clock"]["ombudsman_date"]))
    lines.append(words["safe"])
    return "\n".join(lines)


class Triage:
    def __init__(self, mode: str = "llm", llm=None, intent_model=None, store: TransactionStore | None = None,
                 role: str = "cheap", draft_role: str | None = None):
        self.mode = mode
        self.llm = llm
        self.intent_model = intent_model  # classic classifier; also the fallback in llm mode
        self.store = store or TransactionStore()
        self.merchants = self.store.merchants()
        self.role, self.draft_role = role, draft_role or role

    # ---------- steps ----------
    def classify(self, text: str, events: list[str]) -> dict:
        if self.mode == "llm":
            try:
                result = self.llm.complete(
                    [{"role": "system", "content": prompts.TRIAGE_SYSTEM},
                     {"role": "user", "content": f"<customer_message>{prompts.as_data(text)}</customer_message>"}],
                    role=self.role, purpose="triage", max_tokens=1500)
                raw = parse_json(result.text)
                return {"intent": normalise_intent(raw.get("intent", OTHER)),
                        "confidence": float(raw.get("confidence") or 0),
                        "is_complaint": bool(raw.get("is_complaint")), "is_dispute": bool(raw.get("is_dispute")),
                        "fraud_signal": bool(raw.get("fraud_signal")),
                        "vulnerable_signal": bool(raw.get("vulnerable_signal")),
                        "injection_suspected": bool(raw.get("injection_suspected")),
                        "model": result.model, "min_confidence": 0.0}
            except Exception as error:  # the bank keeps working when the model is down
                events.append(f"triage model failed ({type(error).__name__}): used classic fallback")
        intent, confidence = (self.intent_model.predict([text])[0] if self.intent_model else (OTHER, 0.0))
        return {"intent": intent, "confidence": confidence, "is_complaint": classic.rule_complaint(text),
                "is_dispute": classic.rule_dispute(text), "fraud_signal": False, "vulnerable_signal": False,
                "injection_suspected": False, "model": getattr(self.intent_model, "name", "none"),
                "min_confidence": CLASSIC_MIN_CONFIDENCE}

    def extract(self, text: str, received: date, events: list[str]) -> dict:
        if self.mode == "llm":
            try:
                system = prompts.extract_system(received.isoformat(), WEEKDAYS[received.weekday()])
                result = self.llm.complete(
                    [{"role": "system", "content": system},
                     {"role": "user", "content": f"<customer_message>{prompts.as_data(text)}</customer_message>"}],
                    role=self.role, purpose="extract", max_tokens=1500)
                return extract.clean_llm_fields(parse_json(result.text))
            except Exception as error:
                events.append(f"extraction model failed ({type(error).__name__}): used regex fallback")
        return extract.rule_extract(text, received, self.merchants)

    def draft(self, case: dict, text: str, events: list[str]) -> tuple[str, str, str]:
        """(reason code, why, draft body). Template + rule code in classic mode or when the LLM fails."""
        if self.mode == "llm":
            try:
                system = prompts.DRAFT_SYSTEM.replace("LANGUAGE", prompts.LANGUAGE_NAMES[case["language"]])
                user = (f"<facts>{prompts.draft_facts(case)}</facts>\n"
                        f"<customer_message>{prompts.as_data(text)}</customer_message>")
                result = self.llm.complete([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                           role=self.draft_role, purpose="draft", max_tokens=1500, temperature=0.2)
                raw = parse_json(result.text)
                case["models"]["draft"] = result.model
                code = raw.get("reason_code")
                if code not in REASON_CODES:
                    events.append(f"invalid reason code from model ({code!r}): used rule code")
                    code = rule_reason_code(case, text)
                return code, str(raw.get("why", "")), str(raw.get("draft", "")).strip()
            except Exception as error:
                events.append(f"draft model failed ({type(error).__name__}): used template")
        code = rule_reason_code(case, text)
        return code, "rule-based reason code", TEMPLATE_DRAFT[case["language"]]

    # ---------- the whole pipeline ----------
    def process(self, message: dict, make_draft: bool | None = None) -> dict:
        """message: {"id", "text", "received_at", "customer_id", optional "language"} -> case dict."""
        events: list[str] = []
        masked, masked_items = guards.mask_sensitive(message["text"])  # nothing unmasked goes further
        if masked_items:
            events.append(f"masked before any model or log: {', '.join(sorted(set(masked_items)))}")
        received = datetime.fromisoformat(message["received_at"]).date()
        language = guards.detect_language(masked)
        rule_fraud, rule_vulnerable = guards.fraud_cues(masked), guards.vulnerable_cues(masked)
        rule_injection = guards.looks_like_injection(masked)

        labels = self.classify(masked, events)
        fraud = bool(rule_fraud) or labels["fraud_signal"]
        vulnerable = bool(rule_vulnerable) or labels["vulnerable_signal"]
        team, why = route(labels["intent"], labels["confidence"], fraud, vulnerable, labels["is_dispute"],
                          labels["min_confidence"])
        case = {
            "case_id": message.get("case_id") or message["id"], "item_id": message["id"],
            "customer_id": message.get("customer_id"), "received_at": message["received_at"],
            "language": language, "input_sha256": input_hash(message["text"]), "masked_text": masked,
            "intent": labels["intent"], "confidence": round(labels["confidence"], 3), "team": team, "route_why": why,
            "is_complaint": labels["is_complaint"] or labels["is_dispute"], "is_dispute": labels["is_dispute"],
            "fraud": fraud, "vulnerable": vulnerable, "injection": rule_injection or labels["injection_suspected"],
            "signals": {"rule_fraud": rule_fraud, "rule_vulnerable": rule_vulnerable, "rule_injection": rule_injection,
                        "llm": {k: labels[k] for k in ("fraud_signal", "vulnerable_signal", "injection_suspected")}
                        if self.mode == "llm" else None},
            "priority": "urgent" if fraud else "high" if vulnerable or rule_injection else "normal",
            "models": {"triage": labels["model"]}, "prompt_version": PROMPT_VERSION, "mode": self.mode,
            "dispute_fields": None, "matched_txn": None, "clock": None,
            "reason_code": None, "policy_clause": None, "draft": None, "draft_problems": [], "events": events,
        }
        if case["injection"]:  # the instructions are never followed; a person sees the warning in the console
            events.append("possible prompt injection: instructions inside the message were treated as data")
        if case["is_dispute"]:
            case["dispute_fields"] = self.extract(masked, received, events)
            if case["customer_id"]:
                case["matched_txn"] = self.store.match(case["customer_id"], case["dispute_fields"])
        if case["is_complaint"]:
            case["clock"] = complaint_clock(received)
        # By default only complaints and fraud reports get a drafted acknowledgement.
        should_draft = (case["is_complaint"] or case["fraud"]) if make_draft is None else make_draft
        if should_draft:
            self.add_draft(case, masked, events)
        return case

    def add_draft(self, case: dict, text: str, events: list[str]) -> None:
        code, why, body = self.draft(case, text, events)
        case["reason_code"], case["reason_why"], case["policy_clause"] = code, why, clause_for(code)
        case["raw_draft"] = body
        problems = [f"asks for secrets: {s}" for s in guards.asks_for_secrets(body)]
        problems += [f"promises an outcome: {p}" for p in guards.promises_outcome(body)]
        if problems:  # the code, not the model, has the last word
            events.append("draft blocked by output check: replaced with the safe template")
            body = TEMPLATE_DRAFT[case["language"]]
        case["draft_problems"] = problems
        case["draft"] = f"{body}\n\n{footer(case)}"


def model_ids() -> dict:
    return {role: model_id(role) for role in ("main", "cheap", "judge", "embed")}


def to_json(case: dict) -> str:
    return json.dumps(case, ensure_ascii=False, default=str)
