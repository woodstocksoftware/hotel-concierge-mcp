# CLAUDE.md — Hotel Concierge MCP Server

> **Purpose:** MCP server enabling Claude to manage hotel operations (reservations, services, info)
> **Owner:** Jim Williams - Woodstock Software LLC
> **Repo:** woodstocksoftware/hotel-concierge-mcp (public)

---

## Tech Stack

- Python 3.12
- FastMCP (MCP framework)
- SQLite (auto-initialized with sample data)
- pydantic, python-dateutil, python-dotenv

## Project Structure

```
hotel-concierge-mcp/
├── run_server.py                  # Entry point — mcp.run(transport="stdio")
├── requirements.txt               # 3 direct dependencies
├── src/hotel_concierge/
│   ├── server.py                  # 7 MCP tools + 3 resources (422 lines)
│   ├── database.py                # SQLite setup + queries (374 lines)
│   └── __main__.py                # Alt entry with error handling
├── data/hotel.db                  # SQLite DB (auto-created on first run)
├── LICENSE                        # MIT
└── README.md
```

## How to Run

```bash
cd /Users/james/projects/hotel-concierge-mcp
source venv/bin/activate
python run_server.py
```

Or via module: `python -m src.hotel_concierge`

### Claude Desktop Config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "hotel-concierge": {
      "command": "/Users/james/projects/hotel-concierge-mcp/venv/bin/python",
      "args": ["/Users/james/projects/hotel-concierge-mcp/run_server.py"]
    }
  }
}
```

## Environment Variables

None required. Fully self-contained with SQLite.

## MCP Tools (7)

| Tool | Purpose |
|------|---------|
| `check_availability` | Query available rooms by date range and type |
| `make_reservation` | Create booking, validates dates/occupancy, returns confirmation # |
| `get_reservation` | Look up by confirmation number |
| `cancel_reservation` | Cancel (only if status is 'confirmed') |
| `submit_service_request` | Room service/housekeeping/maintenance/concierge requests |
| `get_hotel_info` | Hotel info by topic (check-in, parking, wifi, pool, etc.) |
| `get_room_types` | List all room types with rates and amenities |

## MCP Resources (3)

| Resource | Returns |
|----------|---------|
| `hotel://info` | General hotel information and policies |
| `hotel://rooms` | All room types with rates |
| `hotel://attractions` | Local attractions and recommendations |

## Database Schema

5 tables: `room_types`, `rooms`, `reservations`, `service_requests`, `hotel_info`

Sample data: 4 room types ($149-$399), 20 rooms, 3 sample reservations, 15 info entries.

## Testing

No formal test suite. Manual validation:
```bash
python -c "from src.hotel_concierge.server import mcp; print(f'Server: {mcp.name}')"
python -m src.hotel_concierge.database  # Prints sample data
```

## Key Patterns

- **Auto-init DB**: Schema + sample data created on first import of database.py
- **Confirmation numbers**: `CONF` + 6 random alphanumeric chars
- **Status flows**: Reservations: confirmed → checked_in → checked_out (or cancelled). Service requests: pending → in_progress → completed
- **Validation**: Check-in after today, check-out after check-in, occupancy limits, status guards
- **Output format**: Formatted markdown with emoji indicators

## What's Missing

- [ ] Tests (pytest)
- [ ] CI workflow (.github/workflows/)
- [ ] pyproject.toml
