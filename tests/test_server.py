"""
Tests for src/hotel_concierge/server.py

Covers all 7 MCP tools and 3 MCP resources:

Tools:
  1. check_availability
  2. make_reservation
  3. get_reservation
  4. cancel_reservation
  5. submit_service_request
  6. get_hotel_info
  7. get_room_types

Resources:
  1. hotel://info
  2. hotel://rooms
  3. hotel://attractions
"""

from datetime import datetime, timedelta

import pytest

from src.hotel_concierge.server import (
    cancel_reservation,
    check_availability,
    get_hotel_info,
    get_reservation,
    get_room_types,
    make_reservation,
    submit_service_request,
    # Resources
    hotel_info_resource,
    room_types_resource,
    attractions_resource,
)


# ============================================================
# Helper
# ============================================================

def _future(days_ahead: int) -> str:
    return str((datetime.now().date() + timedelta(days=days_ahead)))


# ============================================================
# Tool 1: check_availability
# ============================================================

class TestCheckAvailability:

    def test_returns_availability_text(self, future_dates):
        check_in, check_out = future_dates
        result = check_availability(check_in, check_out)
        assert "Availability for" in result
        assert "night" in result

    def test_filter_by_room_type(self, future_dates):
        check_in, check_out = future_dates
        result = check_availability(check_in, check_out, room_type="suite")
        assert "Executive Suite" in result

    def test_invalid_date_format(self):
        result = check_availability("not-a-date", "also-bad")
        assert "Error" in result
        assert "YYYY-MM-DD" in result

    def test_checkout_before_checkin(self, future_dates):
        check_in, check_out = future_dates
        result = check_availability(check_out, check_in)
        assert "Check-out date must be after check-in date" in result

    def test_same_date_checkin_checkout(self, future_dates):
        check_in, _ = future_dates
        result = check_availability(check_in, check_in)
        assert "Check-out date must be after check-in date" in result

    def test_past_checkin_date(self, past_date):
        checkout = _future(2)
        result = check_availability(past_date, checkout)
        assert "past" in result.lower()

    def test_shows_rate_and_total(self, future_dates):
        check_in, check_out = future_dates
        result = check_availability(check_in, check_out)
        assert "$" in result
        assert "Rate" in result
        assert "Total" in result

    def test_shows_max_occupancy(self, future_dates):
        check_in, check_out = future_dates
        result = check_availability(check_in, check_out)
        assert "Max Occupancy" in result

    def test_shows_amenities(self, future_dates):
        check_in, check_out = future_dates
        result = check_availability(check_in, check_out)
        assert "Amenities" in result

    def test_nonexistent_room_type(self, future_dates):
        check_in, check_out = future_dates
        result = check_availability(check_in, check_out, room_type="penthouse")
        assert "No rooms available" in result


# ============================================================
# Tool 2: make_reservation
# ============================================================

