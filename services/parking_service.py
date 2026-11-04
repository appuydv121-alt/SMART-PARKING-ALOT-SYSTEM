from datetime import datetime

from database.connection import get_connection
from utils.validators import normalize_vehicle_number, validate_vehicle_number, validate_required_fields


class ParkingService:
    def create_parking_lot(self, lot_name: str, location: str, created_by: int):
        if not validate_required_fields(lot_name, location, created_by):
            raise ValueError("Parking lot name and location are required.")
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO parking_lots (lot_name, location, created_by) VALUES (?, ?, ?)",
                (lot_name, location, created_by),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def generate_slots_for_lot(self, lot_id: int, car_capacity: int, bike_capacity: int):
        if car_capacity < 0 or bike_capacity < 0:
            raise ValueError("Slot capacities must be non-negative.")
        conn = get_connection()
        try:
            for index in range(1, int(car_capacity) + 1):
                slot_number = f"C-{index:02d}"
                conn.execute(
                    "INSERT OR IGNORE INTO parking_slots (lot_id, slot_number, slot_type, occupancy_status, is_active) VALUES (?, ?, 'CAR', 'AVAILABLE', 1)",
                    (lot_id, slot_number),
                )
            for index in range(1, int(bike_capacity) + 1):
                slot_number = f"B-{index:02d}"
                conn.execute(
                    "INSERT OR IGNORE INTO parking_slots (lot_id, slot_number, slot_type, occupancy_status, is_active) VALUES (?, ?, 'BIKE', 'AVAILABLE', 1)",
                    (lot_id, slot_number),
                )
            conn.commit()
        finally:
            conn.close()

    def add_parking_rate(self, lot_id: int, vehicle_type: str, hourly_rate: float, effective_from=None):
        if vehicle_type.upper() not in {'CAR', 'BIKE'}:
            raise ValueError("Vehicle type must be CAR or BIKE.")
        if float(hourly_rate) <= 0:
            raise ValueError("Hourly rate must be positive.")
        effective = effective_from or datetime.now().isoformat(timespec='seconds')
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO parking_rates (lot_id, vehicle_type, hourly_rate, effective_from, is_active) VALUES (?, ?, ?, ?, 1)",
                (lot_id, vehicle_type.upper(), float(hourly_rate), effective),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def create_vehicle(self, vehicle_number: str, owner_name: str, vehicle_type: str):
        if not validate_required_fields(vehicle_number, owner_name, vehicle_type):
            raise ValueError("Vehicle number, owner name and type are required.")
        normalized = normalize_vehicle_number(vehicle_number)
        if not validate_vehicle_number(normalized):
            raise ValueError("Invalid vehicle number format.")
        if vehicle_type.upper() not in {'CAR', 'BIKE'}:
            raise ValueError("Vehicle type must be CAR or BIKE.")
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM vehicles WHERE vehicle_number = ?",
                (normalized,),
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    "INSERT INTO vehicles (vehicle_number, owner_name, vehicle_type) VALUES (?, ?, ?)",
                    (normalized, owner_name.strip(), vehicle_type.upper()),
                )
                conn.commit()
                return cur.lastrowid
            return row['vehicle_id']
        finally:
            conn.close()

    def get_vehicle(self, vehicle_number: str):
        normalized = normalize_vehicle_number(vehicle_number)
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM vehicles WHERE vehicle_number = ?", (normalized,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_active_record_for_vehicle(self, vehicle_number: str):
        vehicle = self.get_vehicle(vehicle_number)
        if not vehicle:
            return None
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM parking_records WHERE vehicle_id = ? AND parking_status = 'ACTIVE' ORDER BY entry_time DESC LIMIT 1",
                (vehicle['vehicle_id'],),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create_parking_record(self, vehicle_id: int, slot_id: int, entry_worker_id: int, hourly_rate: float, ticket_id: str):
        conn = get_connection()
        try:
            entry_time = datetime.now().isoformat(timespec='seconds')
            cur = conn.execute(
                "INSERT INTO parking_records (ticket_id, vehicle_id, slot_id, entry_worker_id, entry_time, applied_hourly_rate, chargeable_duration, total_fee, parking_status) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'ACTIVE')",
                (ticket_id, vehicle_id, slot_id, entry_worker_id, entry_time, float(hourly_rate)),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_record_by_ticket(self, ticket_id: str):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM parking_records WHERE ticket_id = ?", (ticket_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_record_by_vehicle(self, vehicle_number: str):
        vehicle = self.get_vehicle(vehicle_number)
        if not vehicle:
            return None
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM parking_records WHERE vehicle_id = ? AND parking_status = 'ACTIVE' ORDER BY entry_time DESC LIMIT 1",
                (vehicle['vehicle_id'],),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def complete_exit(self, record_id: int, exit_worker_id: int, exit_time: str, hourly_rate: float):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM parking_records WHERE record_id = ?", (record_id,)).fetchone()
            if row is None:
                raise ValueError("Parking record not found.")
            entry_dt = datetime.fromisoformat(row['entry_time'])
            exit_dt = datetime.fromisoformat(exit_time)
            if exit_dt < entry_dt:
                raise ValueError("Exit time cannot be earlier than entry time.")
            duration_seconds = int((exit_dt - entry_dt).total_seconds())
            chargeable_hours = max(1, (duration_seconds + 3599) // 3600)
            amount = float(hourly_rate) * chargeable_hours
            conn.execute(
                "UPDATE parking_records SET exit_worker_id = ?, exit_time = ?, chargeable_duration = ?, total_fee = ?, parking_status = 'COMPLETED' WHERE record_id = ?",
                (exit_worker_id, exit_time, chargeable_hours, amount, record_id),
            )
            conn.execute("UPDATE parking_slots SET occupancy_status = 'AVAILABLE' WHERE slot_id = ?", (row['slot_id'],))
            conn.commit()
            return {
                'record_id': record_id,
                'chargeable_duration': chargeable_hours,
                'total_fee': amount,
            }
        finally:
            conn.close()
