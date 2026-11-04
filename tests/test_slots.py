from database.connection import initialize_database
from database.seed import seed_default_data
from services.parking_service import ParkingService
from services.slot_allocation_service import SlotAllocationService


def setup_function():
    initialize_database()
    seed_default_data()


def test_duplicate_active_vehicle_is_blocked():
    lot_id = ParkingService().create_parking_lot('City Parking', 'Main Market', 1)
    ParkingService().generate_slots_for_lot(lot_id, 1, 1)
    ParkingService().add_parking_rate(lot_id, 'CAR', 30)
    vehicle_id = ParkingService().create_vehicle('MP10AB1234', 'Rahul Sharma', 'CAR')
    slot = SlotAllocationService().allocate_slot(lot_id, 'CAR')
    ParkingService().create_parking_record(vehicle_id, slot['slot_id'], 1, 30, 'P001')
    active = ParkingService().get_active_record_for_vehicle('MP10AB1234')
    assert active is not None
    assert active['ticket_id'] == 'P001'
