from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.api.assignment_serializers import (
    app_label,
    serialize_app,
    serialize_app_connector,
    serialize_app_policy_assignment,
    serialize_effective_app_assignment,
    serialize_effective_global_assignment,
)
from nemo_mcp_guardrails.api.app_schemas import (
    AppConnectorCreate,
    AppConnectorRead,
    AppConnectorUpdate,
    AppCreate,
    AppPolicyAssignmentRead,
    AppRead,
    AppUpdate,
    EffectivePolicyAssignmentsRead,
    PolicyAssignmentBulkDelete,
    PolicyAssignmentBulkDeleteResponse,
    PolicyAssignmentBulkUpdate,
    PolicyAssignmentCreate,
    PolicyAssignmentUpdate,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppPolicyAssignmentRecord,
    AppRecord,
    AppUserRecord,
    ConnectorRecord,
    GlobalPolicyAssignmentRecord,
    LlmConfigRecord,
    PolicyRecord,
    UserRecord,
)
from nemo_mcp_guardrails.management_permissions import require_app_route_access


router = APIRouter(
    prefix="/apps",
    tags=["apps"],
    dependencies=[Depends(require_app_route_access)],
)


def _require_app(app_id: int, db: Session) -> AppRecord:
    """Return one app or raise a not-found response."""

    app = db.get(AppRecord, app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return app


def _require_app_by_client_id(client_id: str, db: Session) -> AppRecord:
    """Return one app by client ID or raise a not-found response."""

    app = db.scalar(select(AppRecord).where(AppRecord.client_id == client_id))
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return app


def _require_connector_by_reference(
    connector_ref: str,
    db: Session,
) -> ConnectorRecord:
    """Return one connector by numeric ID or connector name."""

    connector = None
    if connector_ref.isdigit():
        connector = db.get(ConnectorRecord, int(connector_ref))

    if connector is None:
        connector = db.scalar(
            select(ConnectorRecord).where(ConnectorRecord.name == connector_ref)
        )

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    return connector


def _require_connector_from_payload(
    payload: AppConnectorCreate,
    db: Session,
) -> ConnectorRecord:
    """Return the connector referenced by create payload."""

    if payload.connector_id is None and payload.connector_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide connector_id or connector_name",
        )

    if payload.connector_id is not None:
        connector = db.get(ConnectorRecord, payload.connector_id)
    else:
        connector = db.scalar(
            select(ConnectorRecord).where(
                ConnectorRecord.name == payload.connector_name
            )
        )

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    return connector


def _unique_policy_ids(policy_ids: list[int]) -> list[int]:
    """Return unique policy IDs while preserving request order."""

    return list(dict.fromkeys(policy_ids))


def _require_policies(policy_ids: list[int], db: Session) -> dict[int, PolicyRecord]:
    """Return policies keyed by ID or raise for missing IDs."""

    unique_ids = _unique_policy_ids(policy_ids)
    policies = list(
        db.scalars(select(PolicyRecord).where(PolicyRecord.id.in_(unique_ids)))
    )
    policies_by_id = {policy.id: policy for policy in policies}
    missing_ids = [policy_id for policy_id in unique_ids if policy_id not in policies_by_id]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy IDs not found: {missing_ids}",
        )
    return policies_by_id


def _validate_llm_config_ids(values: dict[str, object], db: Session) -> None:
    """Validate any provided main-agent or guardrail LLM references."""

    for field in ("main_llm_config_id", "guardrail_llm_config_id"):
        config_id = values.get(field)
        if config_id is not None and not db.get(LlmConfigRecord, config_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown {field}: {config_id}",
            )


def _list_policy_assignments_for_app(
    app_id: int,
    db: Session,
) -> list[dict[str, object]]:
    """Return serialized policy assignments for one app."""

    assignments = list(
        db.scalars(
            select(AppPolicyAssignmentRecord)
            .where(AppPolicyAssignmentRecord.app_id == app_id)
            .order_by(AppPolicyAssignmentRecord.id)
        )
    )
    return [serialize_app_policy_assignment(assignment) for assignment in assignments]


def _list_app_connectors(
    app_id: int,
    db: Session,
) -> list[dict[str, object]]:
    """Return connector links for one app."""

    links = list(
        db.scalars(
            select(AppConnectorRecord)
            .where(AppConnectorRecord.app_id == app_id)
            .order_by(AppConnectorRecord.id)
        )
    )
    return [serialize_app_connector(link) for link in links]


