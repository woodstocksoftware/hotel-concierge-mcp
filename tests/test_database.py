"""
Tests for src/hotel_concierge/database.py

Covers:
- Database initialization (tables, sample data)
- get_room_types()
- check_availability()
- make_reservation()
- get_reservation()
- cancel_reservation()
- submit_service_request()
- get_hotel_info()
"""

import json
import sqlite3
from datetime import datetime, timedelta

import pytest

from src.hotel_concierge import database as db


# ============================================================
# Database initialization
# ============================================================

class TestInitDatabase:
    """Verify schema creation and sample data seeding."""

    def test_tables_exist(self, temp_database):
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = sorted(row[0] for row in cursor.fetchall())
        conn.close()
        assert "hotel_info" in tables
        assert "reservations" in tables
        assert "room_types" in tables
        assert "rooms" in tables
        assert "service_requests" in tables

    def test_room_types_seeded(self):
        room_types = db.get_room_types()
        assert len(room_types) == 4
        ids = {rt["id"] for rt in room_types}
        assert ids == {"standard", "deluxe", "suite", "family"}

    def test_rooms_seeded(self, temp_database):
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rooms")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 20  # 5 rooms per floor * 4 floors

    def test_sample_reservations_seeded(self, temp_database):
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reservations")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 3

    def test_hotel_info_seeded(self, temp_database):
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hotel_info")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 17  # 17 key-value pairs

    def test_idempotent_init(self, temp_database):
        """Calling init_database() again should not duplicate data."""
        db.init_database()
        room_types = db.get_room_types()
        assert len(room_types) == 4


# ============================================================
# get_room_types()
# ============================================================

class TestGetRoomTypes:

    def test_returns_all_types(self):
        result = db.get_room_types()
        assert len(result) == 4

    def test_room_type_fields(self):
        result = db.get_room_types()
        for rt in result:
            assert "id" in rt
            assert "name" in rt
            assert "description" in rt
            assert "base_rate" in rt
            assert "max_occupancy" in rt
            assert "amenities" in rt
            # amenities is a JSON string
            parsed = json.loads(rt["amenities"])
            assert isinstance(parsed, list)
            assert len(parsed) > 0

    def test_standard_rate(self):
        result = {rt["id"]: rt for rt in db.get_room_types()}
        assert result["standard"]["base_rate"] == 149.00

    def test_suite_rate(self):
        result = {rt["id"]: rt for rt in db.get_room_types()}
        assert result["suite"]["base_rate"] == 399.00

    def test_max_occupancy_values(self):
        result = {rt["id"]: rt for rt in db.get_room_types()}
        assert result["standard"]["max_occupancy"] == 2
        assert result["deluxe"]["max_occupancy"] == 2
        assert result["suite"]["max_occupancy"] == 4
        assert result["family"]["max_occupancy"] == 4


# ============================================================
# check_availability()
# ============================================================

class TestCheckAvailability:

    def test_returns_available_rooms(self, future_dates):
        check_in, check_out = future_dates
        result = db.check_availability(check_in, check_out)
        assert len(result) > 0

    def test_filter_by_room_type(self, future_dates):
        check_in, check_out = future_dates
        result = db.check_availability(check_in, check_out, room_type="suite")
        for room in result:
            assert room["room_type_id"] == "suite"

    def test_invalid_room_type_returns_empty(self, future_dates):
        check_in, check_out = future_dates
        result = db.check_availability(check_in, check_out, room_type="penthouse")
        assert result == []

    def test_room_fields_present(self, future_dates):
        check_in, check_out = future_dates
        result = db.check_availability(check_in, check_out)
        room = result[0]
        assert "room_number" in room
        assert "room_type_id" in room
        assert "room_type_name" in room
        assert "base_rate" in room
        assert "max_occupancy" in room
        assert "amenities" in room

    def test_occupied_room_excluded(self, temp_database):
        """Room 301 is assigned to CONF001 (checked_in) -- should be excluded
        for overlapping dates."""
        # CONF001 dates overlap with today-1 to today+2
        today = datetime.now().date()
        check_in = str(today)
        check_out = str(today + timedelta(days=1))
        result = db.check_availability(check_in, check_out)
        room_numbers = [r["room_number"] for r in result]
        assert "301" not in room_numbers


# ============================================================
# make_reservation()
# ============================================================

class TestMakeReservation:

    def test_creates_reservation(self, future_dates):
        check_in, check_out = future_dates
        result = db.make_reservation(
            guest_name="Test Guest",
            guest_email="test@example.com",
            guest_phone="555-9999",
            room_type_id="standard",
            check_in=check_in,
            check_out=check_out,
            num_guests=1,
        )
        assert result["confirmation_number"].startswith("CONF")
        assert len(result["confirmation_number"]) == 10  # CONF + 6 chars
        assert result["guest_name"] == "Test Guest"
        assert result["status"] == "confirmed"

    def test_total_amount_calculated(self, future_dates):
        check_in, check_out = future_dates
        result = db.make_reservation(
            guest_name="Price Test",
            guest_email="price@test.com",
            guest_phone="555-0000",
            room_type_id="standard",
            check_in=check_in,
            check_out=check_out,
        )
        # 2 nights at $149/night = $298
        assert result["total_amount"] == 298.00
        assert result["nights"] == 2

    def test_reservation_persists(self, future_dates):
        check_in, check_out = future_dates
        result = db.make_reservation(
            guest_name="Persist Test",
            guest_email="persist@test.com",
            guest_phone="555-1111",
            room_type_id="deluxe",
            check_in=check_in,
            check_out=check_out,
        )
        fetched = db.get_reservation(result["confirmation_number"])
        assert fetched is not None
        assert fetched["guest_name"] == "Persist Test"
        assert fetched["status"] == "confirmed"

    def test_special_requests_stored(self, future_dates):
        check_in, check_out = future_dates
        result = db.make_reservation(
            guest_name="Special Req",
            guest_email="special@test.com",
            guest_phone="555-2222",
            room_type_id="standard",
            check_in=check_in,
            check_out=check_out,
            special_requests="Extra pillows please",
        )
        fetched = db.get_reservation(result["confirmation_number"])
        assert fetched["special_requests"] == "Extra pillows please"


