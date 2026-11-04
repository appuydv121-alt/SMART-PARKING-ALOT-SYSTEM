from datetime import datetime

from database.connection import get_connection
from utils.validators import normalize_vehicle_number, validate_vehicle_number, validate_required_fields


class ParkingService:
    def get_lot_for_user(self, user_id: int):
        """Returns the isolated parking facility belonging to or assigned to this user."""
        conn = get_connection()
        try:
            user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not user:
                target_admin_id = 1
                user_name = "Admin"
            else:
                user_name = user['full_name'] or user['username']
                target_admin_id = user_id if user['role'] == 'ADMIN' else (user['created_by'] or 1)

            lot = conn.execute(
                "SELECT * FROM parking_lots WHERE created_by = ? ORDER BY lot_id ASC LIMIT 1",
                (target_admin_id,)
            ).fetchone()

            if lot is None and target_admin_id == 1:
                lot = conn.execute("SELECT * FROM parking_lots ORDER BY lot_id ASC LIMIT 1").fetchone()

            if lot is None:
                facility_name = f"{user_name}'s Parking"
                cur = conn.execute(
                    "INSERT INTO parking_lots (lot_name, location, created_by) VALUES (?, 'Main Facility', ?)",
                    (facility_name, target_admin_id),
                )
                conn.commit()
                lot = conn.execute("SELECT * FROM parking_lots WHERE lot_id = ?", (cur.lastrowid,)).fetchone()

                # Add default rates for this new facility
                conn.execute(
                    "INSERT INTO parking_rates (lot_id, vehicle_type, hourly_rate, effective_from, is_active) VALUES (?, 'CAR', 30.0, datetime('now'), 1)",
                    (lot['lot_id'],),
                )
                conn.execute(
                    "INSERT INTO parking_rates (lot_id, vehicle_type, hourly_rate, effective_from, is_active) VALUES (?, 'BIKE', 15.0, datetime('now'), 1)",
                    (lot['lot_id'],),
                )
                # Add default slots (10 cars, 15 bikes)
                for index in range(1, 11):
                    conn.execute(
                        "INSERT OR IGNORE INTO parking_slots (lot_id, slot_number, slot_type, occupancy_status, is_active) VALUES (?, ?, 'CAR', 'AVAILABLE', 1)",
                        (lot['lot_id'], f"C-{index:02d}"),
                    )
                for index in range(1, 16):
                    conn.execute(
                        "INSERT OR IGNORE INTO parking_slots (lot_id, slot_number, slot_type, occupancy_status, is_active) VALUES (?, ?, 'BIKE', 'AVAILABLE', 1)",
                        (lot['lot_id'], f"B-{index:02d}"),
                    )
                conn.commit()

            lot_id = lot['lot_id']
            cars = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'CAR' AND is_active = 1", (lot_id,)).fetchone()[0]
            bikes = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'BIKE' AND is_active = 1", (lot_id,)).fetchone()[0]
            car_rate_row = conn.execute(
                "SELECT hourly_rate FROM parking_rates WHERE lot_id = ? AND vehicle_type = 'CAR' AND is_active = 1 ORDER BY rate_id DESC LIMIT 1",
                (lot_id,)
            ).fetchone()
            bike_rate_row = conn.execute(
                "SELECT hourly_rate FROM parking_rates WHERE lot_id = ? AND vehicle_type = 'BIKE' AND is_active = 1 ORDER BY rate_id DESC LIMIT 1",
                (lot_id,)
            ).fetchone()

            return {
                'lot_id': lot_id,
                'lot_name': lot['lot_name'],
                'location': lot['location'],
                'car_capacity': cars,
                'bike_capacity': bikes,
                'car_rate': car_rate_row['hourly_rate'] if car_rate_row else 30.0,
                'bike_rate': bike_rate_row['hourly_rate'] if bike_rate_row else 15.0,
                'created_by': lot['created_by'],
            }
        finally:
            conn.close()

    def get_primary_lot(self, user_id: int = None):
        """Returns the primary lot for this user/admin, or the system default lot."""
        if user_id is not None:
            return self.get_lot_for_user(user_id)
        return self.get_lot_for_user(1)

    def configure_single_lot(self, lot_name: str, location: str, car_capacity: int, bike_capacity: int, car_rate: float, bike_rate: float, user_id: int = None):
        """Configures/updates the parking lot, slots, and rates for the current admin."""
        lot = self.get_lot_for_user(user_id) if user_id is not None else self.get_primary_lot()
        lot_id = lot['lot_id']
        self.update_parking_lot(lot_id, lot_name, location, car_capacity, bike_capacity, car_rate, bike_rate)
        return self.get_lot_for_user(user_id) if user_id is not None else self.get_primary_lot()

    def create_parking_lot(self, lot_name: str, location: str, created_by: int):
        if not validate_required_fields(lot_name, location, created_by):
            raise ValueError("Parking lot name and location are required.")
        conn = get_connection()
        try:
            # Check if this admin already owns a lot
            existing = conn.execute("SELECT lot_id FROM parking_lots WHERE created_by = ? ORDER BY lot_id ASC LIMIT 1", (created_by,)).fetchone()
            if existing:
                conn.execute(
                    "UPDATE parking_lots SET lot_name = ?, location = ? WHERE lot_id = ?",
                    (lot_name, location, existing['lot_id']),
                )
                conn.commit()
                return existing['lot_id']

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
            # Delete available slots to strictly enforce the new count
            conn.execute("DELETE FROM parking_slots WHERE lot_id = ? AND occupancy_status = 'AVAILABLE'", (lot_id,))
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

    def update_parking_lot(self, lot_id: int, lot_name: str, location: str, car_capacity: int, bike_capacity: int, car_rate: float = None, bike_rate: float = None):
        if not validate_required_fields(lot_name, location):
            raise ValueError("Parking lot name and location are required.")
        if car_capacity < 0 or bike_capacity < 0:
            raise ValueError("Slot capacities must be non-negative.")
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE parking_lots SET lot_name = ?, location = ? WHERE lot_id = ?",
                (lot_name, location, lot_id),
            )
            # Remove available slots to match new count exactly
            conn.execute("DELETE FROM parking_slots WHERE lot_id = ? AND occupancy_status = 'AVAILABLE'", (lot_id,))
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
            if car_rate is not None and float(car_rate) > 0:
                conn.execute("UPDATE parking_rates SET is_active = 0 WHERE lot_id = ? AND vehicle_type = 'CAR'", (lot_id,))
                conn.execute(
                    "INSERT INTO parking_rates (lot_id, vehicle_type, hourly_rate, effective_from, is_active) VALUES (?, 'CAR', ?, datetime('now'), 1)",
                    (lot_id, float(car_rate)),
                )
            if bike_rate is not None and float(bike_rate) > 0:
                conn.execute("UPDATE parking_rates SET is_active = 0 WHERE lot_id = ? AND vehicle_type = 'BIKE'", (lot_id,))
                conn.execute(
                    "INSERT INTO parking_rates (lot_id, vehicle_type, hourly_rate, effective_from, is_active) VALUES (?, 'BIKE', ?, datetime('now'), 1)",
                    (lot_id, float(bike_rate)),
                )
            conn.commit()
        finally:
            conn.close()

    def delete_parking_lot(self, lot_id: int):
        conn = get_connection()
        try:
            active_cars = conn.execute(
                "SELECT COUNT(*) FROM parking_records WHERE slot_id IN (SELECT slot_id FROM parking_slots WHERE lot_id = ?) AND parking_status = 'ACTIVE'",
                (lot_id,),
            ).fetchone()[0]
            if active_cars > 0:
                raise ValueError("Cannot delete lot with active parked vehicles.")
            conn.execute("DELETE FROM parking_rates WHERE lot_id = ?", (lot_id,))
            conn.execute("DELETE FROM parking_slots WHERE lot_id = ?", (lot_id,))
            conn.execute("DELETE FROM parking_lots WHERE lot_id = ?", (lot_id,))
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
            conn.execute("UPDATE parking_rates SET is_active = 0 WHERE lot_id = ? AND vehicle_type = ?", (lot_id, vehicle_type.upper()))
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

    def get_active_record_for_vehicle_in_lot(self, vehicle_number: str, lot_id: int):
        vehicle = self.get_vehicle(vehicle_number)
        if not vehicle:
            return None
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT pr.* FROM parking_records pr "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE pr.vehicle_id = ? AND s.lot_id = ? AND pr.parking_status = 'ACTIVE' "
                "ORDER BY pr.entry_time DESC LIMIT 1",
                (vehicle['vehicle_id'], lot_id),
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

    def get_record_by_ticket_in_lot(self, ticket_id: str, lot_id: int):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT pr.* FROM parking_records pr "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE pr.ticket_id = ? AND s.lot_id = ? AND pr.parking_status = 'ACTIVE'",
                (ticket_id, lot_id),
            ).fetchone()
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

    def get_record_by_vehicle_in_lot(self, vehicle_number: str, lot_id: int):
        vehicle = self.get_vehicle(vehicle_number)
        if not vehicle:
            return None
        return self.get_active_record_for_vehicle_in_lot(vehicle_number, lot_id)

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
