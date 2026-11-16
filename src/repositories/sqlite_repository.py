import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from src.domain.rules import BusinessError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteRepository:
    def __init__(self, database: str = "wallet.db"):
        self.database = database
        self.uri = database.startswith("file:")
        self._write_lock = threading.RLock()
        # Mantém banco em memória compartilhado vivo durante os testes.
        self.anchor = self.connect() if "mode=memory" in database else None
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.database, uri=self.uri, timeout=15,
                               isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 15000")
        return conn

    @contextmanager
    def transaction(self):
        with self._write_lock:
            conn = self.connect()
            try:
                # Serializa threads locais e inicia transação exclusiva para escrita.
                conn.execute("BEGIN IMMEDIATE")
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def initialize(self):
        with self.transaction() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL,
                    balance_cents INTEGER NOT NULL CHECK(balance_cents >= 0)
                );
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    transfer_id TEXT,
                    kind TEXT NOT NULL CHECK(kind IN ('credit', 'debit')),
                    amount_cents INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(account_id) REFERENCES accounts(id)
                );
                CREATE TABLE IF NOT EXISTS transfers (
                    id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    origin_id INTEGER NOT NULL,
                    destination_id INTEGER NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

    def create_account(self, owner: str, balance_cents: int) -> dict:
        with self.transaction() as conn:
            cursor = conn.execute("INSERT INTO accounts(owner, balance_cents) VALUES (?, ?)",
                                  (owner, balance_cents))
            account_id = cursor.lastrowid
            if balance_cents:
                conn.execute("INSERT INTO entries(account_id,kind,amount_cents,created_at) VALUES (?, 'credit', ?, ?)",
                             (account_id, balance_cents, utc_now()))
            return {"id": account_id, "owner": owner, "balance_cents": balance_cents}

    def get_account(self, account_id: int):
        conn = self.connect()
        try:
            row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def statement(self, account_id: int, kind: str | None = None,
                  start: str | None = None, end: str | None = None):
        conn = self.connect()
        try:
            if not conn.execute("SELECT 1 FROM accounts WHERE id=?", (account_id,)).fetchone():
                raise BusinessError("Conta não encontrada", 404)
            query = "SELECT * FROM entries WHERE account_id=?"
            params = [account_id]
            if kind:
                query += " AND kind=?"
                params.append(kind)
            if start:
                query += " AND created_at>=?"
                params.append(start)
            if end:
                query += " AND created_at<?"
                params.append(end)
            query += " ORDER BY id"
            return [dict(row) for row in conn.execute(query, params).fetchall()]
        finally:
            conn.close()
