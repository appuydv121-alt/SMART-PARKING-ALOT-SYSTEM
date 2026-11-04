import tkinter as tk
from tkinter import ttk, messagebox

from database.connection import get_connection
from services.parking_service import ParkingService
from services.slot_allocation_service import SlotAllocationService


class VehicleEntryWindow(tk.Tk):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.title("Vehicle Entry")
        self.geometry("760x560")
        self.configure(bg="#f8fafc")

        tk.Label(self, text="Vehicle Entry", font=("Segoe UI", 22, "bold"), bg="#f8fafc").pack(pady=(18, 12))

        frame = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        frame.pack(fill="both", expand=True, padx=18, pady=8)

        tk.Label(frame, text="Vehicle Number", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))
        self.vehicle_number = tk.Entry(frame, width=28, font=("Segoe UI", 10))
        self.vehicle_number.grid(row=0, column=1, padx=18, pady=(18, 8), sticky="w")

        tk.Label(frame, text="Owner Name", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=1, column=0, sticky="w", padx=18, pady=8)
        self.owner_name = tk.Entry(frame, width=28, font=("Segoe UI", 10))
        self.owner_name.grid(row=1, column=1, padx=18, pady=8, sticky="w")

        tk.Label(frame, text="Vehicle Type", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=2, column=0, sticky="w", padx=18, pady=8)
        self.vehicle_type = ttk.Combobox(frame, width=25, values=["CAR", "BIKE"], state="readonly")
        self.vehicle_type.grid(row=2, column=1, padx=18, pady=8, sticky="w")
        self.vehicle_type.set("CAR")

        tk.Button(frame, text="Register Vehicle", width=24, height=2, bg="#2563eb", fg="white",
                  font=("Segoe UI", 10, "bold"), command=self.register_vehicle).grid(row=3, column=1, sticky="w", padx=18, pady=(14, 18))

        self.result = tk.Text(self, height=12, bg="#f8fafc", wrap="word", font=("Segoe UI", 10))
        self.result.pack(fill="both", expand=True, padx=18, pady=(8, 18))

    def register_vehicle(self):
        try:
            vehicle_number = self.vehicle_number.get().strip()
            owner_name = self.owner_name.get().strip()
            vehicle_type = self.vehicle_type.get().upper()

            if not vehicle_number or not owner_name:
                raise ValueError("Vehicle number and owner name are required.")

            conn = get_connection()
            lot_row = conn.execute("SELECT lot_id FROM parking_lots ORDER BY lot_id DESC LIMIT 1").fetchone()
            conn.close()
            if lot_row is None:
                raise ValueError("Create a parking lot first.")

            service = ParkingService()
            vehicle_id = service.create_vehicle(vehicle_number, owner_name, vehicle_type)
            active = service.get_active_record_for_vehicle(vehicle_number)
            if active:
                raise ValueError("This vehicle already has an active parking session.")

            slot = SlotAllocationService().allocate_slot(lot_row['lot_id'], vehicle_type)
            conn = get_connection()
            rate_row = conn.execute(
                "SELECT hourly_rate FROM parking_rates WHERE lot_id = ? AND vehicle_type = ? ORDER BY rate_id DESC LIMIT 1",
                (lot_row['lot_id'], vehicle_type),
            ).fetchone()
            conn.close()
            if rate_row is None:
                raise ValueError("Parking rate not configured for this vehicle type.")

            ticket_id = f"P{vehicle_id:04d}"
            worker_id = getattr(self.user, 'user_id', 1) if self.user is not None else 1
            service.create_parking_record(vehicle_id, slot['slot_id'], worker_id, rate_row['hourly_rate'], ticket_id)
            self.result.delete("1.0", tk.END)
            self.result.insert(
                tk.END,
                f"Vehicle registered successfully\n"
                f"Ticket ID: {ticket_id}\n"
                f"Vehicle: {vehicle_number}\n"
                f"Owner: {owner_name}\n"
                f"Type: {vehicle_type}\n"
                f"Allocated Slot: {slot['slot_number']}\n"
                f"Rate: ₹{rate_row['hourly_rate']}/hour"
            )
            self.vehicle_number.delete(0, tk.END)
            self.owner_name.delete(0, tk.END)
        except Exception as exc:
            messagebox.showerror("Entry failed", str(exc))
