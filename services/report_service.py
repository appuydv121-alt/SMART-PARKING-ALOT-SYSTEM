from database.connection import get_connection


class ReportService:
    def get_revenue_summary(self):
        conn = get_connection()
        report = {
            'today': conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status = 'SUCCESS' AND date(payment_time) = date('now')").fetchone()[0],
            'week': conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status = 'SUCCESS' AND payment_time >= date('now','-7 days')").fetchone()[0],
            'month': conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status = 'SUCCESS' AND payment_time >= date('now','-30 days')").fetchone()[0],
            'successful_transactions': conn.execute("SELECT COUNT(*) FROM payments WHERE payment_status='SUCCESS'").fetchone()[0],
        }
        conn.close()
        return report

    def get_payment_breakdown(self):
        conn = get_connection()
        breakdown = {
            'cash': conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status='SUCCESS' AND payment_method='CASH'").fetchone()[0],
            'upi': conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status='SUCCESS' AND payment_method='UPI'").fetchone()[0],
            'card': conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_status='SUCCESS' AND payment_method='CARD'").fetchone()[0],
        }
        conn.close()
        return breakdown

    def get_occupancy_summary(self):
        conn = get_connection()
        total_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1").fetchone()[0]
        occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND occupancy_status = 'OCCUPIED'").fetchone()[0]
        available = total_slots - occupied
        cars = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'CAR'").fetchone()[0]
        occupied_cars = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'CAR' AND occupancy_status = 'OCCUPIED'").fetchone()[0]
        bikes = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'BIKE'").fetchone()[0]
        occupied_bikes = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND slot_type = 'BIKE' AND occupancy_status = 'OCCUPIED'").fetchone()[0]
        conn.close()
        return {
            'total_slots': total_slots,
            'available_slots': available,
            'occupied_slots': occupied,
            'car_occupancy': round((occupied_cars / cars * 100), 2) if cars else 0,
            'bike_occupancy': round((occupied_bikes / bikes * 100), 2) if bikes else 0,
            'overall_occupancy': round((occupied / total_slots * 100), 2) if total_slots else 0,
        }
