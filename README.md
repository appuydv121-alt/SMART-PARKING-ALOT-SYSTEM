# Smart Parking Lot Management System

This project implements a Smart Parking Lot Management System using modular OOP design, SQLite storage (with MySQL-ready configuration), and both **Web** (HTML/CSS/JS with Flask) and **Desktop** (Tkinter) interfaces.

## Features

- **Admin & Worker Authentication**: Role-based access with PBKDF2 hashed passwords and session management
- **Parking Lot Configuration**: Automatic slot generation (Cars and Bikes) and rate management
- **Vehicle Entry**: Registration, real-time slot allocation, and entry slip generation
- **Vehicle Exit**: Instant lookup by ticket ID or vehicle number, hourly duration fee calculation, and payment processing (Cash, UPI, Card)
- **Parking Slot Management**: Live interactive status overview of all parking slots
- **Worker Management**: Admin ability to create and manage attendants
- **Reports & Analytics**: Daily/weekly/monthly revenue and occupancy statistics

---

## Running the Web Frontend (Recommended)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Web Application**:
   ```bash
   python app.py
   ```

3. **Open in browser**:
   Visit [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Default Admin Credentials:
- **Username**: `admin`
- **Password**: `admin123`

---

## Deploying to Render

The included `render.yaml` deploys the web service on Render's free plan and
requires a free Turso database because Render's free filesystem is temporary.
Create a Turso database, then set `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`
in the Render service's environment before deploying. The Blueprint marks
these values as unsynchronized so secrets are not stored in this repository.
Render also generates the Flask session key and initial admin password.

The app uses local SQLite when run outside Render without Turso configured.
The Render deployment refuses to start without both Turso settings rather
than silently storing accounts in temporary storage. Existing accounts created
before Turso is configured are not copied automatically; if they were lost
after a Render restart, they must be registered again.

---

## Running the Desktop GUI (Tkinter)

If you still want to run the original desktop window interface:
```bash
python main.py
```

---

## Running Tests

Run the full automated test suite (database, services, fee calculations, and web app routes):
```bash
python -m pytest
```

---

## Project Structure

```text
SMART_PARKING_ALOT_SYSTEM/
├── app.py                 # Flask Web application & routing
├── main.py                # Desktop GUI (Tkinter) entry point
├── config/                # App & DB configurations
├── database/              # SQLite connection, schema, seed data
├── models/                # OOP Domain Models (User, Admin, Worker, Vehicle, Car, Bike, etc.)
├── services/              # Core business logic (Auth, Parking, Fees, Payments, Reports, Slots)
├── static/                # Modern CSS & Web assets
├── templates/             # HTML templates (Dashboards, Vehicle Entry/Exit, Reports, etc.)
├── interfaces/            # Desktop GUI windows (Tkinter)
├── utils/                 # Validators and helper utilities
└── tests/                 # Pytest test suite
```
