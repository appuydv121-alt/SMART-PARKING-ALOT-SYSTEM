import tkinter as tk
from tkinter import messagebox

from database.connection import initialize_database
from database.seed import seed_default_data
from services.auth_service import AuthenticationService


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Parking Lot Management System")
        self.geometry("900x560")
        self.configure(bg="#edf2f7")
        self.resizable(False, False)

        container = tk.Frame(self, bg="#edf2f7")
        container.pack(fill="both", expand=True)

        left = tk.Frame(container, bg="#102a43", width=420, height=560)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="SMART PARKING", fg="white", bg="#102a43",
                 font=("Segoe UI", 24, "bold")).place(relx=0.5, rely=0.22, anchor="center")
        tk.Label(left, text="Lot Management System", fg="#dbeafe", bg="#102a43",
                 font=("Segoe UI", 12)).place(relx=0.5, rely=0.32, anchor="center")
        tk.Label(left, text="Secure access for admin and attendants",
                 fg="#bfdbfe", bg="#102a43", font=("Segoe UI", 11)).place(relx=0.5, rely=0.4, anchor="center")

        right = tk.Frame(container, bg="#ffffff", width=480, height=560)
        right.pack(side="left", fill="both", expand=True)
        right.pack_propagate(False)

        tk.Label(right, text="Welcome back", font=("Segoe UI", 22, "bold"), fg="#0f172a").pack(pady=(55, 10))
        tk.Label(right, text="Sign in to continue", font=("Segoe UI", 10), fg="#475569").pack()

        form = tk.Frame(right, bg="#ffffff")
        form.pack(pady=24)

        tk.Label(form, text="Username", bg="#ffffff", font=("Segoe UI", 10, "bold"), fg="#334155").pack(anchor="w", padx=22)
        self.username_entry = tk.Entry(form, width=32, font=("Segoe UI", 11), bd=1, relief="solid")
        self.username_entry.pack(padx=22, pady=(6, 16))

        tk.Label(form, text="Password", bg="#ffffff", font=("Segoe UI", 10, "bold"), fg="#334155").pack(anchor="w", padx=22)
        self.password_entry = tk.Entry(form, width=32, font=("Segoe UI", 11), bd=1, relief="solid", show="*")
        self.password_entry.pack(padx=22, pady=(6, 18))

        tk.Button(form, text="Login", width=30, height=2, bg="#2563eb", fg="white",
                  font=("Segoe UI", 10, "bold"), bd=0, command=self.handle_login).pack(pady=8)

        footer = tk.Label(right, text="Default admin: admin / admin123", fg="#64748b", bg="#ffffff",
                          font=("Segoe UI", 9))
        footer.pack(side="bottom", pady=24)

        self.username_entry.focus_set()
        self.bind("<Return>", lambda event: self.handle_login())

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        try:
            initialize_database()
            seed_default_data()
            user = AuthenticationService().login(username, password)
            if user.role == 'ADMIN':
                from interfaces.admin_dashboard import AdminDashboardWindow
                window = AdminDashboardWindow(user)
            else:
                from interfaces.worker_dashboard import WorkerDashboardWindow
                window = WorkerDashboardWindow(user)
            self.destroy()
            window.mainloop()
        except ValueError as exc:
            messagebox.showerror("Authentication failed", str(exc))
