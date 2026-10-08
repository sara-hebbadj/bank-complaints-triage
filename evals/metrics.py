"""Small metric helpers. Every metric is reported with its denominator."""

from __future__ import annotations

from statistics import quantiles

from sklearn.metrics import cohen_kappa_score, f1_score


def pct(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.1f}% ({numerator}/{denominator})" if denominator else "n/a (0)"


def macro_f1(gold: list[str], predicted: list[str]) -> float:
    return round(float(f1_score(gold, predicted, average="macro", zero_division=0)), 4)


def accuracy(gold: list, predicted: list) -> tuple[int, int]:
    return sum(g == p for g, p in zip(gold, predicted, strict=True)), len(gold)


def precision_recall(gold: list[bool], predicted: list[bool]) -> dict:
    tp = sum(g and p for g, p in zip(gold, predicted, strict=True))
    fp = sum(p and not g for g, p in zip(gold, predicted, strict=True))
    fn = sum(g and not p for g, p in zip(gold, predicted, strict=True))
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": pct(tp, tp + fp), "recall": pct(tp, tp + fn),
            "precision_value": tp / (tp + fp) if tp + fp else None, "recall_value": tp / (tp + fn) if tp + fn else None}


def kappa(a: list, b: list) -> float | None:
    """Cohen's kappa; None when it is undefined (both raters used a single label)."""
    if len(set(a) | set(b)) < 2:
        return None
    return round(float(cohen_kappa_score(a, b)), 3)


def p50_p95(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    cuts = quantiles(values, n=100, method="inclusive")
    return round(cuts[49], 1), round(cuts[94], 1)
