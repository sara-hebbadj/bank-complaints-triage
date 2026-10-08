"""The synthetic transactions table in DuckDB, and matching a dispute to one transaction.

Matching is plain code: candidates are the customer's own transactions (the message arrives through the
signed-in app, so the customer ID is known), filtered by card last-4 when given, then scored:
amount equal +3, same date +2 (within 3 days +1), merchant name similar +2. The best score wins if it is 3 or more.
"""

from __future__ import annotations

import threading
from datetime import date
from pathlib import Path

import duckdb

from .config import DATA_DIR
from .extract import merchant_similarity


class TransactionStore:
    def __init__(self, csv_path: Path = DATA_DIR / "transactions.csv"):
        self.con = duckdb.connect()  # in memory; the CSV is the source of truth
        self.lock = threading.Lock()  # one DuckDB connection is not safe to share between threads
        self.con.execute(
            "CREATE TABLE transactions AS SELECT * FROM read_csv(?, header = true, columns = {"
            "'txn_id': 'VARCHAR', 'customer_id': 'VARCHAR', 'card_last4': 'VARCHAR', 'merchant': 'VARCHAR', "
            "'amount_aed': 'DOUBLE', 'txn_date': 'DATE', 'kind': 'VARCHAR'})", [str(csv_path)])

    def for_customer(self, customer_id: str) -> list[dict]:
        with self.lock:
            cursor = self.con.execute(
                "SELECT txn_id, card_last4, merchant, amount_aed, txn_date FROM transactions "
                "WHERE customer_id = ? ORDER BY txn_date, txn_id", [customer_id])
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def merchants(self) -> list[str]:
        with self.lock:
            return [row[0] for row in self.con.execute("SELECT DISTINCT merchant FROM transactions").fetchall()]

    def match(self, customer_id: str, fields: dict) -> dict | None:
        """The customer's transaction that best fits the extracted fields, or None."""
        candidates = self.for_customer(customer_id)
        if fields.get("card_last4"):
            on_card = [row for row in candidates if row["card_last4"] == fields["card_last4"]]
            candidates = on_card or candidates  # a wrong last-4 should not hide the transaction
        best, best_score = None, 0
        for row in candidates:
            score = 0
            if fields.get("amount") is not None and abs(row["amount_aed"] - float(fields["amount"])) < 0.01:
                score += 3
            if fields.get("transaction_date"):
                gap = abs((row["txn_date"] - date.fromisoformat(fields["transaction_date"])).days)
                score += 2 if gap == 0 else 1 if gap <= 3 else 0
            if merchant_similarity(fields.get("merchant"), row["merchant"]) >= 0.5:
                score += 2
            # ">=" keeps the later of two equal rows (for a duplicate charge, the second payment)
            if score >= best_score and score > 0:
                best, best_score = row, score
        if best is None or best_score < 3:
            return None
        return {**best, "txn_date": best["txn_date"].isoformat(), "score": best_score}
