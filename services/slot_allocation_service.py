from database.connection import get_connection


class SlotAllocationService:
    def allocate_slot(self, lot_id: int, vehicle_type: str):
        if vehicle_type.upper() not in {'CAR', 'BIKE'}:
            raise ValueError("Vehicle type must be CAR or BIKE.")
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT slot_id, slot_number FROM parking_slots WHERE lot_id = ? AND slot_type = ? AND is_active = 1 AND occupancy_status = 'AVAILABLE' ORDER BY slot_number LIMIT 1",
                (lot_id, vehicle_type.upper()),
            ).fetchone()
            if row is None:
                conn.rollback()
                raise ValueError(f"No {vehicle_type.lower()} parking slots available.")
            conn.execute(
                "UPDATE parking_slots SET occupancy_status = 'OCCUPIED' WHERE slot_id = ?",
                (row['slot_id'],),
            )
            conn.commit()
            return {'slot_id': row['slot_id'], 'slot_number': row['slot_number']}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release_slot(self, slot_id: int):
        conn = get_connection()
        conn.execute("UPDATE parking_slots SET occupancy_status = 'AVAILABLE' WHERE slot_id = ?", (slot_id,))
        conn.commit()
        conn.close()
