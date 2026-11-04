import tkinter as tk
from tkinter import ttk

from database.connection import get_connection


class ParkingHistoryWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Parking History")
        self.geometry("980x620")
        self.configure(bg="#f8fafc")

        tk.Label(self, text="Parking History", font=("Segoe UI", 22, "bold"), bg="#f8fafc").pack(pady=(20, 10))

        columns = ("ticket", "vehicle", "owner", "slot", "status", "entry", "exit")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=18)
        for col in columns:
            tree.heading(col, text=col.title())
            tree.column(col, width=130)
        tree.pack(fill="both", expand=True, padx=18, pady=12)

        conn = get_connection()
        rows = conn.execute(
            "SELECT pr.ticket_id, v.vehicle_number, v.owner_name, s.slot_number, pr.parking_status, pr.entry_time, pr.exit_time "
            "FROM parking_records pr JOIN vehicles v ON v.vehicle_id = pr.vehicle_id JOIN parking_slots s ON s.slot_id = pr.slot_id "
            "ORDER BY pr.created_at DESC LIMIT 30"
        ).fetchall()
        conn.close()

        for row in rows:
            tree.insert("", "end", values=(row['ticket_id'], row['vehicle_number'], row['owner_name'], row['slot_number'], row['parking_status'], row['entry_time'], row['exit_time'] or "-"))
