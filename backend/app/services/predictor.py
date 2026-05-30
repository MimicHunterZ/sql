from __future__ import annotations

from typing import List, Dict


MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


def weighted_moving_average(values: List[float]) -> float:
    if not values:
        return 0.0
    weights = list(range(1, len(values) + 1))
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    total_w = sum(weights)
    return weighted_sum / total_w


def _parse_month_abs(s: str) -> int:
    """'April 2026'  →  2026 * 12 + 3  (absolute month index)"""
    parts = s.strip().split()
    return int(parts[1]) * 12 + MONTHS.index(parts[0])


def _fmt_month_abs(abs_idx: int) -> str:
    """2026 * 12 + 3  →  'April 2026'"""
    return f"{MONTHS[abs_idx % 12]} {abs_idx // 12}"


def predict_next_7_days(base_values: List[int], discount_rate: float, update_quality: float) -> List[int]:
    base = weighted_moving_average(base_values)
    discount_factor = 1.0 + 0.35 * (discount_rate / 100.0)
    update_factor = 1.0 + 0.25 * (update_quality / 10.0)

    # 先上冲后回落，保持趋势平滑。
    day_decay = [1.00, 1.03, 1.05, 1.04, 1.02, 1.00, 0.98]

    preds: List[int] = []
    for decay in day_decay:
        value = base * discount_factor * update_factor * decay
        preds.append(max(int(round(value)), 0))
    return preds


def predict_monthly_to_dec2026(
    history_rows: List[Dict],   # [{month: "April 2026", avg_players: ..., peak_players: ...}, ...]  newest→oldest
    discount_rate: float,
    update_quality: float,
) -> List[Dict]:
    """
    Predict monthly avg_players from the month after the last known data through December 2026.
    Uses seasonal decomposition (12-month pattern) + mild trend + what-if multipliers.
    Returns list of {month, avg_players} oldest→newest.
    """
    if not history_rows:
        return []

    # Sort oldest → newest
    sorted_h = sorted(history_rows, key=lambda x: _parse_month_abs(x['month']))

    latest_abs = _parse_month_abs(sorted_h[-1]['month'])
    target_abs = _parse_month_abs('December 2026')

    if latest_abs >= target_abs:
        return []   # data already covers Dec 2026

    # ── Seasonal factors (use up to last 36 months) ──────────────────────────
    recent = sorted_h[-36:]
    avgs = [r['avg_players'] for r in recent]
    overall_avg = sum(avgs) / len(avgs) if avgs else 1.0

    monthly_vals: Dict[int, List[float]] = {m: [] for m in range(12)}
    for r in recent:
        m = _parse_month_abs(r['month']) % 12
        monthly_vals[m].append(r['avg_players'])

    seasonal_factor: Dict[int, float] = {}
    for m in range(12):
        vals = monthly_vals[m]
        if vals and overall_avg > 0:
            seasonal_factor[m] = (sum(vals) / len(vals)) / overall_avg
        else:
            seasonal_factor[m] = 1.0

    # ── Trend: last 3 months vs previous 3 (compound monthly growth rate) ────
    if len(sorted_h) >= 6:
        last3  = sum(r['avg_players'] for r in sorted_h[-3:]) / 3
        prev3  = sum(r['avg_players'] for r in sorted_h[-6:-3]) / 3
        cmgr = (last3 / prev3) ** (1 / 3) if prev3 > 0 else 1.0
        # Clamp: don't let trend drift more than ±3% per month
        cmgr = min(max(cmgr, 0.97), 1.03)
    else:
        cmgr = 1.0

    # ── Base: WMA of last 6 months ────────────────────────────────────────────
    base = weighted_moving_average([r['avg_players'] for r in sorted_h[-6:]])

    # ── What-if multipliers ───────────────────────────────────────────────────
    discount_factor = 1.0 + 0.35 * (discount_rate / 100.0)
    update_factor   = 1.0 + 0.25 * (update_quality / 10.0)
    param_mult = discount_factor * update_factor

    # ── Generate predictions ──────────────────────────────────────────────────
    n_months = target_abs - latest_abs
    results = []
    for i in range(n_months):
        abs_idx = latest_abs + i + 1
        m_idx = abs_idx % 12

        sf = seasonal_factor.get(m_idx, 1.0)
        trend_mult = cmgr ** (i + 1)          # compound over forecast horizon

        value = base * sf * trend_mult * param_mult
        results.append({
            'month':       _fmt_month_abs(abs_idx),
            'avg_players': max(int(round(value)), 0),
        })

    return results
