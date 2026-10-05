"""Transfer decisions (spec §6, §30). Thresholds are fixed constants registered before the evaluation run."""
from __future__ import annotations

from typing import Any, Dict

PRINCIPLE_DECISIONS = ("TRUST", "TEST", "REJECT", "IGNORE", "ABSTAIN")
ENVIRONMENT_DECISIONS = ("REUSE", "MODIFY", "BUILD_NEW", "ABSTAIN")
TRUST_T, TEST_T, IGNORE_T = 0.80, 0.40, 0.20
ACCEPT_FRACTION, ACCEPT_MIN, RETEST_BAND = 0.4, 0.02, 0.03      # a tested transformation is accepted if its measured effect reaches this share of the prediction
PATIENCE = 8                                 # adaptation economics: stop refining after this many non-improving evaluations
SHIFT_SD, DROP = 1.5, 0.08                   # regime detection: feature shift in training-sd units; incumbent score drop


def decide(pred: Dict[str, Any], hidden_sensitive: bool, use_confidence: bool = True, use_contraindications: bool = True) -> str:
    """Per-principle decision from its prediction in the current environment.

    TRUST   apply without testing            REJECT  an observable contraindication holds
    TEST    measure before applying          IGNORE  predicted not to help
    ABSTAIN "I don't know whether this transfers" (neither applied nor tested up front)
    """
    if use_contraindications and pred["contraindicated"]:
        return "REJECT"
    if not use_confidence:
        return "TRUST" if pred["p_help"] >= 0.5 else "IGNORE"
    c = pred["confidence"]
    if pred["out_of_range"] and c >= TEST_T:
        return "TEST"
    if c >= TRUST_T:
        return "TEST" if (hidden_sensitive and use_contraindications) else "TRUST"
    if c >= TEST_T:
        return "TEST"
    if c <= IGNORE_T:
        return "IGNORE"
    return "ABSTAIN"
