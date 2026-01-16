from core.analysis_models import PeerComparison


def _percentile_rank(value, peer_values):
    if value is None or not peer_values:
        return None
    sorted_vals = sorted(peer_values)
    below = len([v for v in sorted_vals if v < value])
    return round((below / len(sorted_vals)) * 100, 1)


def build_peer_comparison(ticker, fundamentals, peer_fundamentals):
    metrics = ["pe_ratio", "forward_pe", "revenue_growth", "roe", "debt_to_equity"]
    peer_metrics = []
    for peer, data in peer_fundamentals.items():
        peer_metrics.append(
            {
                "ticker": peer,
                **{metric: data.get(metric) for metric in metrics},
            }
        )

    percentile_ranks = {}
    for metric in metrics:
        peer_values = [
            data.get(metric)
            for data in peer_fundamentals.values()
            if data.get(metric) is not None
        ]
        percentile_ranks[metric] = _percentile_rank(
            fundamentals.get(metric), peer_values
        )

    return PeerComparison(
        peer_metrics=peer_metrics,
        percentile_ranks=percentile_ranks,
    )
