from models.vehicle import Vehicle


class Car(Vehicle):
    def __init__(self, vehicle_id=None, vehicle_number="", owner_name=""):
        super().__init__(vehicle_id=vehicle_id, vehicle_number=vehicle_number, owner_name=owner_name)

    def calculate_rate(self, rate):
        return float(rate)
