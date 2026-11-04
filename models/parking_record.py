from datetime import datetime


class ParkingRecord:
    def __init__(self, record_id=None, ticket_id="", vehicle=None, slot=None, entry_time=None, exit_time=None, total_fee=0, status="ACTIVE"):
        self.record_id = record_id
        self.ticket_id = ticket_id
        self.vehicle = vehicle
        self.slot = slot
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.total_fee = total_fee
        self.status = status

    def calculate_duration(self):
        if self.entry_time is None:
            return 0
        end = self.exit_time or datetime.now()
        delta = end - self.entry_time
        return max(0, delta.total_seconds())

    def calculate_fee(self, hourly_rate):
        seconds = self.calculate_duration()
        if seconds <= 0:
            return 0
        hours = seconds / 3600
        import math
        chargeable_hours = max(1, math.ceil(hours))
        return chargeable_hours * float(hourly_rate)

    def complete_session(self):
        self.status = "COMPLETED"
        return self.status