def _link_connector_to_app(
    app_id: int,
    payload: AppConnectorCreate,
    db: Session,
) -> dict[str, object]:
    """Create or update one app connector link."""

    connector = _require_connector_from_payload(payload, db)
    link = db.scalar(
        select(AppConnectorRecord).where(
            AppConnectorRecord.app_id == app_id,
            AppConnectorRecord.connector_id == connector.id,
        )
    )

    if link is None:
        link = AppConnectorRecord(
            app_id=app_id,
            connector_id=connector.id,
            credential_reference=payload.credential_reference,
            enabled=payload.enabled,
        )
        db.add(link)
    else:
        link.credential_reference = payload.credential_reference
        link.enabled = payload.enabled

    db.commit()
    db.refresh(link)
    return serialize_app_connector(link)


def _require_app_connector_link(
    app_id: int,
    connector_ref: str,
    db: Session,
) -> AppConnectorRecord:
    """Return one app connector link or raise a not-found response."""

    connector = _require_connector_by_reference(connector_ref, db)
    link = db.scalar(
        select(AppConnectorRecord).where(
            AppConnectorRecord.app_id == app_id,
            AppConnectorRecord.connector_id == connector.id,
        )
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App connector link not found",
        )

    return link


def _update_app_connector_link(
    app_id: int,
    connector_ref: str,
    payload: AppConnectorUpdate,
    db: Session,
) -> dict[str, object]:
    """Update one app connector link."""

    link = _require_app_connector_link(app_id, connector_ref, db)
    values = payload.model_dump(exclude_unset=True)

    for field, value in values.items():
        setattr(link, field, value)

    db.commit()
    db.refresh(link)
    return serialize_app_connector(link)


def _delete_app_connector_link(
    app_id: int,
    connector_ref: str,
    db: Session,
) -> None:
    """Delete one app connector link."""

    link = _require_app_connector_link(app_id, connector_ref, db)
    db.delete(link)
    db.commit()


def _assign_policies_to_app(
    app_id: int,
    payload: PolicyAssignmentCreate,
    db: Session,
) -> list[dict[str, object]]:
    """Create or update one or more policy assignments for one app."""

    policy_ids = _unique_policy_ids(payload.policy_ids)
    _require_policies(policy_ids, db)

    existing_assignments = list(
        db.scalars(
            select(AppPolicyAssignmentRecord).where(
                AppPolicyAssignmentRecord.app_id == app_id,
                AppPolicyAssignmentRecord.policy_id.in_(policy_ids),
            )
        )
    )
    assignments_by_policy_id = {
        assignment.policy_id: assignment for assignment in existing_assignments
    }
    assignments: list[AppPolicyAssignmentRecord] = []

    for policy_id in policy_ids:
        assignment = assignments_by_policy_id.get(policy_id)
        if assignment is None:
            assignment = AppPolicyAssignmentRecord(
                app_id=app_id,
                policy_id=policy_id,
                enabled=payload.enabled,
            )
            db.add(assignment)
        else:
            assignment.enabled = payload.enabled
        assignments.append(assignment)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more policies could not be assigned to the app",
        ) from error

    for assignment in assignments:
        db.refresh(assignment)
    return [serialize_app_policy_assignment(assignment) for assignment in assignments]


def _require_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    db: Session,
) -> AppPolicyAssignmentRecord:
    """Return one app policy assignment or raise a not-found response."""

    assignment = db.scalar(
        select(AppPolicyAssignmentRecord).where(
            AppPolicyAssignmentRecord.id == assignment_id,
            AppPolicyAssignmentRecord.app_id == app_id,
        )
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App policy assignment not found",
        )
    return assignment


def _require_app_policy_assignments_by_policy_ids(
    app_id: int,
    policy_ids: list[int],
    db: Session,
) -> list[AppPolicyAssignmentRecord]:
    """Return app assignments by policy IDs or raise for missing assignments."""

    unique_ids = _unique_policy_ids(policy_ids)
    assignments = list(
        db.scalars(
            select(AppPolicyAssignmentRecord).where(
                AppPolicyAssignmentRecord.app_id == app_id,
                AppPolicyAssignmentRecord.policy_id.in_(unique_ids),
            )
        )
    )
    assignments_by_policy_id = {
        assignment.policy_id: assignment for assignment in assignments
    }
    missing_ids = [
        policy_id for policy_id in unique_ids if policy_id not in assignments_by_policy_id
    ]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy assignments not found for policy IDs: {missing_ids}",
        )
    return [assignments_by_policy_id[policy_id] for policy_id in unique_ids]


