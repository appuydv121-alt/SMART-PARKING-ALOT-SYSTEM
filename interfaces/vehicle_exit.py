import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.connection import get_connection
from services.fee_calculator import FeeCalculator
from services.payment_service import PaymentService
from services.parking_service import ParkingService


class VehicleExitWindow(tk.Tk):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.title("Vehicle Exit")
        self.geometry("850x620")
        self.configure(bg="#f8fafc")

        tk.Label(self, text="Vehicle Exit", font=("Segoe UI", 22, "bold"), bg="#f8fafc").pack(pady=(20, 10))

        top = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        top.pack(fill="x", padx=18, pady=(0, 12))

        tk.Label(top, text="Search by Ticket ID or Vehicle Number", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))
        self.search_value = tk.Entry(top, width=28, font=("Segoe UI", 10))
        self.search_value.grid(row=0, column=1, padx=18, pady=(18, 8), sticky="w")
        tk.Button(top, text="Find Record", width=18, height=2, bg="#2563eb", fg="white",
                  font=("Segoe UI", 10, "bold"), command=self.search_record).grid(row=0, column=2, padx=(0, 18), pady=(18, 8))

        body = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.record_details = tk.Text(body, height=14, bg="#f8fafc", wrap="word", font=("Segoe UI", 10))
        self.record_details.pack(fill="both", expand=True, padx=18, pady=(18, 12))

        bottom = tk.Frame(body, bg="#ffffff")
        bottom.pack(fill="x", padx=18, pady=(0, 18))

        tk.Label(bottom, text="Payment Method", bg="#ffffff", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.payment_method = ttk.Combobox(bottom, width=18, values=["CASH", "UPI", "CARD"], state="readonly")
        self.payment_method.grid(row=0, column=1, sticky="w", padx=(8, 18))
        self.payment_method.set("CASH")

        tk.Button(bottom, text="Process Exit", width=18, height=2, bg="#16a34a", fg="white",
                  font=("Segoe UI", 10, "bold"), command=self.process_exit).grid(row=0, column=2, sticky="w")

        self.current_record = None

    def search_record(self):
        try:
            query = self.search_value.get().strip()
            if not query:
                raise ValueError("Enter ticket ID or vehicle number.")
            service = ParkingService()
            record = service.get_record_by_ticket(query)
            if not record:
                record = service.get_record_by_vehicle(query)
            if not record:
                raise ValueError("No active parking record found.")

            conn = get_connection()
            vehicle = conn.execute("SELECT vehicle_number, owner_name, vehicle_type FROM vehicles WHERE vehicle_id = ?", (record['vehicle_id'],)).fetchone()
            slot = conn.execute("SELECT slot_number FROM parking_slots WHERE slot_id = ?", (record['slot_id'],)).fetchone()
            conn.close()

            self.current_record = record
            details = (
                f"Ticket ID: {record['ticket_id']}\n"
                f"Vehicle: {vehicle['vehicle_number']}\n"
                f"Owner: {vehicle['owner_name']}\n"
                f"Type: {vehicle['vehicle_type']}\n"
                f"Slot: {slot['slot_number']}\n"
                f"Entry Time: {record['entry_time']}\n"
                f"Rate: ₹{record['applied_hourly_rate']}/hour"
            )
            self.record_details.delete("1.0", tk.END)
            self.record_details.insert(tk.END, details)
        except Exception as exc:
            messagebox.showerror("Search failed", str(exc))

    def process_exit(self):
        try:
            if self.current_record is None:
                raise ValueError("Find a parking record first.")

            exit_time = datetime.now().isoformat(timespec='seconds')
            amount = FeeCalculator.calculate_fee(self.current_record['applied_hourly_rate'], self.current_record['entry_time'], exit_time)
            worker_id = getattr(self.user, 'user_id', 1) if self.user is not None else 1
            PaymentService().record_payment(self.current_record['record_id'], float(amount), self.payment_method.get(), worker_id, 'SUCCESS')
            ParkingService().complete_exit(self.current_record['record_id'], worker_id, exit_time, self.current_record['applied_hourly_rate'])
            self.record_details.delete("1.0", tk.END)
            self.record_details.insert(
                tk.END,
                f"Exit processed successfully\n"
                f"Exit Time: {exit_time}\n"
                f"Amount: ₹{float(amount)}\n"
                f"Payment Method: {self.payment_method.get()}\n"
                f"Status: Completed"
            )
        except Exception as exc:
            messagebox.showerror("Exit failed", str(exc))
