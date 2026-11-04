from pathlib import Path


class Receipt:
    def __init__(self, receipt_number="", receipt_type="ENTRY"):
        self.receipt_number = receipt_number
        self.receipt_type = receipt_type

    def generate_entry_slip(self, parking_record):
        return {
            'receipt_number': self.receipt_number,
            'receipt_type': 'ENTRY',
            'ticket_id': parking_record.ticket_id,
            'vehicle_number': parking_record.vehicle.vehicle_number,
            'vehicle_type': getattr(parking_record.vehicle, 'vehicle_type', 'CAR'),
            'slot_number': parking_record.slot.slot_number if parking_record.slot else '',
        }

    def generate_exit_receipt(self, parking_record, payment):
        return {
            'receipt_number': self.receipt_number,
            'receipt_type': 'EXIT',
            'ticket_id': parking_record.ticket_id,
            'vehicle_number': parking_record.vehicle.vehicle_number,
            'amount': payment.amount,
            'payment_method': payment.payment_method,
        }

    def save_as_pdf(self, payload, directory):
        location = Path(directory)
        location.mkdir(exist_ok=True, parents=True)
        file_path = location / f"{self.receipt_number}.txt"
        file_path.write_text(str(payload), encoding='utf-8')
        return str(file_path)

    def print_receipt(self, payload):
        return payload
