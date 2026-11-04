import tkinter as tk
from tkinter import ttk, messagebox

from services.parking_service import ParkingService


class ParkingSetupWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Parking Lot Setup")
        self.geometry("700x520")
        self.configure(bg="#f8fafc")

        tk.Label(self, text="Parking Lot Configuration", font=("Segoe UI", 20, "bold"), bg="#f8fafc").pack(pady=(20, 10))

        form = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        form.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(form, text="Lot Name", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))
        self.lot_name = tk.Entry(form, width=35, font=("Segoe UI", 10))
        self.lot_name.grid(row=0, column=1, padx=18, pady=(18, 8), sticky="w")

        tk.Label(form, text="Location", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=1, column=0, sticky="w", padx=18, pady=8)
        self.location = tk.Entry(form, width=35, font=("Segoe UI", 10))
        self.location.grid(row=1, column=1, padx=18, pady=8, sticky="w")

        tk.Label(form, text="Car Capacity", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=2, column=0, sticky="w", padx=18, pady=8)
        self.car_capacity = ttk.Spinbox(form, from_=0, to=200, width=10)
        self.car_capacity.grid(row=2, column=1, padx=18, pady=8, sticky="w")
        self.car_capacity.set("20")

        tk.Label(form, text="Bike Capacity", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=3, column=0, sticky="w", padx=18, pady=8)
        self.bike_capacity = ttk.Spinbox(form, from_=0, to=200, width=10)
        self.bike_capacity.grid(row=3, column=1, padx=18, pady=8, sticky="w")
        self.bike_capacity.set("30")

        tk.Label(form, text="Car Rate (₹/hr)", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=4, column=0, sticky="w", padx=18, pady=8)
        self.car_rate = tk.Entry(form, width=15, font=("Segoe UI", 10))
        self.car_rate.grid(row=4, column=1, padx=18, pady=8, sticky="w")
        self.car_rate.insert(0, "30")

        tk.Label(form, text="Bike Rate (₹/hr)", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=5, column=0, sticky="w", padx=18, pady=8)
        self.bike_rate = tk.Entry(form, width=15, font=("Segoe UI", 10))
        self.bike_rate.grid(row=5, column=1, padx=18, pady=8, sticky="w")
        self.bike_rate.insert(0, "15")

        tk.Button(self, text="Create Parking Lot", width=26, height=2, bg="#2563eb", fg="white",
                  font=("Segoe UI", 10, "bold"), command=self.create_lot).pack(pady=14)

    def create_lot(self):
        try:
            lot_name = self.lot_name.get().strip()
            location = self.location.get().strip()
            car_capacity = int(self.car_capacity.get())
            bike_capacity = int(self.bike_capacity.get())
            car_rate = float(self.car_rate.get())
            bike_rate = float(self.bike_rate.get())

            if not lot_name or not location:
                raise ValueError("Lot name and location are required.")

            lot_id = ParkingService().create_parking_lot(lot_name, location, 1)
            ParkingService().generate_slots_for_lot(lot_id, car_capacity, bike_capacity)
            ParkingService().add_parking_rate(lot_id, 'CAR', car_rate)
            ParkingService().add_parking_rate(lot_id, 'BIKE', bike_rate)
            messagebox.showinfo("Success", f"Parking lot '{lot_name}' created successfully.")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Setup failed", str(exc))
