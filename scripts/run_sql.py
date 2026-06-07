"""Ejecuta scripts SQL en MySQL (schema + seed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

ROOT = Path(__file__).resolve().parent.parent


def run_file(cursor, path: Path) -> int:
    sql = path.read_text(encoding="utf-8-sig")
    statements = []
    buffer: list[str] = []

    for raw_line in sql.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue
        buffer.append(raw_line)
        if line.endswith(";"):
            statements.append("\n".join(buffer))
            buffer = []

    if buffer:
        statements.append("\n".join(buffer))

    for stmt in statements:
        cursor.execute(stmt)
    return len(statements)


def main() -> None:
    files = sys.argv[1:] or ["schema_mysql.sql", "seed_mysql.sql"]
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3307,
        user="binfrix",
        password="Binfrix2026.",
        charset="utf8mb4",
        client_flag=CLIENT.MULTI_STATEMENTS,
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            total = 0
            for name in files:
                path = ROOT / "scripts" / name
                count = run_file(cur, path)
                total += count
                print(f"OK {name}: {count} sentencias")
            cur.execute("USE binfrix")
            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0]
            cur.execute("SELECT email, name FROM users ORDER BY email")
            print(f"Usuarios en BD: {users}")
            for email, name in cur.fetchall():
                print(f"  - {email} ({name})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
