import tkinter as tk
from tkinter import ttk

from database.connection import get_connection


class SlotManagementWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Parking Slot Management")
        self.geometry("820x560")
        self.configure(bg="#f8fafc")

        tk.Label(self, text="Parking Slots", font=("Segoe UI", 20, "bold"), bg="#f8fafc").pack(pady=(20, 10))

        columns = ("slot_number", "slot_type", "status", "active")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        tree.heading("slot_number", text="Slot Number")
        tree.heading("slot_type", text="Type")
        tree.heading("status", text="Status")
        tree.heading("active", text="Active")
        tree.pack(fill="both", expand=True, padx=18, pady=10)

        conn = get_connection()
        rows = conn.execute("SELECT slot_number, slot_type, occupancy_status, is_active FROM parking_slots ORDER BY slot_type, slot_number").fetchall()
        conn.close()

        for row in rows:
            tree.insert("", "end", values=(row['slot_number'], row['slot_type'], row['occupancy_status'], "Yes" if row['is_active'] else "No"))

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
