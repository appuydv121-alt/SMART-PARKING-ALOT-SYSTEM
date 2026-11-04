import math
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


class FeeCalculator:
    @staticmethod
    def calculate_chargeable_hours(entry_time, exit_time):
        if entry_time is None or exit_time is None:
            return 0
        if isinstance(entry_time, str):
            entry_dt = datetime.fromisoformat(entry_time)
            exit_dt = datetime.fromisoformat(exit_time)
            delta = exit_dt - entry_dt
        else:
            delta = exit_time - entry_time
        total_seconds = max(0, int(delta.total_seconds()))
        if total_seconds == 0:
            return 0
        hours = total_seconds / 3600
        return max(1, math.ceil(hours))

    @staticmethod
    def calculate_fee(hourly_rate, entry_time, exit_time):
        chargeable_hours = FeeCalculator.calculate_chargeable_hours(entry_time, exit_time)
        amount = Decimal(str(float(hourly_rate))) * Decimal(chargeable_hours)
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
