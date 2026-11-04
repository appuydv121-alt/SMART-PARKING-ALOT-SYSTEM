import tkinter as tk


class PaymentScreenWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Payment")
        self.geometry("600x400")
        tk.Label(self, text="Payment Processing", font=("Segoe UI", 16, "bold")).pack(pady=20)
