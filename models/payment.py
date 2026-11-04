class Payment:
    def __init__(self, payment_id=None, parking_record=None, amount=0.0, payment_method="CASH", payment_status="PENDING"):
        self.payment_id = payment_id
        self.parking_record = parking_record
        self.amount = amount
        self.payment_method = payment_method
        self.payment_status = payment_status

    def process_payment(self):
        self.payment_status = "SUCCESS"
        return self.payment_status

    def verify_payment(self):
        return self.payment_status == "SUCCESS"

    def record_payment(self):
        return self.process_payment()