class TestMakeReservation:

    def test_successful_reservation(self, future_dates):
        check_in, check_out = future_dates
        result = make_reservation(
            guest_name="Test Guest",
            guest_email="test@example.com",
            guest_phone="555-0000",
            room_type="standard",
            check_in_date=check_in,
            check_out_date=check_out,
            num_guests=1,
        )
        assert "Reservation Confirmed" in result
        assert "CONF" in result
        assert "Test Guest" in result

    def test_shows_total(self, future_dates):
        check_in, check_out = future_dates
        result = make_reservation(
            guest_name="Price Test",
            guest_email="price@test.com",
            guest_phone="555-1111",
            room_type="standard",
            check_in_date=check_in,
            check_out_date=check_out,
        )
        # 2 nights at $149 = $298.00
        assert "$298.00" in result
        assert "2 nights" in result

    def test_invalid_date_format(self):
        result = make_reservation(
            guest_name="Bad Date",
            guest_email="bad@date.com",
            guest_phone="555-2222",
            room_type="standard",
            check_in_date="invalid",
            check_out_date="also-invalid",
        )
        assert "Error" in result
        assert "YYYY-MM-DD" in result

    def test_checkout_before_checkin(self, future_dates):
        check_in, check_out = future_dates
        result = make_reservation(
            guest_name="Backwards",
            guest_email="back@test.com",
            guest_phone="555-3333",
            room_type="standard",
            check_in_date=check_out,
            check_out_date=check_in,
        )
        assert "Check-out date must be after check-in date" in result

    def test_past_checkin(self, past_date):
        result = make_reservation(
            guest_name="Past Guest",
            guest_email="past@test.com",
            guest_phone="555-4444",
            room_type="standard",
            check_in_date=past_date,
            check_out_date=_future(2),
        )
        assert "past" in result.lower()

    def test_invalid_room_type(self, future_dates):
        check_in, check_out = future_dates
        result = make_reservation(
            guest_name="Bad Type",
            guest_email="bad@type.com",
            guest_phone="555-5555",
            room_type="penthouse",
            check_in_date=check_in,
            check_out_date=check_out,
        )
        assert "no penthouse rooms" in result.lower() or "Invalid room type" in result or "no penthouse" in result.lower()

    def test_exceeds_max_occupancy(self, future_dates):
        check_in, check_out = future_dates
        result = make_reservation(
            guest_name="Crowd",
            guest_email="crowd@test.com",
            guest_phone="555-6666",
            room_type="standard",
            check_in_date=check_in,
            check_out_date=check_out,
            num_guests=5,  # standard max is 2
        )
        assert "maximum occupancy" in result.lower() or "max" in result.lower()

    def test_special_requests(self, future_dates):
        check_in, check_out = future_dates
        result = make_reservation(
            guest_name="Special Guest",
            guest_email="special@test.com",
            guest_phone="555-7777",
            room_type="standard",
            check_in_date=check_in,
            check_out_date=check_out,
            special_requests="Late checkout",
        )
        assert "Reservation Confirmed" in result

    def test_single_night_stay(self):
        check_in = _future(10)
        check_out = _future(11)
        result = make_reservation(
            guest_name="One Night",
            guest_email="one@night.com",
            guest_phone="555-8888",
            room_type="standard",
            check_in_date=check_in,
            check_out_date=check_out,
        )
        assert "1 night" in result
        assert "$149.00" in result


# ============================================================
# Tool 3: get_reservation
# ============================================================

class TestGetReservation:

    def test_existing_reservation(self, sample_confirmed_conf):
        result = get_reservation(sample_confirmed_conf)
        assert "Sarah Johnson" in result
        assert sample_confirmed_conf in result

    def test_nonexistent_reservation(self):
        result = get_reservation("CONFXXXXXX")
        assert "No reservation found" in result

    def test_shows_status(self, sample_checked_in_conf):
        result = get_reservation(sample_checked_in_conf)
        assert "Checked In" in result

    def test_shows_room_details(self, sample_confirmed_conf):
        result = get_reservation(sample_confirmed_conf)
        assert "Executive Suite" in result or "suite" in result.lower()
        assert "$" in result

    def test_shows_special_requests(self, sample_confirmed_conf):
        result = get_reservation(sample_confirmed_conf)
        assert "Anniversary celebration" in result

    def test_checked_in_shows_room_number(self, sample_checked_in_conf):
        result = get_reservation(sample_checked_in_conf)
        assert "301" in result


# ============================================================
# Tool 4: cancel_reservation
# ============================================================

class TestCancelReservation:

    def test_cancel_confirmed(self, sample_confirmed_conf):
        result = cancel_reservation(sample_confirmed_conf)
        assert "Cancelled" in result
        assert sample_confirmed_conf in result

    def test_cancel_nonexistent(self):
        result = cancel_reservation("CONFXXXXXX")
        assert "No reservation found" in result

    def test_cancel_already_cancelled(self, sample_confirmed_conf):
        cancel_reservation(sample_confirmed_conf)
        result = cancel_reservation(sample_confirmed_conf)
        assert "already been cancelled" in result

    def test_cancel_checked_in(self, sample_checked_in_conf):
        result = cancel_reservation(sample_checked_in_conf)
        assert "already checked in" in result

    def test_cancel_shows_refund_policy(self, sample_confirmed_conf):
        result = cancel_reservation(sample_confirmed_conf)
        assert "refund" in result.lower() or "48 hours" in result

    def test_cancel_shows_guest_info(self, sample_confirmed_conf):
        result = cancel_reservation(sample_confirmed_conf)
        assert "Sarah Johnson" in result


# ============================================================
# Tool 5: submit_service_request
# ============================================================

