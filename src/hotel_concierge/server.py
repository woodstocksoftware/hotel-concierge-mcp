"""
Hotel Concierge MCP Server

Provides tools for Claude to act as a hotel concierge:
- Check room availability
- Make reservations
- Look up guest information
- Submit service requests
- Get hotel information
"""

import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from . import database as db

# Initialize MCP server
mcp = FastMCP("Hotel Concierge")


# ============================================================
# TOOLS
# ============================================================

@mcp.tool()
def check_availability(
    check_in_date: str,
    check_out_date: str,
    room_type: str = None
) -> str:
    """
    Check room availability for given dates.
    
    Args:
        check_in_date: Check-in date (YYYY-MM-DD format)
        check_out_date: Check-out date (YYYY-MM-DD format)
        room_type: Optional room type filter (standard, deluxe, suite, family)
    
    Returns:
        Available rooms with rates and amenities
    """
    try:
        # Validate dates
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        
        if check_in >= check_out:
            return "Error: Check-out date must be after check-in date."
        
        if check_in.date() < datetime.now().date():
            return "Error: Check-in date cannot be in the past."
        
        nights = (check_out - check_in).days
        
        available = db.check_availability(check_in_date, check_out_date, room_type)
        
        if not available:
            return f"No rooms available for {check_in_date} to {check_out_date}."
        
        # Group by room type
        by_type = {}
        for room in available:
            rt = room['room_type_id']
            if rt not in by_type:
                by_type[rt] = {
                    'name': room['room_type_name'],
                    'rate': room['base_rate'],
                    'total': room['base_rate'] * nights,
                    'max_occupancy': room['max_occupancy'],
                    'amenities': json.loads(room['amenities']),
                    'count': 0,
                    'rooms': []
                }
            by_type[rt]['count'] += 1
            by_type[rt]['rooms'].append(room['room_number'])
        
        result = f"Availability for {check_in_date} to {check_out_date} ({nights} night{'s' if nights > 1 else ''}):\n\n"
        
        for rt_id, info in by_type.items():
            result += f"**{info['name']}** - {info['count']} available\n"
            result += f"  Rate: ${info['rate']}/night (Total: ${info['total']})\n"
            result += f"  Max Occupancy: {info['max_occupancy']} guests\n"
            result += f"  Amenities: {', '.join(info['amenities'])}\n\n"
        
        return result
        
    except ValueError as e:
        return f"Error: Invalid date format. Please use YYYY-MM-DD. ({e})"


@mcp.tool()
def make_reservation(
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    room_type: str,
    check_in_date: str,
    check_out_date: str,
    num_guests: int = 1,
    special_requests: str = None
) -> str:
    """
    Make a room reservation.
    
    Args:
        guest_name: Full name of the guest
        guest_email: Guest's email address
        guest_phone: Guest's phone number
        room_type: Room type (standard, deluxe, suite, family)
        check_in_date: Check-in date (YYYY-MM-DD format)
        check_out_date: Check-out date (YYYY-MM-DD format)
        num_guests: Number of guests (default 1)
        special_requests: Any special requests or notes
    
    Returns:
        Confirmation details or error message
    """
    try:
        # Validate dates
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        
        if check_in >= check_out:
            return "Error: Check-out date must be after check-in date."
        
        if check_in.date() < datetime.now().date():
            return "Error: Check-in date cannot be in the past."
        
        # Check availability first
        available = db.check_availability(check_in_date, check_out_date, room_type)
        if not available:
            return f"Sorry, no {room_type} rooms are available for those dates."
        
        # Check occupancy
        room_types = {rt['id']: rt for rt in db.get_room_types()}
        if room_type not in room_types:
            return f"Error: Invalid room type. Choose from: standard, deluxe, suite, family"
        
        if num_guests > room_types[room_type]['max_occupancy']:
            return f"Error: {room_types[room_type]['name']} has maximum occupancy of {room_types[room_type]['max_occupancy']}."
        
        # Make the reservation
        result = db.make_reservation(
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            room_type_id=room_type,
            check_in=check_in_date,
            check_out=check_out_date,
            num_guests=num_guests,
            special_requests=special_requests
        )
        
        return f"""
✅ Reservation Confirmed!

Confirmation Number: **{result['confirmation_number']}**
Guest: {result['guest_name']}
Room Type: {room_types[room_type]['name']}
Check-in: {result['check_in']} (3:00 PM)
Check-out: {result['check_out']} (11:00 AM)
Guests: {num_guests}
Total: ${result['total_amount']:.2f} ({result['nights']} night{'s' if result['nights'] > 1 else ''})

Please save your confirmation number for check-in.
"""
        
    except ValueError as e:
        return f"Error: Invalid date format. Please use YYYY-MM-DD. ({e})"


@mcp.tool()
def get_reservation(confirmation_number: str) -> str:
    """
    Look up a reservation by confirmation number.
    
    Args:
        confirmation_number: The reservation confirmation number
    
    Returns:
        Reservation details or error if not found
    """
    reservation = db.get_reservation(confirmation_number)
    
    if not reservation:
        return f"No reservation found with confirmation number: {confirmation_number}"
    
    status_emoji = {
        'confirmed': '📅',
        'checked_in': '🏨',
        'checked_out': '✅',
        'cancelled': '❌'
    }
    
    result = f"""
{status_emoji.get(reservation['status'], '📋')} Reservation Details

Confirmation: **{reservation['confirmation_number']}**
Status: {reservation['status'].replace('_', ' ').title()}
Guest: {reservation['guest_name']}
Email: {reservation['guest_email']}
Phone: {reservation['guest_phone']}

Room Type: {reservation['room_type_name']}
Room Number: {reservation['room_number'] or 'To be assigned at check-in'}
Check-in: {reservation['check_in_date']} (3:00 PM)
Check-out: {reservation['check_out_date']} (11:00 AM)
Guests: {reservation['num_guests']}
Total: ${reservation['total_amount']:.2f}
"""
    
    if reservation['special_requests']:
        result += f"\nSpecial Requests: {reservation['special_requests']}"
    
    return result


