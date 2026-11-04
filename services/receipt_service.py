from pathlib import Path

from models.receipt import Receipt


class ReceiptService:
    def generate_entry_slip(self, parking_record):
        receipt_number = f"ENTRY-{parking_record.ticket_id}"
        receipt = Receipt(receipt_number=receipt_number, receipt_type='ENTRY')
        payload = receipt.generate_entry_slip(parking_record)
        return receipt, payload

    def generate_exit_receipt(self, parking_record, payment):
        receipt_number = f"RECEIPT-{parking_record.ticket_id}"
        receipt = Receipt(receipt_number=receipt_number, receipt_type='EXIT')
        payload = receipt.generate_exit_receipt(parking_record, payment)
        return receipt, payload

    def save_receipt(self, receipt, payload, directory='receipts'):
        location = Path(directory)
        location.mkdir(exist_ok=True, parents=True)
        file_path = location / f"{receipt.receipt_number}.txt"
        file_path.write_text(str(payload), encoding='utf-8')
        return str(file_path)
