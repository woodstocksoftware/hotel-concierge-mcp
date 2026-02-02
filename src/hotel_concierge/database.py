"""
Hotel database with mock data.
Uses SQLite for simplicity - easily swappable for a real PMS.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path


DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "hotel.db"


def get_connection():
    """Get database connection."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with schema and sample data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript("""
        -- Room types
        CREATE TABLE IF NOT EXISTS room_types (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            base_rate REAL NOT NULL,
            max_occupancy INTEGER NOT NULL,
            amenities TEXT  -- JSON array
        );
        
        -- Rooms
        CREATE TABLE IF NOT EXISTS rooms (
            room_number TEXT PRIMARY KEY,
            room_type_id TEXT NOT NULL,
            floor INTEGER NOT NULL,
            status TEXT DEFAULT 'available',  -- available, occupied, maintenance
            FOREIGN KEY (room_type_id) REFERENCES room_types(id)
        );
        
        -- Reservations
        CREATE TABLE IF NOT EXISTS reservations (
            confirmation_number TEXT PRIMARY KEY,
            guest_name TEXT NOT NULL,
            guest_email TEXT,
            guest_phone TEXT,
            room_number TEXT,
            room_type_id TEXT NOT NULL,
            check_in_date TEXT NOT NULL,
            check_out_date TEXT NOT NULL,
            num_guests INTEGER DEFAULT 1,
            status TEXT DEFAULT 'confirmed',  -- confirmed, checked_in, checked_out, cancelled
            total_amount REAL,
            special_requests TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_number) REFERENCES rooms(room_number),
            FOREIGN KEY (room_type_id) REFERENCES room_types(id)
        );
        
        -- Service requests
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            confirmation_number TEXT NOT NULL,
            request_type TEXT NOT NULL,  -- room_service, housekeeping, maintenance, concierge
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',  -- pending, in_progress, completed
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY (confirmation_number) REFERENCES reservations(confirmation_number)
        );
        
        -- Hotel information
        CREATE TABLE IF NOT EXISTS hotel_info (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM room_types")
    if cursor.fetchone()[0] == 0:
        _insert_sample_data(cursor)
    
    conn.commit()
    conn.close()


def _insert_sample_data(cursor):
    """Insert sample hotel data."""
    
    # Room types
    room_types = [
        ("standard", "Standard Room", "Comfortable room with queen bed, work desk, and city view.", 149.00, 2,
         json.dumps(["Queen Bed", "Work Desk", "40\" TV", "WiFi", "Coffee Maker"])),
        ("deluxe", "Deluxe Room", "Spacious room with king bed, sitting area, and premium amenities.", 219.00, 2,
         json.dumps(["King Bed", "Sitting Area", "55\" TV", "WiFi", "Mini Bar", "Nespresso Machine"])),
        ("suite", "Executive Suite", "Luxurious suite with separate living room, bedroom, and panoramic views.", 399.00, 4,
         json.dumps(["King Bed", "Living Room", "Dining Area", "65\" TV", "WiFi", "Full Bar", "Jacuzzi Tub", "Balcony"])),
        ("family", "Family Room", "Large room with two queen beds, perfect for families.", 249.00, 4,
         json.dumps(["Two Queen Beds", "Sofa Bed", "50\" TV", "WiFi", "Mini Fridge", "Microwave"])),
    ]
    cursor.executemany(
        "INSERT INTO room_types (id, name, description, base_rate, max_occupancy, amenities) VALUES (?, ?, ?, ?, ?, ?)",
        room_types
    )
    
    # Rooms (3 of each type across floors 2-5)
    rooms = []
    room_num = 200
    for floor in range(2, 6):
        for room_type in ["standard", "standard", "deluxe", "suite", "family"]:
            room_num += 1
            rooms.append((str(room_num), room_type, floor, "available"))
    
    cursor.executemany(
        "INSERT INTO rooms (room_number, room_type_id, floor, status) VALUES (?, ?, ?, ?)",
        rooms
    )
    
    # Sample reservations
    today = datetime.now().date()
    reservations = [
        ("CONF001", "John Smith", "john.smith@email.com", "555-0101", "301", "deluxe",
         str(today - timedelta(days=1)), str(today + timedelta(days=2)), 2, "checked_in", 657.00, "Late checkout requested"),
        ("CONF002", "Sarah Johnson", "sarah.j@email.com", "555-0102", None, "suite",
         str(today + timedelta(days=3)), str(today + timedelta(days=5)), 2, "confirmed", 798.00, "Anniversary celebration"),
        ("CONF003", "The Williams Family", "williams@email.com", "555-0103", None, "family",
         str(today + timedelta(days=1)), str(today + timedelta(days=4)), 4, "confirmed", 747.00, "Need crib for infant"),
    ]
    cursor.executemany(
        """INSERT INTO reservations 
           (confirmation_number, guest_name, guest_email, guest_phone, room_number, room_type_id,
            check_in_date, check_out_date, num_guests, status, total_amount, special_requests)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        reservations
    )
    
    # Hotel information
    hotel_info = [
        ("name", "The Grand Azure Hotel"),
        ("address", "123 Oceanview Boulevard, Seaside City, CA 90210"),
        ("phone", "1-800-555-AZURE"),
        ("email", "info@grandazure.com"),
        ("check_in_time", "3:00 PM"),
        ("check_out_time", "11:00 AM"),
        ("early_check_in", "Early check-in available from 12:00 PM for $50 (subject to availability)"),
        ("late_check_out", "Late check-out until 2:00 PM for $50 (subject to availability)"),
        ("cancellation_policy", "Free cancellation up to 48 hours before check-in. One night charge for late cancellation."),
        ("parking", "Valet parking: $35/night. Self-parking: $25/night."),
        ("wifi", "Complimentary high-speed WiFi throughout the hotel."),
        ("pool", "Rooftop pool open 6:00 AM - 10:00 PM daily. Towels provided."),
        ("fitness", "24-hour fitness center on Level 3. Complimentary for all guests."),
        ("spa", "Azure Spa open 9:00 AM - 9:00 PM. Reservations recommended."),
        ("restaurant", "The Azure Table: Breakfast 6:30-10:30 AM, Dinner 5:30-10:00 PM. Smart casual dress code."),
        ("room_service", "24-hour room service available. Menu in room or dial 0."),
        ("local_attractions", json.dumps([
            {"name": "Seaside Pier", "distance": "0.3 miles", "description": "Historic pier with shops and restaurants"},
            {"name": "Ocean View Beach", "distance": "0.1 miles", "description": "Sandy beach with lifeguards"},
            {"name": "Maritime Museum", "distance": "0.5 miles", "description": "Local history and marine exhibits"},
            {"name": "Downtown Shopping District", "distance": "1.2 miles", "description": "Boutiques, galleries, and dining"},
        ])),
    ]
    cursor.executemany("INSERT INTO hotel_info (key, value) VALUES (?, ?)", hotel_info)


# Initialize on import
init_database()


# Query functions
def get_room_types():
    """Get all room types with details."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM room_types")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def check_availability(check_in: str, check_out: str, room_type: str = None):
    """Check room availability for given dates."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Find rooms not reserved during these dates
    query = """
        SELECT r.room_number, r.floor, rt.id as room_type_id, rt.name as room_type_name, 
               rt.base_rate, rt.max_occupancy, rt.amenities
        FROM rooms r
        JOIN room_types rt ON r.room_type_id = rt.id
        WHERE r.status = 'available'
        AND r.room_number NOT IN (
            SELECT room_number FROM reservations
            WHERE room_number IS NOT NULL
            AND status IN ('confirmed', 'checked_in')
            AND check_in_date < ? AND check_out_date > ?
        )
    """
    params = [check_out, check_in]
    
    if room_type:
        query += " AND rt.id = ?"
        params.append(room_type)
    
    query += " ORDER BY rt.base_rate, r.room_number"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def make_reservation(guest_name: str, guest_email: str, guest_phone: str,
                     room_type_id: str, check_in: str, check_out: str,
                     num_guests: int = 1, special_requests: str = None):
    """Create a new reservation."""
    import random
    import string
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate confirmation number
    conf_num = "CONF" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Calculate nights and total
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
    nights = (check_out_date - check_in_date).days
    
    cursor.execute("SELECT base_rate FROM room_types WHERE id = ?", (room_type_id,))
    rate = cursor.fetchone()["base_rate"]
    total = rate * nights
    
    cursor.execute("""
        INSERT INTO reservations 
        (confirmation_number, guest_name, guest_email, guest_phone, room_type_id,
         check_in_date, check_out_date, num_guests, total_amount, special_requests)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (conf_num, guest_name, guest_email, guest_phone, room_type_id,
          check_in, check_out, num_guests, total, special_requests))
    
    conn.commit()
    conn.close()
    
    return {
        "confirmation_number": conf_num,
        "guest_name": guest_name,
        "room_type": room_type_id,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "total_amount": total,
        "status": "confirmed"
    }


