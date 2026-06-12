from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import func, select

from nemo_mcp_guardrails.database.connection import (
    SessionLocal,
    create_database_tables,
)
from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppUserRecord,
)


def main() -> None:
    """Create and report app ownership and connector relationship tables."""

    create_database_tables()

    with SessionLocal() as db:
        app_user_count = db.scalar(
            select(func.count()).select_from(AppUserRecord)
        )
        app_connector_count = db.scalar(
            select(func.count()).select_from(AppConnectorRecord)
        )

    print("App relationship migration complete.")
    print(f"- app user links: {app_user_count}")
    print(f"- app connector links: {app_connector_count}")


if __name__ == "__main__":
    main()
