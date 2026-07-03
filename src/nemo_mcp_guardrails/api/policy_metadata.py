from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.policy_schemas import (
    PolicyActionOption,
    PolicyConnectorOption,
    PolicyResourceOption,
)
from nemo_mcp_guardrails.api.management_auth import require_management_user
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    ConnectorActionRecord,
    ConnectorRecord,
    ConnectorResourceRecord,
    ConnectorToolMappingRecord,
)


router = APIRouter(
    tags=["policy-metadata"],
    dependencies=[Depends(require_management_user)],
)


@router.get("/policy-options", response_model=list[PolicyConnectorOption])
def list_policy_options(
    db: Session = Depends(get_db),
) -> list[PolicyConnectorOption]:
    """Return enabled connector/action/resource combinations for policy forms."""

    rows = db.execute(
        select(
            ConnectorRecord.name,
            ConnectorRecord.display_name,
            ConnectorActionRecord.name,
            ConnectorActionRecord.display_name,
            ConnectorResourceRecord.name,
            ConnectorResourceRecord.display_name,
        )
        .join(
            ConnectorToolMappingRecord,
            ConnectorToolMappingRecord.connector_id == ConnectorRecord.id,
        )
        .join(
            ConnectorActionRecord,
            ConnectorActionRecord.id == ConnectorToolMappingRecord.action_id,
        )
        .join(
            ConnectorResourceRecord,
            ConnectorResourceRecord.id == ConnectorToolMappingRecord.resource_id,
        )
        .where(
            ConnectorRecord.enabled.is_(True),
            ConnectorActionRecord.enabled.is_(True),
            ConnectorResourceRecord.enabled.is_(True),
            ConnectorToolMappingRecord.enabled.is_(True),
        )
        .distinct()
        .order_by(
            ConnectorRecord.display_name,
            ConnectorActionRecord.display_name,
            ConnectorResourceRecord.display_name,
        )
    ).all()

    catalog: dict[
        str,
        tuple[str, dict[str, tuple[str, dict[str, str]]]],
    ] = {}
    for (
        connector_name,
        connector_label,
        action_name,
        action_label,
        resource_name,
        resource_label,
    ) in rows:
        _connector_label, actions = catalog.setdefault(
            connector_name,
            (connector_label, {}),
        )
        _action_label, resources = actions.setdefault(
            action_name,
            (action_label, {}),
        )
        resources[resource_name] = resource_label

    return [
        PolicyConnectorOption(
            value=connector_name,
            label=connector_label,
            actions=[
                PolicyActionOption(
                    value=action_name,
                    label=action_label,
                    resources=[
                        PolicyResourceOption(value=value, label=label)
                        for value, label in resources.items()
                    ],
                )
                for action_name, (action_label, resources) in actions.items()
            ],
        )
        for connector_name, (connector_label, actions) in catalog.items()
    ]
