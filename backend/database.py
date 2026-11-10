import sqlite3
from datetime import datetime

DB_PATH = "chat_data.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                title TEXT DEFAULT 'New Chat',
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                pages INTEGER,
                chunks INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id)
                    REFERENCES chats(chat_id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id)
                    REFERENCES chats(chat_id)
                    ON DELETE CASCADE
            )
        """)


def create_chat(chat_id):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chats (chat_id, created_at)
            VALUES (?, ?)
            """,
            (chat_id, datetime.now().isoformat())
        )


def get_all_chats():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT c.*
            FROM chats c
            WHERE EXISTS (
                SELECT 1 FROM messages m
                WHERE m.chat_id = c.chat_id
            )
            OR EXISTS (
                SELECT 1 FROM documents d
                WHERE d.chat_id = c.chat_id
            )
            ORDER BY c.created_at DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_chat(chat_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM chats WHERE chat_id = ?",
            (chat_id,)
        ).fetchone()

        return dict(row) if row else None


def update_chat_title(chat_id, title):
    with get_connection() as conn:
        conn.execute(
            "UPDATE chats SET title = ? WHERE chat_id = ?",
            (title, chat_id)
        )


def save_document(
    document_id,
    chat_id,
    filename,
    pages,
    chunks
):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents (
                document_id,
                chat_id,
                filename,
                pages,
                chunks,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                chat_id,
                filename,
                pages,
                chunks,
                datetime.now().isoformat()
            )
        )


def get_chat_documents(chat_id):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM documents
            WHERE chat_id = ?
            ORDER BY created_at DESC
            """,
            (chat_id,)
        ).fetchall()

        return [dict(row) for row in rows]


def delete_document_record(chat_id, document_id):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM documents
            WHERE chat_id = ? AND document_id = ?
            """,
            (chat_id, document_id)
        )


def delete_chat_record(chat_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chats WHERE chat_id = ?",
            (chat_id,)
        )

def save_message(chat_id, role, content):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO messages (
                chat_id, role, content, created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                chat_id,
                role,
                content,
                datetime.now().isoformat()
            )
        )


def get_chat_messages(chat_id):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY message_id ASC
            """,
            (chat_id,)
        ).fetchall()

        return [dict(row) for row in rows]

