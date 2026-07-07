from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import select

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import AppRecord, AppUserRecord, UserRecord


def main() -> None:
    """Link every current user to every current app without creating duplicates."""

    created = 0
    with SessionLocal() as db:
        users = list(db.scalars(select(UserRecord).order_by(UserRecord.id)))
        apps = list(db.scalars(select(AppRecord).order_by(AppRecord.id)))

        for user in users:
            for app in apps:
                existing = db.scalar(
                    select(AppUserRecord).where(
                        AppUserRecord.user_id == user.id,
                        AppUserRecord.app_id == app.id,
                    )
                )
                if existing is None:
                    db.add(
                        AppUserRecord(
                            user_id=user.id,
                            app_id=app.id,
                            role="admin",
                        )
                    )
                    created += 1

        db.commit()

    print("Existing app developer-link backfill complete.")
    print(f"- users inspected: {len(users)}")
    print(f"- apps inspected: {len(apps)}")
    print(f"- app developer links created: {created}")


if __name__ == "__main__":
    main()
