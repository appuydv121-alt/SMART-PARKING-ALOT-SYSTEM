import pytest
from app import app
from database.connection import initialize_database
from database.seed import seed_default_data


@pytest.fixture
def client():
    app.config['TESTING'] = True
    initialize_database()
    seed_default_data()
    with app.test_client() as client:
        yield client


def test_login_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"SMART PARKING" in response.data
    assert b"Welcome back" in response.data


def test_login_flow_admin(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data


def test_login_failure(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_admin_dashboard_requires_login(client):
    response = client.get('/admin/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_worker_vehicle_entry_and_exit_flow(client):
    # 1. Login as admin first to configure lot rates
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

    # Configure lot
    client.post('/admin/parking-setup', data={
        'lot_name': 'City Parking',
        'location': 'Main Market',
        'car_capacity': 10,
        'bike_capacity': 10,
        'car_rate': 30,
        'bike_rate': 15
    }, follow_redirects=True)

    # 2. Register vehicle entry
    entry_resp = client.post('/worker/vehicle-entry', data={
        'vehicle_number': 'MH12AB1234',
        'owner_name': 'Rahul Sharma',
        'vehicle_type': 'CAR'
    }, follow_redirects=True)
    assert entry_resp.status_code == 200
    assert b"Vehicle Registered Successfully" in entry_resp.data
    assert b"MH12AB1234" in entry_resp.data

    # 3. Search for vehicle in exit screen
    search_resp = client.post('/worker/vehicle-exit/search', data={'search_value': 'MH12AB1234'})
    assert search_resp.status_code == 200
    record_data = search_resp.get_json()
    assert record_data['vehicle_number'] == 'MH12AB1234'
    record_id = record_data['record_id']

    # 4. Process vehicle exit with an entry from 1 hour prior
    exit_resp = client.post('/worker/vehicle-exit/process', json={
        'record_id': record_id,
        'payment_method': 'CASH',
        'entry_time': '2026-11-05T00:00:00',
        'hourly_rate': record_data['hourly_rate']
    })
    assert exit_resp.status_code == 200
    res_json = exit_resp.get_json()
    assert res_json['success'] is True
    assert res_json['amount'] >= 30.0


def test_single_lot_modification_and_slot_count(client):
    # 1. Login as admin
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

    # 2. Update the single lot to 4 cars and 5 bikes
    setup_resp = client.post('/admin/parking-setup', data={
        'lot_name': 'Super City Parking',
        'location': 'Downtown Indore',
        'car_capacity': 4,
        'bike_capacity': 5,
        'car_rate': 40,
        'bike_rate': 20
    }, follow_redirects=True)
    assert setup_resp.status_code == 200
    assert b"Super City Parking" in setup_resp.data
    assert b"updated successfully" in setup_resp.data

    # 3. Check slot management displays exact counts
    slot_resp = client.get('/admin/slots')
    assert slot_resp.status_code == 200
    assert b"Super City Parking" in slot_resp.data
    assert b"Cars: 4 Slots" in slot_resp.data
    assert b"Bikes: 5 Slots" in slot_resp.data
    assert b"Total: 9 Slots" in slot_resp.data
    assert b"C-04" in slot_resp.data
    assert b"B-05" in slot_resp.data
    assert b"C-05" not in slot_resp.data
    assert b"B-06" not in slot_resp.data


def test_registration_flow(client):
    # 1. Register a new user
    reg_resp = client.post('/register', data={
        'full_name': 'Rohit Verma',
        'username': 'rohit_worker',
        'role': 'WORKER',
        'password': 'secretpassword',
        'confirm_password': 'secretpassword'
    }, follow_redirects=True)
    assert reg_resp.status_code == 200
    assert b"Account created successfully" in reg_resp.data

    # 2. Login with newly registered user
    login_resp = client.post('/login', data={
        'username': 'rohit_worker',
        'password': 'secretpassword'
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Worker Dashboard" in login_resp.data


def test_slip_download_and_view(client):
    # 1. Login as admin and create vehicle entry
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    client.post('/admin/parking-setup', data={
        'lot_name': 'City Center',
        'location': 'Central Plaza',
        'car_capacity': 5,
        'bike_capacity': 5,
        'car_rate': 30,
        'bike_rate': 15
    }, follow_redirects=True)

    entry_resp = client.post('/worker/vehicle-entry', data={
        'vehicle_number': 'DL01XY9999',
        'owner_name': 'Amit Singh',
        'vehicle_type': 'CAR'
    }, follow_redirects=True)
    assert entry_resp.status_code == 200

    from database.connection import get_connection
    conn = get_connection()
    rec = conn.execute("SELECT ticket_id FROM parking_records ORDER BY record_id DESC LIMIT 1").fetchone()
    conn.close()
    ticket_id = rec['ticket_id']

    # 2. Test downloading slip as text attachment
    download_resp = client.get(f'/slip/entry/{ticket_id}?download=1')
    assert download_resp.status_code == 200
    assert download_resp.mimetype == 'text/plain'
    assert b"VEHICLE ENTRY SLIP" in download_resp.data
    assert b"DL01XY9999" in download_resp.data

    # 3. Test viewing printable slip HTML
    view_resp = client.get(f'/slip/entry/{ticket_id}')
    assert view_resp.status_code == 200
    assert b"Print Slip" in view_resp.data


def test_worker_password_reveal_and_update(client):
    # 1. Login as admin
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

    # 2. Create worker
    client.post('/admin/workers', data={
        'username': 'ram_worker',
        'full_name': 'Ram Kumar',
        'password': 'mypassword123'
    }, follow_redirects=True)

    from database.connection import get_connection
    conn = get_connection()
    worker = conn.execute("SELECT user_id FROM users WHERE username = 'ram_worker'").fetchone()
    conn.close()
    worker_id = worker['user_id']

    # 3. Try to view password with wrong admin password -> should fail
    fail_resp = client.post('/admin/workers/get-password', json={
        'worker_id': worker_id,
        'admin_password': 'wrongadminpassword'
    })
    assert fail_resp.status_code == 403

    # 4. View password with correct admin password -> should succeed
    succ_resp = client.post('/admin/workers/get-password', json={
        'worker_id': worker_id,
        'admin_password': 'admin123'
    })
    assert succ_resp.status_code == 200
    assert succ_resp.get_json()['password'] == 'mypassword123'

    # 5. Change worker password
    update_resp = client.post('/admin/workers/update-password', json={
        'worker_id': worker_id,
        'admin_password': 'admin123',
        'new_password': 'newpassword456'
    })
    assert update_resp.status_code == 200
    assert update_resp.get_json()['success'] is True

    # 6. Verify worker can login with new password
    client.get('/logout')
    login_resp = client.post('/login', data={
        'username': 'ram_worker',
        'password': 'newpassword456'
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Worker Dashboard" in login_resp.data


def test_slip_download_and_view(client):
    # 1. Login as admin and create vehicle entry
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    client.post('/admin/parking-setup', data={
        'lot_name': 'City Center',
        'location': 'Central Plaza',
        'car_capacity': 5,
        'bike_capacity': 5,
        'car_rate': 30,
        'bike_rate': 15
    }, follow_redirects=True)

    entry_resp = client.post('/worker/vehicle-entry', data={
        'vehicle_number': 'DL01XY9999',
        'owner_name': 'Amit Singh',
        'vehicle_type': 'CAR'
    }, follow_redirects=True)
    assert entry_resp.status_code == 200

    from database.connection import get_connection
    conn = get_connection()
    rec = conn.execute("SELECT ticket_id FROM parking_records ORDER BY record_id DESC LIMIT 1").fetchone()
    conn.close()
    ticket_id = rec['ticket_id']

    # 2. Test downloading slip as text attachment
    download_resp = client.get(f'/slip/entry/{ticket_id}?download=1')
    assert download_resp.status_code == 200
    assert download_resp.mimetype == 'text/plain'
    assert b"VEHICLE ENTRY SLIP" in download_resp.data
    assert b"DL01XY9999" in download_resp.data

    # 3. Test viewing printable slip HTML
    view_resp = client.get(f'/slip/entry/{ticket_id}')
    assert view_resp.status_code == 200
    assert b"Print Slip" in view_resp.data


def test_admin_isolation_multi_tenant(client):
    # 1. Admin 1 logs in and parks a vehicle
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    client.post('/admin/parking-setup', data={
        'lot_name': 'Admin 1 Facility',
        'location': 'Sector 1',
        'car_capacity': 2,
        'bike_capacity': 3,
        'car_rate': 30,
        'bike_rate': 15
    }, follow_redirects=True)
    entry_resp = client.post('/worker/vehicle-entry', data={
        'vehicle_number': 'MH12AB1234',
        'owner_name': 'Arpit Yadav',
        'vehicle_type': 'CAR'
    }, follow_redirects=True)
    assert entry_resp.status_code == 200

    # Admin 1 dashboard shows 1 occupied slot and vehicle
    dash1 = client.get('/admin/dashboard')
    assert b"FILLED" in dash1.data
    assert b"MH12AB1234" in dash1.data
    client.get('/logout')

    # 2. Register Admin 2
    reg_resp = client.post('/register', data={
        'full_name': 'New Admin 2',
        'username': 'admin2',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'ADMIN'
    }, follow_redirects=True)
    assert reg_resp.status_code == 200

    # 3. Admin 2 logs in
    login_resp = client.post('/login', data={'username': 'admin2', 'password': 'password123'}, follow_redirects=True)
    assert login_resp.status_code == 200

    # 4. Admin 2 dashboard MUST NOT show Admin 1's parked car or occupied slots
    dash2 = client.get('/admin/dashboard')
    assert b"FILLED" not in dash2.data
    assert b"MH12AB1234" not in dash2.data
    assert b"Occupied: <strong>0</strong>" in dash2.data

    # 5. Admin 2 worker management should not show Admin 1's workers
    workers_resp = client.get('/admin/workers')
    assert b"worker1" not in workers_resp.data




