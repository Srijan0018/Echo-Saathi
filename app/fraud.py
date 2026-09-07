from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FraudAssessment:
    z_score: Decimal
    rolling_mean: Decimal
    rolling_std: Decimal
    flagged: bool
    reason: str | None


def assess_discrepancy(
    history: list[Decimal],
    current_discrepancy: Decimal,
    ai_midpoint: Decimal,
) -> FraudAssessment:
    prior = history[-30:]
    if not prior:
        return FraudAssessment(Decimal("0.00"), current_discrepancy, Decimal("1.00"), False, None)

    rolling_mean = sum(prior, Decimal("0")) / Decimal(len(prior))
    variance = sum((value - rolling_mean) ** 2 for value in prior) / Decimal(len(prior))
    rolling_std = variance.sqrt()
    z_score = (current_discrepancy - rolling_mean) / (rolling_std or Decimal("1"))
    outlier_flag = abs(z_score) > Decimal("2.5")
    systematic_flag = rolling_mean < (Decimal("-0.15") * ai_midpoint)
    reasons: list[str] = []
    if outlier_flag:
        reasons.append("z_score_exceeds_2.5")
    if systematic_flag:
        reasons.append("rolling_under_reporting")
    return FraudAssessment(
        z_score.quantize(Decimal("0.01")),
        rolling_mean.quantize(Decimal("0.01")),
        rolling_std.quantize(Decimal("0.01")),
        bool(reasons),
        ",".join(reasons) if reasons else None,
    )
