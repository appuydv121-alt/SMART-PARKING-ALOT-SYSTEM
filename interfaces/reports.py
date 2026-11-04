import tkinter as tk

from services.report_service import ReportService


class ReportsWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reports")
        self.geometry("780x520")
        self.configure(bg="#f8fafc")

        tk.Label(self, text="Revenue and Occupancy Reports", font=("Segoe UI", 22, "bold"), bg="#f8fafc").pack(pady=(20, 12))

        report = ReportService()
        revenue = report.get_revenue_summary()
        occupancy = report.get_occupancy_summary()
        breakdown = report.get_payment_breakdown()

        text = tk.Text(self, height=18, bg="#ffffff", wrap="word", font=("Segoe UI", 10))
        text.pack(fill="both", expand=True, padx=18, pady=10)

        text.insert(
            tk.END,
            f"Today's Revenue: ₹{revenue['today']}\n"
            f"Weekly Revenue: ₹{revenue['week']}\n"
            f"Monthly Revenue: ₹{revenue['month']}\n"
            f"Successful Transactions: {revenue['successful_transactions']}\n\n"
            f"Cash: ₹{breakdown['cash']}\n"
            f"UPI: ₹{breakdown['upi']}\n"
            f"Card: ₹{breakdown['card']}\n\n"
            f"Total Slots: {occupancy['total_slots']}\n"
            f"Occupied Slots: {occupancy['occupied_slots']}\n"
            f"Available Slots: {occupancy['available_slots']}\n"
            f"Car Occupancy: {occupancy['car_occupancy']}%\n"
            f"Bike Occupancy: {occupancy['bike_occupancy']}%\n"
            f"Overall Occupancy: {occupancy['overall_occupancy']}%\n"
        )
