from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import text

from nemo_mcp_guardrails.database.connection import create_database_tables, engine


MIGRATION_STATEMENTS = (
    """
    ALTER TABLE policies
    ADD COLUMN IF NOT EXISTS connector_id INTEGER
        REFERENCES connectors(id) ON DELETE RESTRICT
    """,
    """
    ALTER TABLE policies
    ADD COLUMN IF NOT EXISTS action_id INTEGER
        REFERENCES connector_actions(id) ON DELETE RESTRICT
    """,
    """
    ALTER TABLE policies
    ADD COLUMN IF NOT EXISTS resource_id INTEGER
        REFERENCES connector_resources(id) ON DELETE RESTRICT
    """,
    """
    ALTER TABLE policies
    ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100
    """,
    """
    ALTER TABLE policies
    ADD COLUMN IF NOT EXISTS conditions JSONB NOT NULL DEFAULT '{}'::jsonb
    """,
    """
    ALTER TABLE policies
    ADD COLUMN IF NOT EXISTS policy_version INTEGER NOT NULL DEFAULT 1
    """,
    """
    ALTER TABLE compiled_policy_rules
    ADD COLUMN IF NOT EXISTS policy_version INTEGER NOT NULL DEFAULT 1
    """,
    """
    ALTER TABLE compiled_policy_rules
    ADD COLUMN IF NOT EXISTS stale BOOLEAN NOT NULL DEFAULT FALSE
    """,
    "CREATE INDEX IF NOT EXISTS ix_policies_connector_id ON policies(connector_id)",
    "CREATE INDEX IF NOT EXISTS ix_policies_action_id ON policies(action_id)",
    "CREATE INDEX IF NOT EXISTS ix_policies_resource_id ON policies(resource_id)",
    """
    CREATE INDEX IF NOT EXISTS ix_compiled_policy_rules_stale
    ON compiled_policy_rules(stale)
    """,
)


BACKFILL_STATEMENTS = (
    """
    UPDATE policies AS policy
    SET connector_id = connector.id
    FROM connectors AS connector
    WHERE policy.connector_id IS NULL
      AND policy.connector = connector.name
    """,
    """
    UPDATE policies AS policy
    SET connector_id = connector.id
    FROM connectors AS connector
    WHERE policy.connector_id IS NULL
      AND policy.policy_type = 'output'
      AND connector.name = 'global'
    """,
    """
    UPDATE policies AS policy
    SET action_id = action.id
    FROM connector_actions AS action
    WHERE policy.action_id IS NULL
      AND policy.connector_id = action.connector_id
      AND policy.action = action.name
    """,
    """
    UPDATE policies AS policy
    SET resource_id = resource.id
    FROM connector_resources AS resource
    WHERE policy.resource_id IS NULL
      AND policy.connector_id = resource.connector_id
      AND policy.resource = resource.name
    """,
    """
    UPDATE compiled_policy_rules AS compiled
    SET policy_version = policy.policy_version,
        stale = FALSE
    FROM policies AS policy
    WHERE compiled.policy_id = policy.id
    """,
)


COUNT_QUERY = """
SELECT
    COUNT(*) AS total_policies,
    COUNT(*) FILTER (WHERE connector_id IS NOT NULL) AS policies_with_connector_id,
    COUNT(*) FILTER (
        WHERE policy_type = 'input'
          AND action_id IS NOT NULL
          AND resource_id IS NOT NULL
    ) AS normalized_input_policies
FROM policies
"""


def main() -> None:
    """Add and backfill normalized policy references and rule lifecycle fields."""

    create_database_tables()

    with engine.begin() as connection:
        for statement in MIGRATION_STATEMENTS:
            connection.execute(text(statement))

        for statement in BACKFILL_STATEMENTS:
            connection.execute(text(statement))

        counts = connection.execute(text(COUNT_QUERY)).mappings().one()

    print("Normalized policy-reference migration complete.")
    print(f"- total policies: {counts['total_policies']}")
    print(
        "- policies with connector_id: "
        f"{counts['policies_with_connector_id']}"
    )
    print(f"- normalized input policies: {counts['normalized_input_policies']}")


if __name__ == "__main__":
    main()
