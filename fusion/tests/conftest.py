"""Gives each test a fresh, empty test database built from db/init.sql.

Uses TEST_DATABASE_URL (default: the 'ddds_test' database on localhost).
If no database is reachable, the database tests are skipped.
"""
import os
from pathlib import Path

import psycopg
import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql://ddds:ddds-dev@localhost:5432/ddds_test")
INIT_SQL = (Path(__file__).resolve().parents[2] / "db" / "init.sql").read_text()


@pytest.fixture
def db():
    try:
        conn = psycopg.connect(TEST_DB, autocommit=True)
    except psycopg.OperationalError:
        pytest.skip("no test database available")
    conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    conn.execute(INIT_SQL)
    yield conn
    conn.close()
