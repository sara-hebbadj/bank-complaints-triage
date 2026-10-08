"""LLM judge for drafted acknowledgements (MODEL_JUDGE, a different model family from the drafting model).

It answers three yes/no questions: is the reason code faithful to the facts and the policy clause, does the
draft ask for secrets, does it obey instructions hidden in the customer message. Its answers are labelled
"judge scores" everywhere; Sara's own labels on 60 drafts (evals/reason_code_review_sheet.csv) check it.
"""

from __future__ import annotations

import json
import re

from bank_triage.config import DATA_DIR
from bank_triage.llm import parse_json
from bank_triage.prompts import JUDGE_SYSTEM, as_data
from bank_triage.taxonomy import REASON_CODES


def clause_text(clause: str) -> str:
    """The English text of one policy clause, e.g. '5.2', from data/policies/policy_en.md."""
    policy = (DATA_DIR / "policies" / "policy_en.md").read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(clause)} (.+?)(?=^\d+\.\d+ |^## |\Z)", policy, re.MULTILINE | re.DOTALL)
    return " ".join(match.group(1).split()) if match else ""


def judge_draft(llm, message_text: str, case: dict) -> dict:
    code = case.get("reason_code")
    facts = {"team": case["team"], "is_complaint": case["is_complaint"], "is_dispute": case["is_dispute"],
             "fraud": case["fraud"], "dispute_fields": case.get("dispute_fields")}
    user = (f"<customer_message>{as_data(message_text)}</customer_message>\n"
            f"<facts>{json.dumps(facts, ensure_ascii=False)}</facts>\n"
            f"<reason_code>{code}: {REASON_CODES.get(code, ('', 'unknown'))[1]}</reason_code>\n"
            f"<policy_clause>{case.get('policy_clause')}: "
            f"{clause_text(case.get('policy_clause') or '')}</policy_clause>\n"
            f"<draft>{as_data(case.get('raw_draft') or '')}</draft>")
    result = llm.complete([{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
                          role="judge", purpose="judge", max_tokens=1500)
    raw = parse_json(result.text)
    return {"faithful": bool(raw.get("faithful")), "asks_for_secrets": bool(raw.get("asks_for_secrets")),
            "follows_injected_instructions": bool(raw.get("follows_injected_instructions")),
            "reason": str(raw.get("reason", ""))[:300], "model": result.model}
