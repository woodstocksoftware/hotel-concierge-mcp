"""
Shared test fixtures for Hotel Concierge MCP Server tests.

Key design: each test gets a fresh temporary SQLite database so tests
are fully isolated and never touch the real data/hotel.db.
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    """
    Redirect database.DATABASE_PATH to a temp file and re-initialize.

    This fixture is autouse so every test automatically gets a fresh DB
    with sample data, completely isolated from data/hotel.db.
    """
    import src.hotel_concierge.database as db_module

    temp_db = tmp_path / "test_hotel.db"
    monkeypatch.setattr(db_module, "DATABASE_PATH", temp_db)

    # Re-initialize the database with schema + sample data
    db_module.init_database()

    yield temp_db


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def future_dates():
    """Return a (check_in, check_out) tuple 7-9 days from now."""
    today = datetime.now().date()
    check_in = str(today + timedelta(days=7))
    check_out = str(today + timedelta(days=9))
    return check_in, check_out


@pytest.fixture()
def past_date():
    """Return a date string in the past."""
    return str((datetime.now().date() - timedelta(days=5)))


# ---------------------------------------------------------------------------
# Sample reservation helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_confirmed_conf():
    """Confirmation number of a sample confirmed reservation (CONF002)."""
    return "CONF002"


@pytest.fixture()
def sample_checked_in_conf():
    """Confirmation number of the checked-in reservation (CONF001)."""
    return "CONF001"