def _update_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    payload: PolicyAssignmentUpdate,
    db: Session,
) -> dict[str, object]:
    """Enable or disable one app-specific policy assignment."""

    assignment = _require_app_policy_assignment(app_id, assignment_id, db)
    assignment.enabled = payload.enabled
    db.commit()
    db.refresh(assignment)
    return serialize_app_policy_assignment(assignment)


def _bulk_update_app_policy_assignments(
    app_id: int,
    payload: PolicyAssignmentBulkUpdate,
    db: Session,
) -> list[dict[str, object]]:
    """Enable or disable multiple app-specific policy assignments."""

    assignments = _require_app_policy_assignments_by_policy_ids(
        app_id,
        payload.policy_ids,
        db,
    )
    for assignment in assignments:
        assignment.enabled = payload.enabled

    db.commit()
    for assignment in assignments:
        db.refresh(assignment)

    return [serialize_app_policy_assignment(assignment) for assignment in assignments]


def _delete_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    db: Session,
) -> None:
    """Delete one app-specific policy assignment."""

    assignment = _require_app_policy_assignment(app_id, assignment_id, db)
    db.delete(assignment)
    db.commit()


def _bulk_delete_app_policy_assignments(
    app_id: int,
    payload: PolicyAssignmentBulkDelete,
    db: Session,
) -> dict[str, object]:
    """Delete multiple app-specific policy assignments."""

    assignments = _require_app_policy_assignments_by_policy_ids(
        app_id,
        payload.policy_ids,
        db,
    )
    deleted_policy_ids = [assignment.policy_id for assignment in assignments]
    deleted_assignment_ids = [assignment.id for assignment in assignments]

    for assignment in assignments:
        db.delete(assignment)
    db.commit()

    return {
        "deleted_policy_ids": deleted_policy_ids,
        "deleted_assignment_ids": deleted_assignment_ids,
        "deleted_count": len(deleted_assignment_ids),
    }


def _effective_policy_assignments_for_app(
    app: AppRecord,
    db: Session,
) -> dict[str, object]:
    """Return global and app-specific policy assignments for one app."""

    global_assignments = list(
        db.scalars(
            select(GlobalPolicyAssignmentRecord).order_by(
                GlobalPolicyAssignmentRecord.id
            )
        )
    )
    app_assignments = list(
        db.scalars(
            select(AppPolicyAssignmentRecord)
            .where(AppPolicyAssignmentRecord.app_id == app.id)
            .order_by(AppPolicyAssignmentRecord.id)
        )
    )

    serialized_global = [
        serialize_effective_global_assignment(assignment)
        for assignment in global_assignments
    ]
    serialized_app = [
        serialize_effective_app_assignment(assignment)
        for assignment in app_assignments
    ]
    all_assignments = serialized_global + serialized_app
    enabled_count = sum(1 for assignment in all_assignments if assignment["enabled"])

    return {
        "app_id": app.id,
        "app_label": app_label(app),
        "global_assignment_count": len(serialized_global),
        "app_assignment_count": len(serialized_app),
        "enabled_assignment_count": enabled_count,
        "disabled_assignment_count": len(all_assignments) - enabled_count,
        "global_assignments": serialized_global,
        "app_assignments": serialized_app,
    }


