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
    AppActionRecord,
    AppRecord,
    AppResourceRecord,
    ToolMappingRecord,
)
from nemo_mcp_guardrails.database.test_case_loader import parse_expected_tools
from nemo_mcp_guardrails.policy_compiler import (
    GITHUB_ACTION_DISPLAY_NAMES,
    GITHUB_METADATA_TOOL_MAPPINGS,
    GITHUB_RESOURCE_DISPLAY_NAMES,
)


def get_or_create_app(
    db: Session,
    name: str,
    display_name: str,
) -> AppRecord:
    """Return an existing app row or create it."""

    app = db.query(AppRecord).filter(AppRecord.name == name).one_or_none()

    if app:
        return app

    app = AppRecord(name=name, display_name=display_name)
    db.add(app)
    db.flush()
    return app


def get_or_create_action(
    db: Session,
    app_id: int,
    name: str,
    display_name: str,
) -> AppActionRecord:
    """Return an existing app action row or create it."""

    action = (
        db.query(AppActionRecord)
        .filter(
            AppActionRecord.app_id == app_id,
            AppActionRecord.name == name,
        )
        .one_or_none()
    )

    if action:
        return action

    action = AppActionRecord(
        app_id=app_id,
        name=name,
        display_name=display_name,
    )
    db.add(action)
    db.flush()
    return action


def get_or_create_resource(
    db: Session,
    app_id: int,
    name: str,
    display_name: str,
) -> AppResourceRecord:
    """Return an existing app resource row or create it."""

    resource = (
        db.query(AppResourceRecord)
        .filter(
            AppResourceRecord.app_id == app_id,
            AppResourceRecord.name == name,
        )
        .one_or_none()
    )

    if resource:
        return resource

    resource = AppResourceRecord(
        app_id=app_id,
        name=name,
        display_name=display_name,
    )
    db.add(resource)
    db.flush()
    return resource


def get_or_create_tool_mapping(
    db: Session,
    app_id: int,
    action_id: int,
    resource_id: int,
    tool_name: str,
) -> ToolMappingRecord:
    """Return an existing app/action/resource tool mapping or create it."""

    mapping = (
        db.query(ToolMappingRecord)
        .filter(
            ToolMappingRecord.app_id == app_id,
            ToolMappingRecord.action_id == action_id,
            ToolMappingRecord.resource_id == resource_id,
            ToolMappingRecord.tool_name == tool_name,
        )
        .one_or_none()
    )

    if mapping:
        return mapping

    mapping = ToolMappingRecord(
        app_id=app_id,
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
    tool_mapping_id: int,
) -> AllowedTestCaseExpectedToolRecord:
    """Return an existing allowed-test expected-tool row or create it."""

    expected_tool = (
        db.query(AllowedTestCaseExpectedToolRecord)
        .filter(
            AllowedTestCaseExpectedToolRecord.allowed_test_case_id
            == allowed_test_case_id,
            AllowedTestCaseExpectedToolRecord.tool_mapping_id == tool_mapping_id,
        )
        .one_or_none()
    )

    if expected_tool:
        return expected_tool

    expected_tool = AllowedTestCaseExpectedToolRecord(
        allowed_test_case_id=allowed_test_case_id,
        tool_mapping_id=tool_mapping_id,
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
            tool_mappings = list(
                db.scalars(
                    select(ToolMappingRecord).where(
                        ToolMappingRecord.tool_name == tool_name,
                        ToolMappingRecord.enabled.is_(True),
                    )
                )
            )

            for tool_mapping in tool_mappings:
                get_or_create_expected_tool(
                    db,
                    test_case.id,
                    tool_mapping.id,
                )
                backfilled_count += 1

    return backfilled_count


def main() -> None:
    """Seed normalized app/action/resource/tool metadata."""

    create_database_tables()

    with SessionLocal() as db:
        get_or_create_app(db, "global", "Global")
        github_app = get_or_create_app(db, "github", "GitHub")

        actions = {
            action_name: get_or_create_action(
                db,
                github_app.id,
                action_name,
                GITHUB_ACTION_DISPLAY_NAMES[action_name],
            )
            for action_name, _resource_name in GITHUB_METADATA_TOOL_MAPPINGS
        }

        resources = {
            resource_name: get_or_create_resource(
                db,
                github_app.id,
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
                get_or_create_tool_mapping(
                    db,
                    github_app.id,
                    actions[action_name].id,
                    resources[resource_name].id,
                    tool_name,
                )
                mapping_count += 1

        expected_tool_count = backfill_allowed_test_expected_tools(db)

        db.commit()

    print("Normalized policy metadata seeded.")
    print("- apps: global, github")
    print(f"- github actions: {len(actions)}")
    print(f"- github resources: {len(resources)}")
    print(f"- github tool mappings: {mapping_count}")
    print(f"- allowed test expected-tool links: {expected_tool_count}")


if __name__ == "__main__":
    main()
