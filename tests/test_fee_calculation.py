from datetime import datetime, timedelta

from services.fee_calculator import FeeCalculator


def test_fee_calculation_rounds_up_to_next_hour():
    rate = 30
    entry = datetime(2024, 1, 1, 10, 0)
    exit_time = entry + timedelta(hours=3)
    assert FeeCalculator.calculate_chargeable_hours(entry, exit_time) == 3
    fee = FeeCalculator.calculate_fee(rate, entry, exit_time)
    assert float(fee) == 90.0
