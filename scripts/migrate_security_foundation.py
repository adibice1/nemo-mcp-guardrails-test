"""Explicit, idempotent schema rollout for password setup and bounded history."""

import argparse
from _bootstrap import bootstrap_src
bootstrap_src()

from sqlalchemy import inspect, text


def migrate(connection) -> None:
    """Preserve existing credentials while adding setup state and a tail index."""
    columns = {column["name"] for column in inspect(connection).get_columns("users")}
    if "must_change_password" not in columns:
        connection.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT false"))
    if "temporary_password_expires_at" not in columns:
        connection.execute(text("ALTER TABLE users ADD COLUMN temporary_password_expires_at TIMESTAMP WITH TIME ZONE NULL"))
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_conversation_messages_scope_tail ON conversation_messages (app_id, conversation_id, id)"))


def main() -> None:
    """Preview without connecting; --apply is an explicit rollout operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print("Adds users.must_change_password (false), temporary_password_expires_at (null), and scoped conversation tail index.")
    print("Existing accounts/passwords are preserved. Deploy schema before the new API image.")
    if args.apply:
        from nemo_mcp_guardrails.database.connection import engine
        with engine.begin() as connection:
            migrate(connection)
        print("Security foundation schema applied.")


if __name__ == "__main__":
    main()
