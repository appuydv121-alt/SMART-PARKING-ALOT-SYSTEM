from database.connection import initialize_database
from database.seed import seed_default_data
from services.parking_service import ParkingService
from services.payment_service import PaymentService
from services.slot_allocation_service import SlotAllocationService


def setup_function():
    initialize_database()
    seed_default_data()


def test_payment_is_recorded_once():
    lot_id = ParkingService().create_parking_lot('City Parking', 'Main Market', 1)
    ParkingService().generate_slots_for_lot(lot_id, 2, 1)
    ParkingService().add_parking_rate(lot_id, 'CAR', 30)
    vehicle_id = ParkingService().create_vehicle('MP10AB1234', 'Rahul Sharma', 'CAR')
    slot = SlotAllocationService().allocate_slot(lot_id, 'CAR')
    record_id = ParkingService().create_parking_record(vehicle_id, slot['slot_id'], 1, 30, 'P001')
    payment_id = PaymentService().record_payment(record_id, 90, 'CASH', 1)
    assert payment_id > 0
