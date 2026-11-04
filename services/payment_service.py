from database.connection import get_connection


class PaymentService:
    def record_payment(self, record_id: int, amount: float, payment_method: str, processed_by: int, payment_status: str = 'SUCCESS', transaction_reference=None):
        method = payment_method.upper()
        if method not in {'CASH', 'UPI', 'CARD'}:
            raise ValueError("Payment method must be CASH, UPI, or CARD.")
        if payment_status.upper() not in {'PENDING', 'SUCCESS', 'FAILED'}:
            raise ValueError("Payment status must be PENDING, SUCCESS, or FAILED.")
        conn = get_connection()
        existing = conn.execute(
            "SELECT payment_id FROM payments WHERE record_id = ? AND payment_status = 'SUCCESS'",
            (record_id,),
        ).fetchone()
        if existing and payment_status.upper() == 'SUCCESS':
            conn.close()
            raise ValueError("A successful payment has already been recorded for this parking session.")
        cur = conn.execute(
            "INSERT INTO payments (record_id, amount, payment_method, payment_status, processed_by, transaction_reference) VALUES (?, ?, ?, ?, ?, ?)",
            (record_id, float(amount), method, payment_status.upper(), processed_by, transaction_reference),
        )
        conn.commit()
        conn.close()
        return cur.lastrowid