@mcp.tool()
def cancel_reservation(confirmation_number: str) -> str:
    """
    Cancel a reservation.
    
    Args:
        confirmation_number: The reservation confirmation number
    
    Returns:
        Cancellation confirmation or error message
    """
    # First check if it exists
    reservation = db.get_reservation(confirmation_number)
    
    if not reservation:
        return f"No reservation found with confirmation number: {confirmation_number}"
    
    if reservation['status'] == 'cancelled':
        return "This reservation has already been cancelled."
    
    if reservation['status'] == 'checked_in':
        return "Cannot cancel - guest has already checked in. Please speak with the front desk."
    
    if reservation['status'] == 'checked_out':
        return "Cannot cancel - guest has already checked out."
    
    success = db.cancel_reservation(confirmation_number)
    
    if success:
        return f"""
❌ Reservation Cancelled

Confirmation: {confirmation_number}
Guest: {reservation['guest_name']}
Dates: {reservation['check_in_date']} to {reservation['check_out_date']}

The reservation has been cancelled. Per our policy, cancellations made more than 48 hours 
before check-in receive a full refund. Please allow 5-7 business days for processing.
"""
    else:
        return "Unable to cancel reservation. Please contact the front desk for assistance."


@mcp.tool()
def submit_service_request(
    confirmation_number: str,
    request_type: str,
    description: str
) -> str:
    """
    Submit a service request for a guest.
    
    Args:
        confirmation_number: Guest's confirmation number
        request_type: Type of request (room_service, housekeeping, maintenance, concierge)
        description: Description of the request
    
    Returns:
        Request confirmation or error message
    """
    valid_types = ['room_service', 'housekeeping', 'maintenance', 'concierge']
    
    if request_type not in valid_types:
        return f"Error: Invalid request type. Choose from: {', '.join(valid_types)}"
    
    result = db.submit_service_request(confirmation_number, request_type, description)
    
    if not result:
        return f"Error: No active reservation found for confirmation number: {confirmation_number}"
    
    type_messages = {
        'room_service': "Your order will be delivered within 30-45 minutes.",
        'housekeeping': "Housekeeping will arrive within 20 minutes.",
        'maintenance': "A maintenance technician will be dispatched shortly.",
        'concierge': "Our concierge team will contact you within 10 minutes."
    }
    
    return f"""
✅ Service Request Submitted

Request ID: #{result['request_id']}
Type: {request_type.replace('_', ' ').title()}
Description: {result['description']}
Status: {result['status'].title()}

{type_messages[request_type]}

For urgent matters, please call the front desk at extension 0.
"""


@mcp.tool()
def get_hotel_info(topic: str = None) -> str:
    """
    Get information about the hotel.
    
    Args:
        topic: Specific topic (check_in_time, check_out_time, parking, wifi, pool, 
               fitness, spa, restaurant, room_service, cancellation_policy, 
               local_attractions) or None for general info
    
    Returns:
        Hotel information
    """
    if topic:
        info = db.get_hotel_info(topic)
        if info is None:
            return f"No information found for topic: {topic}"
        
        if isinstance(info, list):
            # Format attractions
            result = f"**{topic.replace('_', ' ').title()}:**\n\n"
            for item in info:
                result += f"• **{item['name']}** ({item['distance']})\n  {item['description']}\n\n"
            return result
        
        return f"**{topic.replace('_', ' ').title()}:** {info}"
    
    # Return general overview
    info = db.get_hotel_info()
    
    return f"""
🏨 **{info['name']}**
{info['address']}
📞 {info['phone']} | ✉️ {info['email']}

**Hours:**
- Check-in: {info['check_in_time']}
- Check-out: {info['check_out_time']}

**Amenities:**
- {info['wifi']}
- {info['pool']}
- {info['fitness']}
- {info['spa']}

**Dining:**
- {info['restaurant']}
- {info['room_service']}

**Parking:**
- {info['parking']}

For more details on any topic, ask about: check_in_time, parking, wifi, pool, 
fitness, spa, restaurant, room_service, cancellation_policy, or local_attractions.
"""


@mcp.tool()
def get_room_types() -> str:
    """
    Get information about all room types and rates.
    
    Returns:
        List of room types with descriptions and rates
    """
    room_types = db.get_room_types()
    
    result = "**Room Types at The Grand Azure Hotel:**\n\n"
    
    for rt in room_types:
        amenities = json.loads(rt['amenities'])
        result += f"### {rt['name']}\n"
        result += f"{rt['description']}\n"
        result += f"• **Rate:** ${rt['base_rate']}/night\n"
        result += f"• **Max Occupancy:** {rt['max_occupancy']} guests\n"
        result += f"• **Amenities:** {', '.join(amenities)}\n\n"
    
    return result


# ============================================================
# RESOURCES
# ============================================================

@mcp.resource("hotel://info")
def hotel_info_resource() -> str:
    """General hotel information and policies."""
    return get_hotel_info()


@mcp.resource("hotel://rooms")
def room_types_resource() -> str:
    """Room types, rates, and amenities."""
    return get_room_types()


@mcp.resource("hotel://attractions")
def attractions_resource() -> str:
    """Local attractions and recommendations."""
    return get_hotel_info("local_attractions")


# ============================================================
# MAIN
# ============================================================

def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
