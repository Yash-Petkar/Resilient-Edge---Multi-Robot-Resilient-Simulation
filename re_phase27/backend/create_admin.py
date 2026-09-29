"""Create or explicitly reset the local ResilientEdge administrator account."""
from __future__ import annotations

import argparse
import os
import uuid
from getpass import getpass

from backend.auth import hash_password
from backend.database.sqlite_db import ResilientEdgeDatabase

EMAIL = "petkaryash050@gmail.com"
FULL_NAME = "Fleet Administrator"


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the local ResilientEdge administrator account.")
    parser.add_argument(
        "--reset-existing",
        action="store_true",
        help="Reset the existing administrator password instead of leaving an existing account unchanged.",
    )
    args = parser.parse_args()

    db = ResilientEdgeDatabase()
    existing = db.get_user_by_email(EMAIL)
    password = os.getenv("RESILIENTEDGE_ADMIN_PASSWORD") or getpass("Admin password: ")
    password_hash = hash_password(password)

    if existing:
        if not args.reset_existing:
            print("ADMIN account already exists; no changes made.")
            print("Use --reset-existing to intentionally replace its password.")
            return
        db.update_user_password(existing["id"], password_hash)
        db.update_user_role(existing["id"], "ADMIN")
        db.set_user_active(existing["id"], True)
        print(f"Reset ADMIN account for {EMAIL}")
        return

    db.create_user(str(uuid.uuid4()), EMAIL, password_hash, FULL_NAME, "ADMIN")
    print(f"Created ADMIN account for {EMAIL}")


if __name__ == "__main__":
    main()
