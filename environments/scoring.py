"""Objective evaluation of predictions against known anomalies (Section 11)."""
from __future__ import annotations

from typing import Dict, List


def score(predictions: List[int], labels: List[int]) -> Dict[str, float]:
    if len(predictions) != len(labels):
        raise ValueError("prediction/label length mismatch")
    tp = sum(1 for p, l in zip(predictions, labels) if p and l)
    fp = sum(1 for p, l in zip(predictions, labels) if p and not l)
    fn = sum(1 for p, l in zip(predictions, labels) if not p and l)
    tn = len(labels) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if labels else 0.0
    # quality is the objective score: F1 when positives exist (accuracy is dominated by
    # the majority class); when a batch has no positives, F1 is undefined and quality is
    # specificity, so flagging nothing scores 1.0 and every false positive costs.
    if tp + fn == 0:
        quality = tn / (tn + fp) if (tn + fp) else 1.0
    else:
        quality = f1
    return {"quality": quality, "f1": f1, "precision": precision, "recall": recall, "accuracy": accuracy,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}