@router.get("", response_model=list[AppRead])
def list_apps(
    user: UserRecord = Depends(require_app_route_access),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return all apps for admins or only the current user's apps."""

    query = select(AppRecord).order_by(AppRecord.id)
    if user.system_role != "admin":
        query = (
            query.join(AppUserRecord)
            .where(AppUserRecord.user_id == user.id)
            .distinct()
        )
    apps = list(db.scalars(query))
    return [serialize_app(app) for app in apps]


@router.post("", response_model=AppRead, status_code=status.HTTP_201_CREATED)
def create_app(
    payload: AppCreate,
    user: UserRecord = Depends(require_app_route_access),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Create one client app while storing only its API-key hash."""

    values = payload.model_dump(exclude={"api_key"})
    if user.system_role != "admin" and values.get("guardrail_llm_config_id") is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can select the guardrail LLM",
        )
    _validate_llm_config_ids(values, db)
    app = AppRecord(**values, api_key_hash=hash_api_key(payload.api_key))
    db.add(app)

    try:
        db.flush()
        db.add(AppUserRecord(app_id=app.id, user_id=user.id, role="owner"))
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An app with this client_id already exists",
        ) from error

    db.refresh(app)
    return serialize_app(app)


@router.get("/by-client-id/{client_id}", response_model=AppRead)
def get_app_by_client_id(
    client_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Return one client app by client ID."""

    return serialize_app(_require_app_by_client_id(client_id, db))


@router.get(
    "/by-client-id/{client_id}/effective-policy-assignments",
    response_model=EffectivePolicyAssignmentsRead,
)
def get_effective_policy_assignments_by_client_id(
    client_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Return global and app-specific policy assignments by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _effective_policy_assignments_for_app(app, db)


@router.get(
    "/by-client-id/{client_id}/connectors",
    response_model=list[AppConnectorRead],
)
def list_app_connectors_by_client_id(
    client_id: str,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return connector links belonging to one app by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _list_app_connectors(app.id, db)


@router.post(
    "/by-client-id/{client_id}/connectors",
    response_model=AppConnectorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_app_connector_by_client_id(
    client_id: str,
    payload: AppConnectorCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Create or update one app connector link by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _link_connector_to_app(app.id, payload, db)


@router.put(
    "/by-client-id/{client_id}/connectors/{connector_ref}",
    response_model=AppConnectorRead,
)
def update_app_connector_by_client_id(
    client_id: str,
    connector_ref: str,
    payload: AppConnectorUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Update one app connector link by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _update_app_connector_link(app.id, connector_ref, payload, db)


@router.delete(
    "/by-client-id/{client_id}/connectors/{connector_ref}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_app_connector_by_client_id(
    client_id: str,
    connector_ref: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete one app connector link by client ID."""

    app = _require_app_by_client_id(client_id, db)
    _delete_app_connector_link(app.id, connector_ref, db)


@router.get(
    "/by-client-id/{client_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
)
def list_app_policy_assignments_by_client_id(
    client_id: str,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return all policy assignments belonging to one app by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _list_policy_assignments_for_app(app.id, db)


@router.post(
    "/by-client-id/{client_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
    status_code=status.HTTP_201_CREATED,
)
def create_app_policy_assignment_by_client_id(
    client_id: str,
    payload: PolicyAssignmentCreate,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Assign one or more reusable policies to one app by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _assign_policies_to_app(app.id, payload, db)


@router.put(
    "/by-client-id/{client_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
)
def bulk_update_app_policy_assignments_by_client_id(
    client_id: str,
    payload: PolicyAssignmentBulkUpdate,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Enable or disable multiple app-specific assignments by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _bulk_update_app_policy_assignments(app.id, payload, db)


@router.delete(
    "/by-client-id/{client_id}/policy-assignments",
    response_model=PolicyAssignmentBulkDeleteResponse,
)
def bulk_delete_app_policy_assignments_by_client_id(
    client_id: str,
    payload: PolicyAssignmentBulkDelete,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Delete multiple app-specific assignments by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _bulk_delete_app_policy_assignments(app.id, payload, db)


@router.put(
    "/by-client-id/{client_id}/policy-assignments/{assignment_id}",
    response_model=AppPolicyAssignmentRead,
)
def update_app_policy_assignment_by_client_id(
    client_id: str,
    assignment_id: int,
    payload: PolicyAssignmentUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Enable or disable one app-specific policy assignment by client ID."""

    app = _require_app_by_client_id(client_id, db)
    return _update_app_policy_assignment(app.id, assignment_id, payload, db)


@router.delete(
    "/by-client-id/{client_id}/policy-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_app_policy_assignment_by_client_id(
    client_id: str,
    assignment_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete one app-specific policy assignment by client ID."""

    app = _require_app_by_client_id(client_id, db)
    _delete_app_policy_assignment(app.id, assignment_id, db)


@router.get("/{app_id}", response_model=AppRead)
def get_app(app_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """Return one client app by ID."""

    return serialize_app(_require_app(app_id, db))


@router.get(
    "/{app_id}/effective-policy-assignments",
    response_model=EffectivePolicyAssignmentsRead,
)
def get_effective_policy_assignments(
    app_id: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Return global and app-specific policy assignments for one app."""

    app = _require_app(app_id, db)
    return _effective_policy_assignments_for_app(app, db)


@router.get(
    "/{app_id}/connectors",
    response_model=list[AppConnectorRead],
)
def list_app_connectors(
    app_id: int,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return connector links belonging to one app."""

    _require_app(app_id, db)
    return _list_app_connectors(app_id, db)


@router.post(
    "/{app_id}/connectors",
    response_model=AppConnectorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_app_connector(
    app_id: int,
    payload: AppConnectorCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Create or update one app connector link."""

    _require_app(app_id, db)
    return _link_connector_to_app(app_id, payload, db)


@router.put(
    "/{app_id}/connectors/{connector_ref}",
    response_model=AppConnectorRead,
)
def update_app_connector(
    app_id: int,
    connector_ref: str,
    payload: AppConnectorUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Update one app connector link."""

    _require_app(app_id, db)
    return _update_app_connector_link(app_id, connector_ref, payload, db)


@router.delete(
    "/{app_id}/connectors/{connector_ref}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_app_connector(
    app_id: int,
    connector_ref: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete one app connector link."""

    _require_app(app_id, db)
    _delete_app_connector_link(app_id, connector_ref, db)


@router.put("/{app_id}", response_model=AppRead)
def update_app(
    app_id: int,
    payload: AppUpdate,
    user: UserRecord = Depends(require_app_route_access),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Update one client app."""

    app = _require_app(app_id, db)
    values = payload.model_dump(exclude_unset=True, exclude={"api_key"})
    if user.system_role != "admin" and "guardrail_llm_config_id" in values:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can select the guardrail LLM",
        )
    _validate_llm_config_ids(values, db)

    for field, value in values.items():
        setattr(app, field, value)

    if payload.api_key is not None:
        app.api_key_hash = hash_api_key(payload.api_key)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An app with this client_id already exists",
        ) from error

    db.refresh(app)
    return serialize_app(app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app(app_id: int, db: Session = Depends(get_db)) -> None:
    """Delete one client app and its dependent assignments."""

    app = _require_app(app_id, db)
    db.delete(app)
    db.commit()


@router.get(
    "/{app_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
)
def list_app_policy_assignments(
    app_id: int,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return all policy assignments belonging to one app."""

    _require_app(app_id, db)
    return _list_policy_assignments_for_app(app_id, db)


@router.post(
    "/{app_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
    status_code=status.HTTP_201_CREATED,
)
def create_app_policy_assignment(
    app_id: int,
    payload: PolicyAssignmentCreate,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Assign one or more reusable policies to one client app."""

    _require_app(app_id, db)
    return _assign_policies_to_app(app_id, payload, db)


@router.put(
    "/{app_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
)
def bulk_update_app_policy_assignments(
    app_id: int,
    payload: PolicyAssignmentBulkUpdate,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Enable or disable multiple app-specific policy assignments."""

    _require_app(app_id, db)
    return _bulk_update_app_policy_assignments(app_id, payload, db)


@router.delete(
    "/{app_id}/policy-assignments",
    response_model=PolicyAssignmentBulkDeleteResponse,
)
def bulk_delete_app_policy_assignments(
    app_id: int,
    payload: PolicyAssignmentBulkDelete,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Delete multiple app-specific policy assignments."""

    _require_app(app_id, db)
    return _bulk_delete_app_policy_assignments(app_id, payload, db)


@router.put(
    "/{app_id}/policy-assignments/{assignment_id}",
    response_model=AppPolicyAssignmentRead,
)
def update_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    payload: PolicyAssignmentUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Enable or disable one app-specific policy assignment."""

    _require_app(app_id, db)
    return _update_app_policy_assignment(app_id, assignment_id, payload, db)


@router.delete(
    "/{app_id}/policy-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete one app-specific policy assignment."""

    _require_app(app_id, db)
    _delete_app_policy_assignment(app_id, assignment_id, db)
