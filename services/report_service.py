from database.connection import get_connection


class ReportService:
    def get_revenue_summary(self, lot_id: int = None):
        conn = get_connection()
        if lot_id is not None:
            today = conn.execute(
                "SELECT COALESCE(SUM(p.amount),0) FROM payments p "
                "JOIN parking_records pr ON pr.record_id = p.record_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE s.lot_id = ? AND p.payment_status = 'SUCCESS' AND date(p.payment_time) = date('now')",
                (lot_id,)
            ).fetchone()[0]
            week = conn.execute(
                "SELECT COALESCE(SUM(p.amount),0) FROM payments p "
                "JOIN parking_records pr ON pr.record_id = p.record_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE s.lot_id = ? AND p.payment_status = 'SUCCESS' AND p.payment_time >= date('now','-7 days')",
                (lot_id,)
            ).fetchone()[0]
            month = conn.execute(
                "SELECT COALESCE(SUM(p.amount),0) FROM payments p "
                "JOIN parking_records pr ON pr.record_id = p.record_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE s.lot_id = ? AND p.payment_status = 'SUCCESS' AND p.payment_time >= date('now','-30 days')",
                (lot_id,)
            ).fetchone()[0]
            count = conn.execute(
                "SELECT COUNT(*) FROM payments p "
                "JOIN parking_records pr ON pr.record_id = p.record_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE s.lot_id = ? AND p.payment_status = 'SUCCESS'",
                (lot_id,)
            ).fetchone()[0]
        else:
            today = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status = 'SUCCESS' AND date(payment_time) = date('now')").fetchone()[0]
            week = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status = 'SUCCESS' AND payment_time >= date('now','-7 days')").fetchone()[0]
            month = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status = 'SUCCESS' AND payment_time >= date('now','-30 days')").fetchone()[0]
            count = conn.execute("SELECT COUNT(*) FROM payments WHERE payment_status='SUCCESS'").fetchone()[0]

        conn.close()
        return {
            'today': today,
            'week': week,
            'month': month,
            'successful_transactions': count,
        }

    def get_payment_breakdown(self, lot_id: int = None):
        conn = get_connection()
        if lot_id is not None:
            cash = conn.execute(
                "SELECT COALESCE(SUM(p.amount),0) FROM payments p "
                "JOIN parking_records pr ON pr.record_id = p.record_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE s.lot_id = ? AND p.payment_status='SUCCESS' AND p.payment_method='CASH'",
                (lot_id,)
            ).fetchone()[0]
            upi = conn.execute(
                "SELECT COALESCE(SUM(p.amount),0) FROM payments p "
                "JOIN parking_records pr ON pr.record_id = p.record_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE s.lot_id = ? AND p.payment_status='SUCCESS' AND p.payment_method='UPI'",
                (lot_id,)
            ).fetchone()[0]
            card = conn.execute(
                "SELECT COALESCE(SUM(p.amount),0) FROM payments p "
                "JOIN parking_records pr ON pr.record_id = p.record_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE s.lot_id = ? AND p.payment_status='SUCCESS' AND p.payment_method='CARD'",
                (lot_id,)
            ).fetchone()[0]
        else:
            cash = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status='SUCCESS' AND payment_method='CASH'").fetchone()[0]
            upi = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status='SUCCESS' AND payment_method='UPI'").fetchone()[0]
            card = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status='SUCCESS' AND payment_method='CARD'").fetchone()[0]
        conn.close()
        return {'cash': cash, 'upi': upi, 'card': card}

    def get_occupancy_summary(self, lot_id: int = None):
        conn = get_connection()
        if lot_id is not None:
            total_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND is_active = 1", (lot_id,)).fetchone()[0]
            occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND is_active = 1 AND occupancy_status = 'OCCUPIED'", (lot_id,)).fetchone()[0]
            cars = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND is_active = 1 AND slot_type = 'CAR'", (lot_id,)).fetchone()[0]
            occupied_cars = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND is_active = 1 AND slot_type = 'CAR' AND occupancy_status = 'OCCUPIED'", (lot_id,)).fetchone()[0]
            bikes = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND is_active = 1 AND slot_type = 'BIKE'", (lot_id,)).fetchone()[0]
            occupied_bikes = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND is_active = 1 AND slot_type = 'BIKE' AND occupancy_status = 'OCCUPIED'", (lot_id,)).fetchone()[0]
        else:
            total_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1").fetchone()[0]
            occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND occupancy_status = 'OCCUPIED'").fetchone()[0]
            cars = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'CAR'", (lot_id,)).fetchone()[0]
            occupied_cars = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'CAR' AND occupancy_status = 'OCCUPIED'", (lot_id,)).fetchone()[0]
            bikes = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'BIKE'", (lot_id,)).fetchone()[0]
            occupied_bikes = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'BIKE' AND occupancy_status = 'OCCUPIED'", (lot_id,)).fetchone()[0]

        available = total_slots - occupied
        conn.close()
        return {
            'total_slots': total_slots,
            'available_slots': available,
            'occupied_slots': occupied,
            'car_occupancy': round((occupied_cars / cars * 100), 2) if cars else 0,
            'bike_occupancy': round((occupied_bikes / bikes * 100), 2) if bikes else 0,
            'overall_occupancy': round((occupied / total_slots * 100), 2) if total_slots else 0,
        }
