import tkinter as tk

from interfaces.vehicle_entry import VehicleEntryWindow
from interfaces.vehicle_exit import VehicleExitWindow
from interfaces.parking_history import ParkingHistoryWindow


class WorkerDashboardWindow(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"Worker Dashboard - {user.full_name}")
        self.geometry("1200x760")
        self.configure(bg="#f8fafc")
        self.minsize(1000, 640)

        sidebar = tk.Frame(self, bg="#0f172a", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="SMART PARKING", bg="#0f172a", fg="#e2e8f0",
                 font=("Segoe UI", 18, "bold")).pack(pady=(28, 18))
        tk.Label(sidebar, text=f"Attendant: {user.full_name}", bg="#0f172a", fg="#bfdbfe",
                 font=("Segoe UI", 10)).pack(pady=(0, 18))

        navs = [
            ("Dashboard", self.refresh_dashboard),
            ("Vehicle Entry", self.open_vehicle_entry),
            ("Vehicle Exit", self.open_vehicle_exit),
            ("Parking History", self.open_history),
            ("Logout", self.close_app),
        ]

        for label, callback in navs:
            btn = tk.Button(sidebar, text=label, width=18, height=2, bg="#0f172a", fg="white",
                            bd=0, activebackground="#1d4ed8", activeforeground="white",
                            font=("Segoe UI", 10, "bold"), command=callback)
            btn.pack(pady=4)

        main = tk.Frame(self, bg="#f8fafc")
        main.pack(side="left", fill="both", expand=True, padx=18, pady=18)

        tk.Label(main, text="Worker Dashboard", bg="#f8fafc", fg="#0f172a",
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(main, text="Daily operations and parking activity overview", bg="#f8fafc",
                 fg="#475569", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 18))

        stat_frame = tk.Frame(main, bg="#f8fafc")
        stat_frame.pack(fill="x", pady=(0, 18))
        self.stat_cards = []
        for title, color in [("Cars", "#2563eb"), ("Bikes", "#16a34a"), ("Free Slots", "#f59e0b"), ("Parked", "#ef4444")]:
            card = tk.Frame(stat_frame, bg="#ffffff", bd=1, relief="solid", padx=18, pady=16)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tk.Label(card, text=title, bg="#ffffff", fg="#64748b", font=("Segoe UI", 10)).pack(anchor="w")
            tk.Label(card, text="0", bg="#ffffff", fg=color, font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(6, 0))
            self.stat_cards.append(card)

        content = tk.Frame(main, bg="#f8fafc")
        content.pack(fill="both", expand=True)

        left = tk.Frame(content, bg="#ffffff", bd=1, relief="solid")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(left, text="Current Parking Summary", bg="#ffffff", fg="#0f172a",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 10))
        self.summary = tk.Text(left, height=13, bg="#f8fafc", wrap="word", font=("Segoe UI", 10))
        self.summary.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        right = tk.Frame(content, bg="#ffffff", bd=1, relief="solid")
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Recent Activity", bg="#ffffff", fg="#0f172a",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 10))
        self.activity = tk.Text(right, height=13, bg="#f8fafc", wrap="word", font=("Segoe UI", 10))
        self.activity.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.refresh_dashboard()

    def refresh_dashboard(self):
        from database.connection import get_connection

        conn = get_connection()
        car_total = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE slot_type = 'CAR' AND is_active = 1").fetchone()[0]
        bike_total = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE slot_type = 'BIKE' AND is_active = 1").fetchone()[0]
        car_occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE slot_type = 'CAR' AND occupancy_status = 'OCCUPIED' AND is_active = 1").fetchone()[0]
        bike_occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE slot_type = 'BIKE' AND occupancy_status = 'OCCUPIED' AND is_active = 1").fetchone()[0]
        parked = conn.execute("SELECT COUNT(*) FROM parking_records WHERE parking_status = 'ACTIVE'").fetchone()[0]
        conn.close()

        values = [car_total, bike_total, car_total - car_occupied + bike_total - bike_occupied, parked]
        for label, value in zip(self.stat_cards, values):
            for child in label.winfo_children():
                if isinstance(child, tk.Label):
                    child.destroy()
            tk.Label(label, text=["Cars", "Bikes", "Free Slots", "Parked"][self.stat_cards.index(label)], bg="#ffffff",
                     fg="#64748b", font=("Segoe UI", 10)).pack(anchor="w")
            tk.Label(label, text=str(value), bg="#ffffff", fg=["#2563eb", "#16a34a", "#f59e0b", "#ef4444"][self.stat_cards.index(label)],
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(6, 0))

        summary_text = (
            f"Total car slots: {car_total}\n"
            f"Occupied car slots: {car_occupied}\n"
            f"Available car slots: {car_total - car_occupied}\n"
            f"Total bike slots: {bike_total}\n"
            f"Occupied bike slots: {bike_occupied}\n"
            f"Available bike slots: {bike_total - bike_occupied}\n"
            f"Currently parked vehicles: {parked}\n"
            f"Today's operations are tracked in the database."
        )
        self.summary.delete("1.0", tk.END)
        self.summary.insert(tk.END, summary_text)

        conn = get_connection()
        activity_rows = conn.execute(
            "SELECT pr.ticket_id, v.vehicle_number, pr.parking_status, pr.entry_time FROM parking_records pr JOIN vehicles v ON v.vehicle_id = pr.vehicle_id ORDER BY pr.created_at DESC LIMIT 6"
        ).fetchall()
        conn.close()

        activity_text = "\n".join(
            [f"{row['ticket_id']} | {row['vehicle_number']} | {row['parking_status']} | {row['entry_time']}" for row in activity_rows]
        ) if activity_rows else "No recent activity yet."
        self.activity.delete("1.0", tk.END)
        self.activity.insert(tk.END, activity_text)

    def open_vehicle_entry(self):
        window = VehicleEntryWindow()
        window.mainloop()

    def open_vehicle_exit(self):
        window = VehicleExitWindow()
        window.mainloop()

    def open_history(self):
        from interfaces.parking_history import ParkingHistoryWindow
        window = ParkingHistoryWindow()
        window.mainloop()

    def close_app(self):
        self.destroy()
