from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import inspect, text

from nemo_mcp_guardrails.database.connection import engine


TABLE_RENAMES = (
    ("apps", "connectors"),
    ("client_apps", "apps"),
    ("app_actions", "connector_actions"),
    ("app_resources", "connector_resources"),
    ("tool_mappings", "connector_tool_mappings"),
)

COLUMN_RENAMES = (
    ("connector_actions", "app_id", "connector_id"),
    ("connector_resources", "app_id", "connector_id"),
    ("connector_tool_mappings", "app_id", "connector_id"),
    ("policies", "app", "connector"),
    ("policies", "app_id", "connector_id"),
    (
        "allowed_test_case_expected_tools",
        "tool_mapping_id",
        "connector_tool_mapping_id",
    ),
)

CONSTRAINT_RENAMES = (
    (
        "apps",
        "client_apps_main_llm_config_id_fkey",
        "apps_main_llm_config_id_fkey",
    ),
    (
        "apps",
        "client_apps_guardrail_llm_config_id_fkey",
        "apps_guardrail_llm_config_id_fkey",
    ),
    (
        "connector_actions",
        "app_actions_app_id_fkey",
        "connector_actions_connector_id_fkey",
    ),
    (
        "connector_actions",
        "uq_app_actions_app_id_name",
        "uq_connector_actions_connector_id_name",
    ),
    (
        "connector_resources",
        "app_resources_app_id_fkey",
        "connector_resources_connector_id_fkey",
    ),
    (
        "connector_resources",
        "uq_app_resources_app_id_name",
        "uq_connector_resources_connector_id_name",
    ),
    (
        "connector_tool_mappings",
        "tool_mappings_app_id_fkey",
        "connector_tool_mappings_connector_id_fkey",
    ),
    (
        "connector_tool_mappings",
        "tool_mappings_action_id_fkey",
        "connector_tool_mappings_action_id_fkey",
    ),
    (
        "connector_tool_mappings",
        "tool_mappings_resource_id_fkey",
        "connector_tool_mappings_resource_id_fkey",
    ),
    (
        "connector_tool_mappings",
        "uq_tool_mappings_app_action_resource_tool",
        "uq_connector_tool_mappings_connector_action_resource_tool",
    ),
    (
        "policies",
        "policies_app_id_fkey",
        "policies_connector_id_fkey",
    ),
    (
        "allowed_test_case_expected_tools",
        "allowed_test_case_expected_tools_tool_mapping_id_fkey",
        "allowed_test_case_expected_tools_connector_tool_mapping_id_fkey",
    ),
    (
        "allowed_test_case_expected_tools",
        "uq_allowed_test_case_expected_tools_case_tool",
        "uq_allowed_test_case_expected_tools_case_connector_tool",
    ),
)

INDEX_RENAMES = (
    ("ix_apps_id", "ix_connectors_id"),
    ("ix_apps_name", "ix_connectors_name"),
    ("ix_client_apps_id", "ix_apps_id"),
    ("ix_client_apps_name", "ix_apps_name"),
    ("ix_client_apps_client_id", "ix_apps_client_id"),
    (
        "ix_client_apps_main_llm_config_id",
        "ix_apps_main_llm_config_id",
    ),
    (
        "ix_client_apps_guardrail_llm_config_id",
        "ix_apps_guardrail_llm_config_id",
    ),
    ("ix_app_actions_id", "ix_connector_actions_id"),
    ("ix_app_actions_app_id", "ix_connector_actions_connector_id"),
    ("ix_app_actions_name", "ix_connector_actions_name"),
    ("ix_app_resources_id", "ix_connector_resources_id"),
    ("ix_app_resources_app_id", "ix_connector_resources_connector_id"),
    ("ix_app_resources_name", "ix_connector_resources_name"),
    ("ix_tool_mappings_id", "ix_connector_tool_mappings_id"),
    (
        "ix_tool_mappings_app_id",
        "ix_connector_tool_mappings_connector_id",
    ),
    ("ix_tool_mappings_action_id", "ix_connector_tool_mappings_action_id"),
    (
        "ix_tool_mappings_resource_id",
        "ix_connector_tool_mappings_resource_id",
    ),
    ("ix_tool_mappings_tool_name", "ix_connector_tool_mappings_tool_name"),
    ("ix_policies_app_id", "ix_policies_connector_id"),
    (
        "ix_allowed_test_case_expected_tools_tool_mapping_id",
        "ix_allowed_test_case_expected_tools_connector_tool_mapping_id",
    ),
)


