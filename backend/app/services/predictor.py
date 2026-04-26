from __future__ import annotations

from typing import List


def weighted_moving_average(values: List[int]) -> float:
    if not values:
        return 0.0
    weights = list(range(1, len(values) + 1))
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    total_w = sum(weights)
    return weighted_sum / total_w


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
