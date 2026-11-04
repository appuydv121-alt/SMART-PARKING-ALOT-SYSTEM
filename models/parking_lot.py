class ParkingLot:
    def __init__(self, lot_id=None, lot_name="", location="", slots=None):
        self.lot_id = lot_id
        self.lot_name = lot_name
        self.location = location
        self.slots = slots or []

    def add_slot(self, slot):
        self.slots.append(slot)

    def deactivate_slot(self, slot_number):
        for slot in self.slots:
            if slot.slot_number == slot_number:
                slot.is_active = False
                slot.occupancy_status = "AVAILABLE"
                return True
        return False

    def find_available_slot(self, slot_type):
        for slot in self.slots:
            if slot.slot_type == slot_type.upper() and slot.check_availability():
                return slot
        return None

    def get_available_slots(self, slot_type=None):
        if slot_type is None:
            return [slot for slot in self.slots if slot.check_availability()]
        return [slot for slot in self.slots if slot.slot_type == slot_type.upper() and slot.check_availability()]

    def get_occupancy(self):
        occupied = sum(1 for slot in self.slots if slot.occupancy_status == "OCCUPIED")
        return {"occupied": occupied, "available": len(self.slots) - occupied, "total": len(self.slots)}
