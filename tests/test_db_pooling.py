"""Unit tests for the db_tools connection pool contract (no live database).

The regression these guard against: db_tools used to dial a new PostgreSQL
connection for every query, which cost seconds per query against a managed
Postgres endpoint. Connections must now be checked out and returned, and a
connection that fails at the protocol level must be discarded rather than
handed to the next caller.
"""

import pytest
import psycopg2

from shared.tools import db_tools


class FakeConn:
    def __init__(self):
        self.closed = 0
        self.status = psycopg2.extensions.STATUS_READY
        self.rolled_back = False
        self.committed = False
        self.close_called = False

    def rollback(self):
        self.rolled_back = True

    def commit(self):
        self.committed = True

    def close(self):
        self.close_called = True
        self.closed = 1


class FakePool:
    def __init__(self, conn):
        self.conn = conn
        self.checkouts = 0
        self.returns = []
        self.dial_count = 1  # the one connection created up front

    def getconn(self):
        self.checkouts += 1
        return self.conn

    def putconn(self, conn, close=False):
        self.returns.append(close)


@pytest.fixture
def pooled(monkeypatch):
    conn = FakeConn()
    pool = FakePool(conn)
    monkeypatch.setattr(db_tools, "_pool", pool)
    return conn, pool


def test_connection_is_returned_not_closed(pooled):
    conn, pool = pooled
    with db_tools._conn() as c:
        assert c is conn

    # Returned to the pool for reuse, and never closed.
    assert pool.returns == [False]
    assert conn.close_called is False
    assert pool.dial_count == 1


def test_connection_is_reused_across_calls(pooled):
    conn, pool = pooled
    for _ in range(3):
        with db_tools._conn() as c:
            assert c is conn

    # Three checkouts, three returns, still a single dialed connection.
    assert pool.checkouts == 3
    assert pool.returns == [False, False, False]
    assert pool.dial_count == 1


def test_open_transaction_is_committed_before_reuse(pooled):
    conn, pool = pooled
    conn.status = psycopg2.extensions.STATUS_IN_TRANSACTION
    with db_tools._conn():
        pass

    # A caller that left a transaction open must not leak it into the next user.
    assert conn.committed is True
    assert pool.returns == [False]


def test_protocol_error_rolls_back_and_discards_connection(pooled):
    conn, pool = pooled
    with pytest.raises(psycopg2.OperationalError):
        with db_tools._conn():
            raise psycopg2.OperationalError("server closed the connection unexpectedly")

    # Rolled back, and closed instead of pooled so no dead socket is handed out.
    assert conn.rolled_back is True
    assert pool.returns == [True]


def test_application_error_rolls_back_but_keeps_connection(pooled):
    conn, pool = pooled
    with pytest.raises(ValueError):
        with db_tools._conn():
            raise ValueError("bad data")

    # A query-level error is not a broken connection: roll back, keep it pooled.
    assert conn.rolled_back is True
    assert pool.returns == [False]
    assert conn.close_called is False
