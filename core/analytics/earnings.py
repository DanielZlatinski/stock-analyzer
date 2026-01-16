from core.analysis_models import EarningsSummary


def build_earnings_summary(earnings):
    return EarningsSummary(
        next_earnings_date=earnings.get("next_earnings_date"),
        surprise_history=earnings.get("surprise_history", []),
    )
