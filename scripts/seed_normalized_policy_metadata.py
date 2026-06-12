from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.connection import (
    SessionLocal,
    create_database_tables,
)
from nemo_mcp_guardrails.database.models import (
    AllowedTestCaseExpectedToolRecord,
    AllowedTestCaseRecord,
    ConnectorActionRecord,
    ConnectorRecord,
    ConnectorResourceRecord,
    ConnectorToolMappingRecord,
)
from nemo_mcp_guardrails.database.test_case_loader import parse_expected_tools
from nemo_mcp_guardrails.policy_compiler import (
    GITHUB_ACTION_DISPLAY_NAMES,
    GITHUB_METADATA_TOOL_MAPPINGS,
    GITHUB_RESOURCE_DISPLAY_NAMES,
)


def get_or_create_connector(
    db: Session,
    name: str,
    display_name: str,
) -> ConnectorRecord:
    """Return an existing connector row or create it."""

    connector = (
        db.query(ConnectorRecord)
        .filter(ConnectorRecord.name == name)
        .one_or_none()
    )

    if connector:
        return connector

    connector = ConnectorRecord(name=name, display_name=display_name)
    db.add(connector)
    db.flush()
    return connector


def get_or_create_action(
    db: Session,
    connector_id: int,
    name: str,
    display_name: str,
) -> ConnectorActionRecord:
    """Return an existing connector action row or create it."""

    action = (
        db.query(ConnectorActionRecord)
        .filter(
            ConnectorActionRecord.connector_id == connector_id,
            ConnectorActionRecord.name == name,
        )
        .one_or_none()
    )

    if action:
        return action

    action = ConnectorActionRecord(
        connector_id=connector_id,
        name=name,
        display_name=display_name,
    )
    db.add(action)
    db.flush()
    return action


def get_or_create_resource(
    db: Session,
    connector_id: int,
    name: str,
    display_name: str,
) -> ConnectorResourceRecord:
    """Return an existing connector resource row or create it."""

    resource = (
        db.query(ConnectorResourceRecord)
        .filter(
            ConnectorResourceRecord.connector_id == connector_id,
            ConnectorResourceRecord.name == name,
        )
        .one_or_none()
    )

    if resource:
        return resource

    resource = ConnectorResourceRecord(
        connector_id=connector_id,
        name=name,
        display_name=display_name,
    )
    db.add(resource)
    db.flush()
    return resource


def get_or_create_connector_tool_mapping(
    db: Session,
    connector_id: int,
    action_id: int,
    resource_id: int,
    tool_name: str,
) -> ConnectorToolMappingRecord:
    """Return an existing connector/action/resource tool mapping or create it."""

    mapping = (
        db.query(ConnectorToolMappingRecord)
        .filter(
            ConnectorToolMappingRecord.connector_id == connector_id,
            ConnectorToolMappingRecord.action_id == action_id,
            ConnectorToolMappingRecord.resource_id == resource_id,
            ConnectorToolMappingRecord.tool_name == tool_name,
        )
        .one_or_none()
    )

    if mapping:
        return mapping

    mapping = ConnectorToolMappingRecord(
        connector_id=connector_id,
        action_id=action_id,
        resource_id=resource_id,
        tool_name=tool_name,
    )
    db.add(mapping)
    db.flush()
    return mapping


def get_or_create_expected_tool(
    db: Session,
    allowed_test_case_id: int,
    connector_tool_mapping_id: int,
) -> AllowedTestCaseExpectedToolRecord:
    """Return an existing allowed-test expected-tool row or create it."""

    expected_tool = (
        db.query(AllowedTestCaseExpectedToolRecord)
        .filter(
            AllowedTestCaseExpectedToolRecord.allowed_test_case_id
            == allowed_test_case_id,
            AllowedTestCaseExpectedToolRecord.connector_tool_mapping_id
            == connector_tool_mapping_id,
        )
        .one_or_none()
    )

    if expected_tool:
        return expected_tool

    expected_tool = AllowedTestCaseExpectedToolRecord(
        allowed_test_case_id=allowed_test_case_id,
        connector_tool_mapping_id=connector_tool_mapping_id,
    )
    db.add(expected_tool)
    db.flush()
    return expected_tool


def backfill_allowed_test_expected_tools(db: Session) -> int:
    """Backfill allowed test expected-tool rows from comma-separated tool names."""

    backfilled_count = 0
    allowed_test_cases = list(
        db.scalars(select(AllowedTestCaseRecord).order_by(AllowedTestCaseRecord.id))
    )

    for test_case in allowed_test_cases:
        for tool_name in parse_expected_tools(test_case.expected_tools):
            connector_tool_mappings = list(
                db.scalars(
                    select(ConnectorToolMappingRecord).where(
                        ConnectorToolMappingRecord.tool_name == tool_name,
                        ConnectorToolMappingRecord.enabled.is_(True),
                    )
                )
            )

            for connector_tool_mapping in connector_tool_mappings:
                get_or_create_expected_tool(
                    db,
                    test_case.id,
                    connector_tool_mapping.id,
                )
                backfilled_count += 1

    return backfilled_count


def main() -> None:
    """Seed normalized connector/action/resource/tool metadata."""

    create_database_tables()

    with SessionLocal() as db:
        get_or_create_connector(db, "global", "Global")
        github_connector = get_or_create_connector(db, "github", "GitHub")

        actions = {
            action_name: get_or_create_action(
                db,
                github_connector.id,
                action_name,
                GITHUB_ACTION_DISPLAY_NAMES[action_name],
            )
            for action_name, _resource_name in GITHUB_METADATA_TOOL_MAPPINGS
        }

        resources = {
            resource_name: get_or_create_resource(
                db,
                github_connector.id,
                resource_name,
                GITHUB_RESOURCE_DISPLAY_NAMES[resource_name],
            )
            for _action_name, resource_name in GITHUB_METADATA_TOOL_MAPPINGS
        }

        mapping_count = 0

        for (
            action_name,
            resource_name,
        ), tool_names in GITHUB_METADATA_TOOL_MAPPINGS.items():
            for tool_name in tool_names:
                get_or_create_connector_tool_mapping(
                    db,
                    github_connector.id,
                    actions[action_name].id,
                    resources[resource_name].id,
                    tool_name,
                )
                mapping_count += 1

        expected_tool_count = backfill_allowed_test_expected_tools(db)

        db.commit()

    print("Normalized policy metadata seeded.")
    print("- connectors: global, github")
    print(f"- github connector actions: {len(actions)}")
    print(f"- github connector resources: {len(resources)}")
    print(f"- github connector tool mappings: {mapping_count}")
    print(f"- allowed test expected-tool links: {expected_tool_count}")


if __name__ == "__main__":
    main()
