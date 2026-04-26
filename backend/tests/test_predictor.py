from app.services.predictor import predict_next_7_days, weighted_moving_average


def test_weighted_moving_average_recent_points_have_higher_weight() -> None:
    result = weighted_moving_average([100, 100, 200])
    assert result == 150


def test_predict_next_7_days_increases_with_higher_intervention() -> None:
    base = [1000, 1200, 1100, 1300, 1250, 1400, 1500]

    low = predict_next_7_days(base, discount_rate=0, update_quality=0)
    high = predict_next_7_days(base, discount_rate=80, update_quality=9)

    assert len(low) == 7
    assert len(high) == 7
    assert max(high) > max(low)
    assert min(low) >= 0