# ============================================================
# get_reservation()
# ============================================================

class TestGetReservation:

    def test_existing_reservation(self, sample_confirmed_conf):
        result = db.get_reservation(sample_confirmed_conf)
        assert result is not None
        assert result["guest_name"] == "Sarah Johnson"

    def test_nonexistent_reservation(self):
        result = db.get_reservation("CONFXXXXXX")
        assert result is None

    def test_case_insensitive_lookup(self, sample_confirmed_conf):
        result = db.get_reservation(sample_confirmed_conf.lower())
        assert result is not None

    def test_reservation_fields(self, sample_confirmed_conf):
        result = db.get_reservation(sample_confirmed_conf)
        expected_fields = [
            "confirmation_number",
            "guest_name",
            "guest_email",
            "guest_phone",
            "room_type_id",
            "check_in_date",
            "check_out_date",
            "num_guests",
            "status",
            "total_amount",
            "special_requests",
            "room_type_name",
            "base_rate",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_checked_in_reservation(self, sample_checked_in_conf):
        result = db.get_reservation(sample_checked_in_conf)
        assert result["status"] == "checked_in"
        assert result["room_number"] == "301"


# ============================================================
# cancel_reservation()
# ============================================================

class TestCancelReservation:

    def test_cancel_confirmed(self, sample_confirmed_conf):
        success = db.cancel_reservation(sample_confirmed_conf)
        assert success is True
        result = db.get_reservation(sample_confirmed_conf)
        assert result["status"] == "cancelled"

    def test_cancel_nonexistent(self):
        success = db.cancel_reservation("CONFXXXXXX")
        assert success is False

    def test_cancel_already_cancelled(self, sample_confirmed_conf):
        db.cancel_reservation(sample_confirmed_conf)
        # Second cancel should fail (only 'confirmed' -> 'cancelled')
        success = db.cancel_reservation(sample_confirmed_conf)
        assert success is False

    def test_cancel_checked_in_fails(self, sample_checked_in_conf):
        """Cannot cancel via DB function -- only 'confirmed' status is updated."""
        success = db.cancel_reservation(sample_checked_in_conf)
        assert success is False

    def test_case_insensitive_cancel(self, sample_confirmed_conf):
        success = db.cancel_reservation(sample_confirmed_conf.lower())
        assert success is True


# ============================================================
# submit_service_request()
# ============================================================

class TestSubmitServiceRequest:

    def test_submit_for_confirmed(self, sample_confirmed_conf):
        result = db.submit_service_request(
            sample_confirmed_conf, "room_service", "Extra towels please"
        )
        assert result is not None
        assert result["request_type"] == "room_service"
        assert result["status"] == "pending"
        assert result["request_id"] > 0

    def test_submit_for_checked_in(self, sample_checked_in_conf):
        result = db.submit_service_request(
            sample_checked_in_conf, "housekeeping", "Clean room"
        )
        assert result is not None

    def test_submit_for_nonexistent(self):
        result = db.submit_service_request(
            "CONFXXXXXX", "concierge", "Restaurant recommendation"
        )
        assert result is None

    def test_submit_for_cancelled(self, sample_confirmed_conf):
        db.cancel_reservation(sample_confirmed_conf)
        result = db.submit_service_request(
            sample_confirmed_conf, "room_service", "Something"
        )
        assert result is None

    def test_case_insensitive(self, sample_confirmed_conf):
        result = db.submit_service_request(
            sample_confirmed_conf.lower(), "maintenance", "Broken lamp"
        )
        assert result is not None

    def test_request_persists(self, sample_confirmed_conf, temp_database):
        result = db.submit_service_request(
            sample_confirmed_conf, "concierge", "Book tour"
        )
        conn = sqlite3.connect(temp_database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM service_requests WHERE id = ?", (result["request_id"],)
        )
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        assert row["description"] == "Book tour"


# ============================================================
# get_hotel_info()
# ============================================================

class TestGetHotelInfo:

    def test_get_all_info(self):
        result = db.get_hotel_info()
        assert isinstance(result, dict)
        assert result["name"] == "The Grand Azure Hotel"
        assert "check_in_time" in result
        assert "check_out_time" in result

    def test_get_specific_key(self):
        result = db.get_hotel_info("parking")
        assert isinstance(result, str)
        assert "parking" in result.lower() or "$" in result

    def test_get_nonexistent_key(self):
        result = db.get_hotel_info("nonexistent_topic")
        assert result is None

    def test_local_attractions_parsed_as_list(self):
        result = db.get_hotel_info("local_attractions")
        assert isinstance(result, list)
        assert len(result) == 4
        assert result[0]["name"] == "Seaside Pier"

    def test_all_info_keys_present(self):
        result = db.get_hotel_info()
        expected_keys = [
            "name", "address", "phone", "email",
            "check_in_time", "check_out_time",
            "early_check_in", "late_check_out",
            "cancellation_policy", "parking", "wifi",
            "pool", "fitness", "spa", "restaurant",
            "room_service", "local_attractions",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
