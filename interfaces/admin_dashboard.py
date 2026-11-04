import tkinter as tk
from tkinter import ttk

from database.connection import get_connection
from interfaces.parking_setup import ParkingSetupWindow
from interfaces.reports import ReportsWindow
from interfaces.slot_management import SlotManagementWindow
from interfaces.parking_history import ParkingHistoryWindow


class AdminDashboardWindow(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"Admin Dashboard - {user.full_name}")
        self.geometry("1280x760")
        self.configure(bg="#f1f5f9")
        self.minsize(1100, 680)

        sidebar_bg = "#0f172a"
        panel_bg = "#ffffff"
        accent = "#2563eb"

        self.sidebar = tk.Frame(self, width=220, bg=sidebar_bg)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="SMART PARKING", bg=sidebar_bg, fg="#e2e8f0",
                 font=("Segoe UI", 18, "bold")).pack(pady=(28, 18))
        tk.Label(self.sidebar, text=f"Admin: {user.full_name}", bg=sidebar_bg, fg="#bfdbfe",
                 font=("Segoe UI", 10)).pack(pady=(0, 18))

        navs = [
            ("Dashboard", self.refresh_dashboard),
            ("Parking Setup", self.open_setup),
            ("Slot Management", self.open_slots),
            ("Parking History", self.open_history),
            ("Reports", self.open_reports),
            ("Logout", self.close_app),
        ]

        for label, action in navs:
            btn = tk.Button(self.sidebar, text=label, width=18, height=2, bg=sidebar_bg, fg="white",
                            bd=0, activebackground="#1d4ed8", activeforeground="white",
                            font=("Segoe UI", 10, "bold"), command=action)
            btn.pack(pady=4)

        self.main = tk.Frame(self, bg="#f1f5f9")
        self.main.pack(side="left", fill="both", expand=True, padx=18, pady=16)

        self.header = tk.Frame(self.main, bg="#f1f5f9")
        self.header.pack(fill="x")
        tk.Label(self.header, text="Admin Dashboard", bg="#f1f5f9", fg="#0f172a",
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(self.header, text="Overview of occupancy, transactions, and parking activity",
                 bg="#f1f5f9", fg="#475569", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 18))

        self.cards = tk.Frame(self.main, bg="#f1f5f9")
        self.cards.pack(fill="x", pady=(0, 16))
        self.stat_cards = []
        for _ in range(4):
            card = tk.Frame(self.cards, bg=panel_bg, bd=1, relief="solid", padx=18, pady=18)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            self.stat_cards.append(card)

        self.middle = tk.Frame(self.main, bg="#f1f5f9")
        self.middle.pack(fill="both", expand=True)

        self.left_summary = tk.Frame(self.middle, bg=panel_bg, bd=1, relief="solid")
        self.left_summary.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(self.left_summary, text="Facility Summary", bg=panel_bg, fg="#0f172a",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        self.summary_text = tk.Text(self.left_summary, height=15, bg="#f8fafc", wrap="word", font=("Segoe UI", 10))
        self.summary_text.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        self.right_summary = tk.Frame(self.middle, bg=panel_bg, bd=1, relief="solid")
        self.right_summary.pack(side="left", fill="y", padx=(0, 0))
        tk.Label(self.right_summary, text="Recent Activity", bg=panel_bg, fg="#0f172a",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        self.activity = tk.Text(self.right_summary, height=15, bg="#f8fafc", wrap="word", font=("Segoe UI", 10))
        self.activity.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        self.refresh_dashboard()

    def _make_stat_card(self, title, value, accent_color="#2563eb"):
        card = self.stat_cards[len(self.stat_cards) - 1]
        for child in card.winfo_children():
            child.destroy()

    def _set_card(self, card, title, value, accent_color):
        card.configure(bg="#ffffff")
        tk.Label(card, text=title, bg="#ffffff", fg="#64748b", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(card, text=value, bg="#ffffff", fg=accent_color, font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(6, 0))

    def refresh_dashboard(self):
        from database.connection import get_connection

        conn = get_connection()
        stats = {
            'total_slots': conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1").fetchone()[0],
            'occupied_slots': conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND occupancy_status = 'OCCUPIED'").fetchone()[0],
            'available_slots': conn.execute("SELECT COUNT(*) FROM parking_slots WHERE is_active = 1 AND occupancy_status = 'AVAILABLE'").fetchone()[0],
            'today_revenue': conn.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_status = 'SUCCESS' AND date(payment_time) = date('now')").fetchone()[0],
        }
        active_records = conn.execute("SELECT COUNT(*) FROM parking_records WHERE parking_status = 'ACTIVE'").fetchone()[0]
        successful_payments = conn.execute("SELECT COUNT(*) FROM payments WHERE payment_status = 'SUCCESS'").fetchone()[0]
        conn.close()

        cards = [
            ("Total Slots", str(stats['total_slots']), "#2563eb"),
            ("Occupied", str(stats['occupied_slots']), "#dc2626"),
            ("Available", str(stats['available_slots']), "#16a34a"),
            ("Today Revenue", f"₹{stats['today_revenue']}", "#7c3aed"),
        ]

        for card, (title, value, color) in zip(self.stat_cards, cards):
            for child in card.winfo_children():
                child.destroy()
            self._set_card(card, title, value, color)

        summary = (
            f"Parking lots: {conn.execute('SELECT COUNT(*) FROM parking_lots').fetchone()[0] if False else '1'}\n"
            f"Active vehicles: {active_records}\n"
            f"Completed payments: {successful_payments}\n"
            f"Current occupancy: {stats['occupied_slots']}/{stats['total_slots']}\n"
            f"Parking rate snapshot is managed by the service layer and stored in the database."
        )
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, summary)

        history = []
        conn = get_connection()
        rows = conn.execute(
            "SELECT pr.ticket_id, v.vehicle_number, v.owner_name, pr.parking_status, pr.entry_time "
            "FROM parking_records pr JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
            "ORDER BY pr.created_at DESC LIMIT 8"
        ).fetchall()
        for row in rows:
            history.append(f"{row['ticket_id']} | {row['vehicle_number']} | {row['parking_status']} | {row['entry_time']}")
        conn.close()
        self.activity.delete("1.0", tk.END)
        self.activity.insert(tk.END, "\n".join(history) if history else "No recent activity yet.")

    def open_setup(self):
        window = ParkingSetupWindow()
        window.mainloop()

    def open_slots(self):
        window = SlotManagementWindow()
        window.mainloop()

    def open_history(self):
        window = ParkingHistoryWindow()
        window.mainloop()

    def open_reports(self):
        window = ReportsWindow()
        window.mainloop()

    def close_app(self):
        self.destroy()