class TestSubmitServiceRequest:

    def test_room_service(self, sample_confirmed_conf):
        result = submit_service_request(
            sample_confirmed_conf, "room_service", "Club sandwich and coffee"
        )
        assert "Service Request Submitted" in result
        assert "30-45 minutes" in result

    def test_housekeeping(self, sample_checked_in_conf):
        result = submit_service_request(
            sample_checked_in_conf, "housekeeping", "Fresh towels"
        )
        assert "Service Request Submitted" in result
        assert "20 minutes" in result

    def test_maintenance(self, sample_confirmed_conf):
        result = submit_service_request(
            sample_confirmed_conf, "maintenance", "AC not working"
        )
        assert "Service Request Submitted" in result
        assert "maintenance technician" in result.lower()

    def test_concierge(self, sample_confirmed_conf):
        result = submit_service_request(
            sample_confirmed_conf, "concierge", "Book dinner reservation"
        )
        assert "Service Request Submitted" in result
        assert "10 minutes" in result

    def test_invalid_request_type(self, sample_confirmed_conf):
        result = submit_service_request(
            sample_confirmed_conf, "valet", "Park my car"
        )
        assert "Invalid request type" in result

    def test_nonexistent_reservation(self):
        result = submit_service_request(
            "CONFXXXXXX", "room_service", "Something"
        )
        assert "No active reservation" in result

    def test_cancelled_reservation(self, sample_confirmed_conf):
        cancel_reservation(sample_confirmed_conf)
        result = submit_service_request(
            sample_confirmed_conf, "room_service", "Something"
        )
        assert "No active reservation" in result

    def test_shows_request_id(self, sample_confirmed_conf):
        result = submit_service_request(
            sample_confirmed_conf, "room_service", "Water"
        )
        assert "Request ID" in result

    def test_shows_description(self, sample_confirmed_conf):
        result = submit_service_request(
            sample_confirmed_conf, "concierge", "Need taxi at 8 AM"
        )
        assert "Need taxi at 8 AM" in result


# ============================================================
# Tool 6: get_hotel_info
# ============================================================

class TestGetHotelInfo:

    def test_general_info(self):
        result = get_hotel_info()
        assert "Grand Azure Hotel" in result
        assert "Check-in" in result
        assert "Check-out" in result

    def test_specific_topic_parking(self):
        result = get_hotel_info(topic="parking")
        assert "parking" in result.lower() or "$" in result

    def test_specific_topic_wifi(self):
        result = get_hotel_info(topic="wifi")
        assert "wifi" in result.lower() or "WiFi" in result

    def test_specific_topic_pool(self):
        result = get_hotel_info(topic="pool")
        assert "pool" in result.lower()

    def test_specific_topic_cancellation(self):
        result = get_hotel_info(topic="cancellation_policy")
        assert "48 hours" in result or "cancellation" in result.lower()

    def test_local_attractions(self):
        result = get_hotel_info(topic="local_attractions")
        assert "Seaside Pier" in result
        assert "Ocean View Beach" in result

    def test_nonexistent_topic(self):
        result = get_hotel_info(topic="helicopter_pad")
        assert "No information found" in result

    def test_general_info_has_amenities(self):
        result = get_hotel_info()
        assert "Pool" in result or "pool" in result
        assert "Fitness" in result or "fitness" in result
        assert "Spa" in result or "spa" in result

    def test_general_info_has_dining(self):
        result = get_hotel_info()
        assert "restaurant" in result.lower() or "Azure Table" in result
        assert "room service" in result.lower() or "Room Service" in result


# ============================================================
# Tool 7: get_room_types
# ============================================================

class TestGetRoomTypes:

    def test_returns_all_types(self):
        result = get_room_types()
        assert "Standard Room" in result
        assert "Deluxe Room" in result
        assert "Executive Suite" in result
        assert "Family Room" in result

    def test_shows_rates(self):
        result = get_room_types()
        assert "$149" in result
        assert "$219" in result
        assert "$399" in result
        assert "$249" in result

    def test_shows_max_occupancy(self):
        result = get_room_types()
        assert "Max Occupancy" in result

    def test_shows_amenities(self):
        result = get_room_types()
        assert "WiFi" in result
        assert "TV" in result

    def test_header_present(self):
        result = get_room_types()
        assert "Room Types at The Grand Azure Hotel" in result


