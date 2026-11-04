from database.connection import initialize_database
from database.seed import seed_default_data
from services.parking_service import ParkingService
from services.slot_allocation_service import SlotAllocationService


def setup_function():
    initialize_database()
    seed_default_data()


def test_slot_allocation_and_parking_lot_creation():
    lot_id = ParkingService().create_parking_lot('City Parking', 'Main Market', 1)
    ParkingService().generate_slots_for_lot(lot_id, 2, 2)
    ParkingService().add_parking_rate(lot_id, 'CAR', 30)
    allocated = SlotAllocationService().allocate_slot(lot_id, 'CAR')
    assert allocated['slot_number'] == 'C-01'
    assert allocated['slot_id'] > 0
    vehicle_id = ParkingService().create_vehicle('MP10AB1234', 'Rahul Sharma', 'CAR')
    record_id = ParkingService().create_parking_record(vehicle_id, allocated['slot_id'], 1, 30, 'P001')
    assert record_id > 0