def get_reservation(confirmation_number: str):
    """Look up a reservation by confirmation number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, rt.name as room_type_name, rt.base_rate
        FROM reservations r
        JOIN room_types rt ON r.room_type_id = rt.id
        WHERE r.confirmation_number = ?
    """, (confirmation_number.upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def cancel_reservation(confirmation_number: str):
    """Cancel a reservation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE reservations SET status = 'cancelled'
        WHERE confirmation_number = ? AND status = 'confirmed'
    """, (confirmation_number.upper(),))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def submit_service_request(confirmation_number: str, request_type: str, description: str):
    """Submit a service request for a guest."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verify reservation exists and is active
    cursor.execute("""
        SELECT * FROM reservations 
        WHERE confirmation_number = ? AND status IN ('confirmed', 'checked_in')
    """, (confirmation_number.upper(),))
    
    if not cursor.fetchone():
        conn.close()
        return None
    
    cursor.execute("""
        INSERT INTO service_requests (confirmation_number, request_type, description)
        VALUES (?, ?, ?)
    """, (confirmation_number.upper(), request_type, description))
    
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "request_id": request_id,
        "confirmation_number": confirmation_number.upper(),
        "request_type": request_type,
        "description": description,
        "status": "pending"
    }


def get_hotel_info(key: str = None):
    """Get hotel information."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if key:
        cursor.execute("SELECT value FROM hotel_info WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            try:
                return json.loads(row["value"])
            except json.JSONDecodeError:
                return row["value"]
        return None
    else:
        cursor.execute("SELECT key, value FROM hotel_info")
        rows = cursor.fetchall()
        conn.close()
        result = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                result[row["key"]] = row["value"]
        return result


if __name__ == "__main__":
    # Test the database
    print("Room Types:")
    for rt in get_room_types():
        print(f"  - {rt['name']}: ${rt['base_rate']}/night")
    
    print("\nAvailability for next week:")
    from datetime import date, timedelta
    check_in = str(date.today() + timedelta(days=7))
    check_out = str(date.today() + timedelta(days=9))
    available = check_availability(check_in, check_out)
    print(f"  {len(available)} rooms available")
    
    print("\nHotel Info:")
    info = get_hotel_info()
    print(f"  {info['name']}")
    print(f"  Check-in: {info['check_in_time']}")
