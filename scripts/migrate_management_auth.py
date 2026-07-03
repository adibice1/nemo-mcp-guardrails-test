from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import text

from nemo_mcp_guardrails.database.connection import engine


def migrate_management_auth_schema() -> None:
    """Add management roles and editable profile fields to existing users."""

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS system_role VARCHAR(20)
                NOT NULL DEFAULT 'developer'
                """
            )
        )
        connection.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(320)")
        )
        connection.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(320)")
        )
        connection.execute(
            text("UPDATE users SET name = email WHERE name IS NULL OR name = ''")
        )
        connection.execute(
            text(
                "UPDATE users SET username = email "
                "WHERE username IS NULL OR username = ''"
            )
        )
        connection.execute(
            text("ALTER TABLE users ALTER COLUMN name SET NOT NULL")
        )
        connection.execute(
            text("ALTER TABLE users ALTER COLUMN username SET NOT NULL")
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username "
                "ON users (username)"
            )
        )


def main() -> None:
    """Apply and report the management-auth schema migration."""

    migrate_management_auth_schema()
    print("Management authentication migration complete.")
    print("- users.system_role is available with developer default.")
    print("- users.name and users.username are backfilled from email.")


if __name__ == "__main__":
    main()
