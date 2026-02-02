# Hotel Concierge MCP Server

An MCP (Model Context Protocol) server that enables Claude to act as a hotel concierge—checking availability, making reservations, and handling guest services.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![MCP](https://img.shields.io/badge/MCP-1.26-green)
![Claude](https://img.shields.io/badge/Claude-Desktop-blueviolet)

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io/) is an open standard that lets AI assistants connect to external tools and data sources. This server gives Claude the ability to manage hotel operations.

## Demo

Ask Claude things like:

- "Check room availability for February 10-12"
- "Make a reservation for John Doe, deluxe room, Feb 10-12"
- "Look up reservation CONF001"
- "What's the cancellation policy?"
- "Submit a room service request for extra towels"

## Tools

| Tool | Description |
|------|-------------|
| `check_availability` | Check room availability for specific dates |
| `make_reservation` | Book a room for a guest |
| `get_reservation` | Look up reservation details by confirmation number |
| `cancel_reservation` | Cancel an existing reservation |
| `submit_service_request` | Submit room service, housekeeping, or maintenance requests |
| `get_hotel_info` | Get hotel policies, amenities, and local attractions |
| `get_room_types` | List all room types with rates and amenities |

## Resources

| Resource | Description |
|----------|-------------|
| `hotel://info` | General hotel information |
| `hotel://rooms` | Room types and rates |
| `hotel://attractions` | Local attractions |

## Room Types

| Type | Rate | Occupancy | Amenities |
|------|------|-----------|-----------|
| Standard | $149/night | 2 guests | Queen Bed, Work Desk, 40" TV, WiFi |
| Deluxe | $219/night | 2 guests | King Bed, Sitting Area, 55" TV, Mini Bar |
| Family | $249/night | 4 guests | Two Queen Beds, Sofa Bed, Mini Fridge |
| Executive Suite | $399/night | 4 guests | King Bed, Living Room, Jacuzzi, Balcony |

## Setup

### 1. Clone and Install
```bash
git clone https://github.com/woodstocksoftware/hotel-concierge-mcp.git
cd hotel-concierge-mcp

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "hotel-concierge": {
      "command": "/path/to/hotel-concierge-mcp/venv/bin/python",
      "args": ["/path/to/hotel-concierge-mcp/run_server.py"]
    }
  }
}
```

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. The hotel-concierge tools will be available.

## Project Structure
```
hotel-concierge-mcp/
├── run_server.py              # MCP server entry point
├── src/
│   └── hotel_concierge/
│       ├── server.py          # MCP tools and resources
│       └── database.py        # SQLite database with mock data
├── data/
│   └── hotel.db               # SQLite database (auto-created)
└── requirements.txt
```

## Architecture
```
┌─────────────────┐         ┌─────────────────────────────────────┐
│  Claude Desktop │◄──MCP──►│      Hotel Concierge Server         │
└─────────────────┘         │                                     │
                            │  Tools:                             │
                            │  • check_availability               │
                            │  • make_reservation                 │
                            │  • get_reservation                  │
                            │  • cancel_reservation               │
                            │  • submit_service_request           │
                            │  • get_hotel_info                   │
                            │  • get_room_types                   │
                            │                                     │
                            └──────────────┬──────────────────────┘
                                           │
                                           ▼
                            ┌─────────────────────────────────────┐
                            │            SQLite Database          │
                            │  (easily swap for real PMS/API)     │
                            └─────────────────────────────────────┘
```

## Extending for Production

The database module (`database.py`) uses SQLite with mock data. To connect to a real property management system:

1. Replace the database functions with API calls to your PMS
2. Add authentication/credentials handling
3. Map your PMS data model to the tool interfaces

## Use Cases

### Hospitality
- Hotel front desk assistant
- Guest self-service concierge
- Reservation management

### Training
- Staff training simulator
- Process documentation

## License

MIT

---

Built by [Jim Williams](https://linkedin.com/in/woodstocksoftware) | [GitHub](https://github.com/woodstocksoftware)