# ============================================================
# Resource: hotel://info
# ============================================================

class TestHotelInfoResource:

    def test_returns_hotel_info(self):
        result = hotel_info_resource()
        assert "Grand Azure Hotel" in result
        assert "Check-in" in result

    def test_matches_tool_output(self):
        """Resource should return the same as calling get_hotel_info() with no topic."""
        resource_result = hotel_info_resource()
        tool_result = get_hotel_info()
        assert resource_result == tool_result


# ============================================================
# Resource: hotel://rooms
# ============================================================

class TestRoomTypesResource:

    def test_returns_room_types(self):
        result = room_types_resource()
        assert "Standard Room" in result
        assert "Deluxe Room" in result

    def test_matches_tool_output(self):
        resource_result = room_types_resource()
        tool_result = get_room_types()
        assert resource_result == tool_result


# ============================================================
# Resource: hotel://attractions
# ============================================================

class TestAttractionsResource:

    def test_returns_attractions(self):
        result = attractions_resource()
        assert "Seaside Pier" in result
        assert "Ocean View Beach" in result
        assert "Maritime Museum" in result

    def test_matches_tool_output(self):
        resource_result = attractions_resource()
        tool_result = get_hotel_info("local_attractions")
        assert resource_result == tool_result


# ============================================================
# Integration / end-to-end scenarios
# ============================================================

class TestEndToEnd:

    def test_reserve_then_lookup(self, future_dates):
        """Make a reservation and then look it up."""
        check_in, check_out = future_dates
        reservation_result = make_reservation(
            guest_name="E2E Guest",
            guest_email="e2e@test.com",
            guest_phone="555-0000",
            room_type="deluxe",
            check_in_date=check_in,
            check_out_date=check_out,
        )
        # Extract confirmation number from the formatted output
        for line in reservation_result.split("\n"):
            if "Confirmation Number" in line:
                conf_num = line.split("**")[1]
                break
        else:
            pytest.fail("Could not find confirmation number in output")

        lookup_result = get_reservation(conf_num)
        assert "E2E Guest" in lookup_result
        assert "Deluxe Room" in lookup_result

    def test_reserve_then_cancel(self, future_dates):
        """Make a reservation and then cancel it."""
        check_in, check_out = future_dates
        reservation_result = make_reservation(
            guest_name="Cancel Guest",
            guest_email="cancel@test.com",
            guest_phone="555-1111",
            room_type="standard",
            check_in_date=check_in,
            check_out_date=check_out,
        )
        for line in reservation_result.split("\n"):
            if "Confirmation Number" in line:
                conf_num = line.split("**")[1]
                break
        else:
            pytest.fail("Could not find confirmation number in output")

        cancel_result = cancel_reservation(conf_num)
        assert "Cancelled" in cancel_result

        # Verify it shows as cancelled
        lookup = get_reservation(conf_num)
        assert "Cancelled" in lookup

    def test_reserve_then_service_request(self, future_dates):
        """Make a reservation and submit a service request."""
        check_in, check_out = future_dates
        reservation_result = make_reservation(
            guest_name="Service Guest",
            guest_email="svc@test.com",
            guest_phone="555-2222",
            room_type="family",
            check_in_date=check_in,
            check_out_date=check_out,
        )
        for line in reservation_result.split("\n"):
            if "Confirmation Number" in line:
                conf_num = line.split("**")[1]
                break
        else:
            pytest.fail("Could not find confirmation number in output")

        svc_result = submit_service_request(
            conf_num, "room_service", "Extra blankets"
        )
        assert "Service Request Submitted" in svc_result

    def test_check_availability_then_reserve(self, future_dates):
        """Check availability then reserve an available type."""
        check_in, check_out = future_dates

        # Check availability for suites
        avail = check_availability(check_in, check_out, room_type="suite")
        assert "Executive Suite" in avail

        # Now reserve one
        result = make_reservation(
            guest_name="Suite Guest",
            guest_email="suite@test.com",
            guest_phone="555-3333",
            room_type="suite",
            check_in_date=check_in,
            check_out_date=check_out,
            num_guests=3,
        )
        assert "Reservation Confirmed" in result
        # 2 nights * $399 = $798
        assert "$798.00" in result