def _rename_constraint(
    connection,
    table_name: str,
    old_name: str,
    new_name: str,
) -> None:
    """Rename a constraint when the old name still exists."""

    exists = connection.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = :old_name
                  AND conrelid = CAST(:table_name AS regclass)
            )
            """
        ),
        {"old_name": old_name, "table_name": table_name},
    ).scalar_one()

    if exists:
        connection.execute(
            text(
                f'ALTER TABLE "{table_name}" '
                f'RENAME CONSTRAINT "{old_name}" TO "{new_name}"'
            )
        )


def _rename_index(connection, old_name: str, new_name: str) -> None:
    """Rename an index when the old name exists and the new name does not."""

    old_exists, new_exists = connection.execute(
        text(
            """
            SELECT
                to_regclass(:old_name) IS NOT NULL,
                to_regclass(:new_name) IS NOT NULL
            """
        ),
        {"old_name": old_name, "new_name": new_name},
    ).one()

    if old_exists and not new_exists:
        connection.execute(text(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"'))


def main() -> None:
    """Rename connector-shaped schema objects while preserving current data."""

    current_tables = set(inspect(engine).get_table_names())

    if "client_apps" not in current_tables:
        if {"apps", "connectors"}.issubset(current_tables):
            with engine.begin() as connection:
                for table_name, old_name, new_name in CONSTRAINT_RENAMES:
                    _rename_constraint(connection, table_name, old_name, new_name)

                for old_name, new_name in INDEX_RENAMES:
                    _rename_index(connection, old_name, new_name)

            print("Connector terminology migration already applied.")
            print("- remaining constraint and index names normalized")
            return
        raise RuntimeError(
            "Cannot identify the expected pre-migration or post-migration schema."
        )

    required_tables = {
        old_name
        for old_name, _new_name in TABLE_RENAMES
    } | {
        "policies",
        "allowed_test_case_expected_tools",
    }
    missing_tables = sorted(required_tables - current_tables)
    if missing_tables:
        raise RuntimeError(
            "Cannot migrate because required tables are missing: "
            + ", ".join(missing_tables)
        )

    with engine.begin() as connection:
        for old_name, new_name in TABLE_RENAMES:
            connection.execute(
                text(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"')
            )

        for table_name, old_name, new_name in COLUMN_RENAMES:
            connection.execute(
                text(
                    f'ALTER TABLE "{table_name}" '
                    f'RENAME COLUMN "{old_name}" TO "{new_name}"'
                )
            )

        for table_name, old_name, new_name in CONSTRAINT_RENAMES:
            _rename_constraint(connection, table_name, old_name, new_name)

        for old_name, new_name in INDEX_RENAMES:
            _rename_index(connection, old_name, new_name)

    migrated_tables = set(inspect(engine).get_table_names())

    print("Connector terminology migration complete.")
    print(f"- apps exists: {'apps' in migrated_tables}")
    print(f"- connectors exists: {'connectors' in migrated_tables}")
    print(f"- connector actions exists: {'connector_actions' in migrated_tables}")
    print(f"- connector resources exists: {'connector_resources' in migrated_tables}")
    print(
        "- connector tool mappings exists: "
        f"{'connector_tool_mappings' in migrated_tables}"
    )


if __name__ == "__main__":
    main()
