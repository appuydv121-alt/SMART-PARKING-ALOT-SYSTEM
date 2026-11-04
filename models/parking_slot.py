class ParkingSlot:
    def __init__(self, slot_id=None, lot_id=None, slot_number="", slot_type="CAR", occupancy_status="AVAILABLE", is_active=True):
        self.slot_id = slot_id
        self.lot_id = lot_id
        self.slot_number = slot_number
        self.slot_type = slot_type.upper()
        self.occupancy_status = occupancy_status.upper()
        self.is_active = bool(is_active)

    def occupy_slot(self):
        self.occupancy_status = "OCCUPIED"

    def release_slot(self):
        self.occupancy_status = "AVAILABLE"

    def check_availability(self):
        return self.is_active and self.occupancy_status == "AVAILABLE"
