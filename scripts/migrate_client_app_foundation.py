from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import func, select

from nemo_mcp_guardrails.database.connection import (
    SessionLocal,
    create_database_tables,
)
from nemo_mcp_guardrails.database.models import (
    AppRecord,
    LlmConfigRecord,
    UserRecord,
)


def main() -> None:
    """Create and report the initial client-app foundation tables."""

    create_database_tables()

    with SessionLocal() as db:
        user_count = db.scalar(select(func.count()).select_from(UserRecord))
        llm_config_count = db.scalar(
            select(func.count()).select_from(LlmConfigRecord)
        )
        app_count = db.scalar(
            select(func.count()).select_from(AppRecord)
        )

    print("Client-app foundation migration complete.")
    print(f"- users: {user_count}")
    print(f"- llm configs: {llm_config_count}")
    print(f"- apps: {app_count}")


if __name__ == "__main__":
    main()
