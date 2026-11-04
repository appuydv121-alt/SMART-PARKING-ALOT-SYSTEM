"""
Flask web application for Smart Parking Lot Management System.
This replaces the Tkinter GUI while reusing the exact same backend logic
(models, services, database, validators).
"""
from datetime import datetime
import os

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response

from database.connection import ensure_database, initialize_database, get_connection
from database.seed import seed_default_data
from services.auth_service import AuthenticationService
from services.parking_service import ParkingService
from services.slot_allocation_service import SlotAllocationService
from services.fee_calculator import FeeCalculator
from services.payment_service import PaymentService
from services.report_service import ReportService
from services.worker_service import WorkerManagementService

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smart-parking-secret-key-2024')


# ---------------------------------------------------------------------------
# Initialise database on first request without dropping existing data
# ---------------------------------------------------------------------------
with app.app_context():
    ensure_database()
    seed_default_data()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login_required(f):
    """Decorator that redirects to login if user is not authenticated."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator that requires ADMIN role."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'ADMIN':
            flash('Admin access required.', 'error')
            return redirect(url_for('worker_dashboard'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        if session.get('role') == 'ADMIN':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('worker_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        try:
            user = AuthenticationService().login(username, password)
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['role'] = user.role
            if user.role == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('worker_dashboard'))
        except ValueError as exc:
            flash(str(exc), 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'WORKER').upper()

        if not full_name or not username or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 4:
            flash('Password must be at least 4 characters long.', 'error')
            return render_template('register.html')

        if role not in ('WORKER', 'ADMIN'):
            role = 'WORKER'

        try:
            new_user_id = AuthenticationService().create_user(username=username, full_name=full_name, password=password, role=role)
            if role == 'ADMIN':
                ParkingService().get_lot_for_user(new_user_id)
            flash(f'Account created successfully for {username}! Please sign in.', 'success')
            return redirect(url_for('login'))
        except ValueError as exc:
            flash(str(exc), 'error')

    return render_template('register.html')


# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    service = ParkingService()
    lot = service.get_lot_for_user(session['user_id'])
    lot_id = lot['lot_id']

    conn = get_connection()
    car_total = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'CAR' AND is_active = 1", (lot_id,)).fetchone()[0]
    bike_total = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'BIKE' AND is_active = 1", (lot_id,)).fetchone()[0]
    car_occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'CAR' AND occupancy_status = 'OCCUPIED' AND is_active = 1", (lot_id,)).fetchone()[0]
    bike_occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'BIKE' AND occupancy_status = 'OCCUPIED' AND is_active = 1", (lot_id,)).fetchone()[0]
    car_available = car_total - car_occupied
    bike_available = bike_total - bike_occupied
    total_slots = car_total + bike_total
    occupied_slots = car_occupied + bike_occupied
    available_slots = car_available + bike_available

    today_revenue = conn.execute(
        "SELECT COALESCE(SUM(p.amount), 0) FROM payments p "
        "JOIN parking_records pr ON pr.record_id = p.record_id "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "WHERE s.lot_id = ? AND p.payment_status = 'SUCCESS' AND date(p.payment_time) = date('now')",
        (lot_id,)
    ).fetchone()[0]

    active_records = conn.execute(
        "SELECT COUNT(*) FROM parking_records pr "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "WHERE s.lot_id = ? AND pr.parking_status = 'ACTIVE'",
        (lot_id,)
    ).fetchone()[0]

    successful_payments = conn.execute(
        "SELECT COUNT(*) FROM payments p "
        "JOIN parking_records pr ON pr.record_id = p.record_id "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "WHERE s.lot_id = ? AND p.payment_status = 'SUCCESS'",
        (lot_id,)
    ).fetchone()[0]

    stats = {
        'total_slots': total_slots,
        'occupied_slots': occupied_slots,
        'available_slots': available_slots,
        'car_total': car_total,
        'car_occupied': car_occupied,
        'car_available': car_available,
        'bike_total': bike_total,
        'bike_occupied': bike_occupied,
        'bike_available': bike_available,
        'today_revenue': today_revenue,
        'active_records': active_records,
        'successful_payments': successful_payments,
    }

    slots = [dict(r) for r in conn.execute(
        "SELECT slot_number, slot_type, occupancy_status FROM parking_slots WHERE lot_id = ? AND is_active = 1 ORDER BY slot_type, slot_number",
        (lot_id,)
    ).fetchall()]

    recent = [dict(r) for r in conn.execute(
        "SELECT pr.ticket_id, v.vehicle_number, v.owner_name, pr.parking_status, pr.entry_time "
        "FROM parking_records pr "
        "JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "WHERE s.lot_id = ? "
        "ORDER BY pr.created_at DESC LIMIT 8",
        (lot_id,)
    ).fetchall()]
    conn.close()
    return render_template('admin_dashboard.html', stats=stats, slots=slots, recent=recent, lot=lot)


# ---------------------------------------------------------------------------
# Parking Setup (Admin) - Single Parking Lot Configuration
# ---------------------------------------------------------------------------
@app.route('/admin/parking-setup', methods=['GET', 'POST'])
@admin_required
def parking_setup():
    service = ParkingService()
    if request.method == 'POST':
        try:
            lot_name = request.form['lot_name'].strip()
            location = request.form['location'].strip()
            car_capacity = int(request.form['car_capacity'])
            bike_capacity = int(request.form['bike_capacity'])
            car_rate = float(request.form['car_rate'])
            bike_rate = float(request.form['bike_rate'])

            if not lot_name or not location:
                raise ValueError("Lot name and location are required.")

            service.configure_single_lot(lot_name, location, car_capacity, bike_capacity, car_rate, bike_rate, user_id=session['user_id'])
            flash(f"Parking facility '{lot_name}' updated successfully! Slots and rates reconfigured.", 'success')
            return redirect(url_for('parking_setup'))
        except Exception as exc:
            flash(str(exc), 'error')

    lot = service.get_lot_for_user(session['user_id'])
    return render_template('parking_setup.html', lot=lot)


# ---------------------------------------------------------------------------
# Slot Management (Admin) - Single Parking Lot Slots
# ---------------------------------------------------------------------------
@app.route('/admin/slots')
@admin_required
def slot_management():
    service = ParkingService()
    lot = service.get_lot_for_user(session['user_id'])
    conn = get_connection()
    rows = conn.execute(
        "SELECT slot_number, slot_type, occupancy_status, is_active FROM parking_slots WHERE lot_id = ? ORDER BY slot_type, slot_number",
        (lot['lot_id'],)
    ).fetchall()
    conn.close()
    slots = [dict(r) for r in rows]
    return render_template('slot_management.html', slots=slots, lot=lot)


# ---------------------------------------------------------------------------
# Parking History (Admin + Worker)
# ---------------------------------------------------------------------------
@app.route('/history')
@login_required
def parking_history():
    service = ParkingService()
    lot = service.get_lot_for_user(session['user_id'])
    lot_id = lot['lot_id']
    conn = get_connection()
    rows = conn.execute(
        "SELECT pr.ticket_id, v.vehicle_number, v.owner_name, s.slot_number, "
        "pr.parking_status, pr.entry_time, pr.exit_time "
        "FROM parking_records pr "
        "JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "WHERE s.lot_id = ? "
        "ORDER BY pr.created_at DESC LIMIT 30",
        (lot_id,)
    ).fetchall()
    conn.close()
    records = [dict(r) for r in rows]
    return render_template('parking_history.html', records=records, lot=lot)


# ---------------------------------------------------------------------------
# Reports (Admin)
# ---------------------------------------------------------------------------
@app.route('/admin/reports')
@admin_required
def reports():
    service = ParkingService()
    lot = service.get_lot_for_user(session['user_id'])
    lot_id = lot['lot_id']
    report_svc = ReportService()
    revenue = report_svc.get_revenue_summary(lot_id=lot_id)
    occupancy = report_svc.get_occupancy_summary(lot_id=lot_id)
    breakdown = report_svc.get_payment_breakdown(lot_id=lot_id)
    return render_template('reports.html', revenue=revenue, occupancy=occupancy, breakdown=breakdown, lot=lot)


# ---------------------------------------------------------------------------
# Worker Management (Admin)
# ---------------------------------------------------------------------------
@app.route('/admin/workers', methods=['GET', 'POST'])
@admin_required
def manage_workers():
    if request.method == 'POST':
        try:
            username = request.form['username'].strip()
            full_name = request.form['full_name'].strip()
            password = request.form['password']
            if not username or not full_name or not password:
                raise ValueError("All fields are required.")
            WorkerManagementService().create_worker(username, password, full_name, created_by=session['user_id'])
            flash(f"Worker '{username}' created successfully!", 'success')
            return redirect(url_for('manage_workers'))
        except Exception as exc:
            flash(str(exc), 'error')
    workers = WorkerManagementService().list_workers(admin_id=session['user_id'])
    return render_template('manage_workers.html', workers=workers)


@app.route('/admin/workers/get-password', methods=['POST'])
@admin_required
def get_worker_password():
    data = request.get_json() or {}
    worker_id = data.get('worker_id')
    admin_password = data.get('admin_password', '').strip()

    if not admin_password:
        return jsonify({'error': 'Admin password is required.'}), 400

    auth_svc = AuthenticationService()
    if not auth_svc.verify_admin_password(session['user_id'], admin_password):
        return jsonify({'error': 'Incorrect admin password. Verification failed.'}), 403

    conn = get_connection()
    admin_id = session['user_id']
    if admin_id == 1:
        row = conn.execute(
            "SELECT user_id, username, plain_password FROM users WHERE user_id = ? AND role = 'WORKER' AND (created_by = 1 OR created_by IS NULL)",
            (worker_id,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT user_id, username, plain_password FROM users WHERE user_id = ? AND role = 'WORKER' AND created_by = ?",
            (worker_id, admin_id)
        ).fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Worker not found or not managed by you.'}), 404

    return jsonify({
        'success': True,
        'username': row['username'],
        'password': row['plain_password'] or '(Set a new password below)'
    })


@app.route('/admin/workers/update-password', methods=['POST'])
@admin_required
def update_worker_password():
    data = request.get_json() or {}
    worker_id = data.get('worker_id')
    admin_password = data.get('admin_password', '').strip()
    new_password = data.get('new_password', '').strip()

    if not admin_password or not new_password:
        return jsonify({'error': 'Admin password and new password are required.'}), 400

    auth_svc = AuthenticationService()
    if not auth_svc.verify_admin_password(session['user_id'], admin_password):
        return jsonify({'error': 'Incorrect admin password. Verification failed.'}), 403

    if len(new_password) < 4:
        return jsonify({'error': 'New password must be at least 4 characters long.'}), 400

    conn = get_connection()
    admin_id = session['user_id']
    if admin_id == 1:
        row = conn.execute(
            "SELECT user_id FROM users WHERE user_id = ? AND role = 'WORKER' AND (created_by = 1 OR created_by IS NULL)",
            (worker_id,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT user_id FROM users WHERE user_id = ? AND role = 'WORKER' AND created_by = ?",
            (worker_id, admin_id)
        ).fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Worker not found or not managed by you.'}), 404

    try:
        auth_svc.update_password(worker_id, new_password)
        return jsonify({'success': True, 'message': 'Worker password updated successfully!'})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# Worker Dashboard
# ---------------------------------------------------------------------------
@app.route('/worker/dashboard')
@login_required
def worker_dashboard():
    service = ParkingService()
    lot = service.get_lot_for_user(session['user_id'])
    lot_id = lot['lot_id']

    conn = get_connection()
    car_total = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'CAR' AND is_active = 1", (lot_id,)).fetchone()[0]
    bike_total = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'BIKE' AND is_active = 1", (lot_id,)).fetchone()[0]
    car_occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'CAR' AND occupancy_status = 'OCCUPIED' AND is_active = 1", (lot_id,)).fetchone()[0]
    bike_occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ? AND slot_type = 'BIKE' AND occupancy_status = 'OCCUPIED' AND is_active = 1", (lot_id,)).fetchone()[0]
    car_available = car_total - car_occupied
    bike_available = bike_total - bike_occupied
    total_slots = car_total + bike_total
    free_slots = car_available + bike_available
    parked = conn.execute("SELECT COUNT(*) FROM parking_records pr JOIN parking_slots s ON s.slot_id = pr.slot_id WHERE s.lot_id = ? AND pr.parking_status = 'ACTIVE'", (lot_id,)).fetchone()[0]

    stats = {
        'car_total': car_total,
        'car_occupied': car_occupied,
        'car_available': car_available,
        'bike_total': bike_total,
        'bike_occupied': bike_occupied,
        'bike_available': bike_available,
        'total_slots': total_slots,
        'free_slots': free_slots,
        'parked': parked,
    }

    slots = [dict(r) for r in conn.execute(
        "SELECT slot_number, slot_type, occupancy_status FROM parking_slots WHERE lot_id = ? AND is_active = 1 ORDER BY slot_type, slot_number",
        (lot_id,)
    ).fetchall()]

    activity_rows = conn.execute(
        "SELECT pr.ticket_id, v.vehicle_number, pr.parking_status, pr.entry_time "
        "FROM parking_records pr "
        "JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "WHERE s.lot_id = ? "
        "ORDER BY pr.created_at DESC LIMIT 6",
        (lot_id,)
    ).fetchall()
    conn.close()
    recent = [dict(r) for r in activity_rows]
    return render_template('worker_dashboard.html', stats=stats, slots=slots, recent=recent, lot=lot)


# ---------------------------------------------------------------------------
# Vehicle Entry (Worker)
# ---------------------------------------------------------------------------
@app.route('/worker/vehicle-entry', methods=['GET', 'POST'])
@login_required
def vehicle_entry():
    result = None
    if request.method == 'POST':
        try:
            vehicle_number = request.form['vehicle_number'].strip()
            owner_name = request.form['owner_name'].strip()
            vehicle_type = request.form['vehicle_type'].upper()

            if not vehicle_number or not owner_name:
                raise ValueError("Vehicle number and owner name are required.")

            service = ParkingService()
            lot = service.get_lot_for_user(session['user_id'])

            vehicle_id = service.create_vehicle(vehicle_number, owner_name, vehicle_type)
            active = service.get_active_record_for_vehicle_in_lot(vehicle_number, lot['lot_id'])
            if active:
                raise ValueError("This vehicle already has an active parking session in this facility.")

            slot = SlotAllocationService().allocate_slot(lot['lot_id'], vehicle_type)
            conn = get_connection()
            rate_row = conn.execute(
                "SELECT hourly_rate FROM parking_rates WHERE lot_id = ? AND vehicle_type = ? AND is_active = 1 ORDER BY rate_id DESC LIMIT 1",
                (lot['lot_id'], vehicle_type),
            ).fetchone()
            conn.close()
            if rate_row is None:
                raise ValueError("Parking rate not configured for this vehicle type.")

            ticket_id = f"P{lot['lot_id']:02d}{vehicle_id:04d}"
            worker_id = session['user_id']
            service.create_parking_record(vehicle_id, slot['slot_id'], worker_id, rate_row['hourly_rate'], ticket_id)

            result = {
                'success': True,
                'ticket_id': ticket_id,
                'vehicle_number': vehicle_number,
                'owner_name': owner_name,
                'vehicle_type': vehicle_type,
                'slot_number': slot['slot_number'],
                'hourly_rate': rate_row['hourly_rate'],
            }
        except Exception as exc:
            flash(str(exc), 'error')
    return render_template('vehicle_entry.html', result=result)


# ---------------------------------------------------------------------------
# Vehicle Exit (Worker)
# ---------------------------------------------------------------------------
@app.route('/worker/vehicle-exit', methods=['GET'])
@login_required
def vehicle_exit():
    return render_template('vehicle_exit.html')


@app.route('/worker/vehicle-exit/search', methods=['POST'])
@login_required
def vehicle_exit_search():
    try:
        query = request.form.get('search_value', '').strip()
        if not query:
            return jsonify({'error': 'Enter ticket ID or vehicle number.'}), 400

        service = ParkingService()
        lot = service.get_lot_for_user(session['user_id'])
        record = service.get_record_by_ticket_in_lot(query, lot['lot_id'])
        if not record:
            record = service.get_record_by_vehicle_in_lot(query, lot['lot_id'])
        if not record:
            return jsonify({'error': 'No active parking record found in this facility.'}), 404

        conn = get_connection()
        vehicle = conn.execute(
            "SELECT vehicle_number, owner_name, vehicle_type FROM vehicles WHERE vehicle_id = ?",
            (record['vehicle_id'],)
        ).fetchone()
        slot = conn.execute(
            "SELECT slot_number FROM parking_slots WHERE slot_id = ?",
            (record['slot_id'],)
        ).fetchone()
        conn.close()

        return jsonify({
            'record_id': record['record_id'],
            'ticket_id': record['ticket_id'],
            'vehicle_number': vehicle['vehicle_number'],
            'owner_name': vehicle['owner_name'],
            'vehicle_type': vehicle['vehicle_type'],
            'slot_number': slot['slot_number'],
            'entry_time': record['entry_time'],
            'hourly_rate': record['applied_hourly_rate'],
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

        service = ParkingService()
        record = service.get_record_by_ticket(query)
        if not record:
            record = service.get_record_by_vehicle(query)
        if not record:
            return jsonify({'error': 'No active parking record found.'}), 404

        conn = get_connection()
        vehicle = conn.execute(
            "SELECT vehicle_number, owner_name, vehicle_type FROM vehicles WHERE vehicle_id = ?",
            (record['vehicle_id'],)
        ).fetchone()
        slot = conn.execute(
            "SELECT slot_number FROM parking_slots WHERE slot_id = ?",
            (record['slot_id'],)
        ).fetchone()
        conn.close()

        return jsonify({
            'record_id': record['record_id'],
            'ticket_id': record['ticket_id'],
            'vehicle_number': vehicle['vehicle_number'],
            'owner_name': vehicle['owner_name'],
            'vehicle_type': vehicle['vehicle_type'],
            'slot_number': slot['slot_number'],
            'entry_time': record['entry_time'],
            'hourly_rate': record['applied_hourly_rate'],
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/worker/vehicle-exit/process', methods=['POST'])
@login_required
def vehicle_exit_process():
    try:
        data = request.get_json()
        record_id = int(data['record_id'])
        payment_method = data['payment_method']
        entry_time = data['entry_time']
        hourly_rate = float(data['hourly_rate'])

        exit_time = datetime.now().isoformat(timespec='seconds')
        amount = FeeCalculator.calculate_fee(hourly_rate, entry_time, exit_time)
        worker_id = session['user_id']

        PaymentService().record_payment(record_id, float(amount), payment_method, worker_id, 'SUCCESS')
        ParkingService().complete_exit(record_id, worker_id, exit_time, hourly_rate)

        conn = get_connection()
        rec = conn.execute("SELECT ticket_id FROM parking_records WHERE record_id = ?", (record_id,)).fetchone()
        conn.close()
        ticket_id = rec['ticket_id'] if rec else ''

        return jsonify({
            'success': True,
            'ticket_id': ticket_id,
            'exit_time': exit_time,
            'amount': float(amount),
            'payment_method': payment_method,
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# Parking Slip & Exit Receipt Downloads / Printing
# ---------------------------------------------------------------------------
@app.route('/slip/entry/<ticket_id>')
@login_required
def entry_slip(ticket_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT pr.ticket_id, pr.entry_time, pr.applied_hourly_rate, "
        "v.vehicle_number, v.owner_name, v.vehicle_type, "
        "s.slot_number, u.full_name as attendant_name, l.lot_name, l.location "
        "FROM parking_records pr "
        "JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "JOIN parking_lots l ON l.lot_id = s.lot_id "
        "LEFT JOIN users u ON u.user_id = pr.entry_worker_id "
        "WHERE pr.ticket_id = ?",
        (ticket_id,)
    ).fetchone()
    conn.close()

    if not row:
        flash("Parking record not found.", "error")
        return redirect(url_for('parking_history'))

    slip_data = dict(row)

    if request.args.get('download'):
        slip_text = (
            "========================================\n"
            "     SMART PARKING LOT MANAGEMENT       \n"
            "========================================\n"
            f"Facility   : {slip_data['lot_name']} ({slip_data['location']})\n"
            f"Slip Type  : VEHICLE ENTRY SLIP\n"
            f"Ticket ID  : {slip_data['ticket_id']}\n"
            f"Entry Time : {slip_data['entry_time']}\n"
            "----------------------------------------\n"
            f"Vehicle No : {slip_data['vehicle_number']}\n"
            f"Owner Name : {slip_data['owner_name']}\n"
            f"Type       : {slip_data['vehicle_type']}\n"
            f"Slot No    : {slip_data['slot_number']}\n"
            f"Rate       : ₹{slip_data['applied_hourly_rate']} / hour\n"
            f"Attendant  : {slip_data['attendant_name'] or 'Staff'}\n"
            "----------------------------------------\n"
            "* Please retain this slip until exit.\n"
            "* Parking at vehicle owner's risk.\n"
            "========================================\n"
        )
        return Response(
            slip_text,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename=Parking_Slip_{ticket_id}.txt"}
        )

    return render_template('entry_slip_print.html', slip=slip_data)


@app.route('/slip/exit/<ticket_id>')
@login_required
def exit_receipt(ticket_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT pr.ticket_id, pr.entry_time, pr.exit_time, pr.chargeable_duration, pr.total_fee, "
        "pr.applied_hourly_rate, v.vehicle_number, v.owner_name, v.vehicle_type, "
        "s.slot_number, u.full_name as attendant_name, l.lot_name, l.location, "
        "p.amount as paid_amount, p.payment_method, p.payment_time "
        "FROM parking_records pr "
        "JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
        "JOIN parking_slots s ON s.slot_id = pr.slot_id "
        "JOIN parking_lots l ON l.lot_id = s.lot_id "
        "LEFT JOIN users u ON u.user_id = pr.exit_worker_id "
        "LEFT JOIN payments p ON p.record_id = pr.record_id AND p.payment_status = 'SUCCESS' "
        "WHERE pr.ticket_id = ?",
        (ticket_id,)
    ).fetchone()
    conn.close()

    if not row:
        flash("Exit record not found.", "error")
        return redirect(url_for('parking_history'))

    receipt_data = dict(row)

    if request.args.get('download'):
        receipt_text = (
            "========================================\n"
            "     SMART PARKING LOT MANAGEMENT       \n"
            "========================================\n"
            f"Facility   : {receipt_data['lot_name']} ({receipt_data['location']})\n"
            f"Slip Type  : PAYMENT & EXIT RECEIPT\n"
            f"Ticket ID  : {receipt_data['ticket_id']}\n"
            f"Exit Time  : {receipt_data['exit_time'] or '-'}\n"
            "----------------------------------------\n"
            f"Vehicle No : {receipt_data['vehicle_number']}\n"
            f"Owner Name : {receipt_data['owner_name']}\n"
            f"Type       : {receipt_data['vehicle_type']}\n"
            f"Slot No    : {receipt_data['slot_number']}\n"
            f"Entry Time : {receipt_data['entry_time']}\n"
            f"Duration   : {receipt_data['chargeable_duration']} hour(s)\n"
            f"Total Paid : ₹{receipt_data['paid_amount'] or receipt_data['total_fee']}\n"
            f"Method     : {receipt_data['payment_method'] or 'CASH'}\n"
            f"Processed  : {receipt_data['attendant_name'] or 'Staff'}\n"
            "----------------------------------------\n"
            "      Thank You! Visit Again.\n"
            "========================================\n"
        )
        return Response(
            receipt_text,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename=Exit_Receipt_{ticket_id}.txt"}
        )

    return render_template('exit_receipt_print.html', receipt=receipt_data)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
