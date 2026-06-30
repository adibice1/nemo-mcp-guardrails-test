from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import text

from nemo_mcp_guardrails.database.connection import engine


def main() -> None:
    """Add assignment display names and backfill policy descriptions."""

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE app_policy_assignments "
                "ADD COLUMN IF NOT EXISTS display_name VARCHAR(300)"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE global_policy_assignments "
                "ADD COLUMN IF NOT EXISTS display_name VARCHAR(300)"
            )
        )
        app_result = connection.execute(
            text(
                "UPDATE app_policy_assignments AS assignment "
                "SET display_name = NULLIF(BTRIM(policy.description), '') "
                "FROM policies AS policy "
                "WHERE assignment.policy_id = policy.id "
                "AND assignment.display_name IS NULL "
                "AND NULLIF(BTRIM(policy.description), '') IS NOT NULL"
            )
        )
        global_result = connection.execute(
            text(
                "UPDATE global_policy_assignments AS assignment "
                "SET display_name = NULLIF(BTRIM(policy.description), '') "
                "FROM policies AS policy "
                "WHERE assignment.policy_id = policy.id "
                "AND assignment.display_name IS NULL "
                "AND NULLIF(BTRIM(policy.description), '') IS NOT NULL"
            )
        )

    print("Policy assignment display-name migration complete.")
    print(f"- app assignments backfilled: {app_result.rowcount}")
    print(f"- global assignments backfilled: {global_result.rowcount}")


if __name__ == "__main__":
    main()
