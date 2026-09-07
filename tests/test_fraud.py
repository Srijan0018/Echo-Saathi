from decimal import Decimal

from app.fraud import assess_discrepancy


def test_outlier_is_flagged_without_rejecting_the_assessment() -> None:
    assessment = assess_discrepancy(
        [Decimal("0.00"), Decimal("0.10"), Decimal("-0.10")],
        Decimal("2.00"),
        Decimal("4.00"),
    )

    assert assessment.flagged is True
    assert "z_score_exceeds_2.5" in (assessment.reason or "")


def test_consistent_under_reporting_is_flagged() -> None:
    assessment = assess_discrepancy(
        [Decimal("-1.00"), Decimal("-1.20"), Decimal("-0.90")],
        Decimal("-1.10"),
        Decimal("6.00"),
    )

    assert assessment.flagged is True
    assert "rolling_under_reporting" in (assessment.reason or "")