from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.policy_schemas import (
    CompileAndStoreRulesResponse,
    CompilePreviewResponse,
    CompiledPolicyRuleRead,
    CompiledTestPrompt,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    CompiledPolicyRuleRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.policy_compiler import (
    InputPolicyObject,
    OutputPolicyObject,
    compile_output_rail_rules,
    compile_policy,
)


router = APIRouter(prefix="/policies", tags=["policies"])


def _require_policy_fields(policy: PolicyRecord, fields: tuple[str, ...]) -> None:
    """Raise a validation error when a stored policy is missing compiler fields."""

    missing_fields = [field for field in fields if not getattr(policy, field)]
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Policy {policy.id} is missing required fields: "
                + ", ".join(missing_fields)
            ),
        )


def _to_input_policy_object(policy: PolicyRecord) -> InputPolicyObject:
    """Convert a stored input policy row into the compiler dataclass."""

    app = policy.normalized_app.name if policy.normalized_app else policy.app
    action = policy.normalized_action.name if policy.normalized_action else policy.action
    resource = (
        policy.normalized_resource.name
        if policy.normalized_resource
        else policy.resource
    )

    if not (app and action and resource and policy.effect):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy {policy.id} is missing required input policy fields",
        )

    return InputPolicyObject(
        app=app,
        action=action,
        resource=resource,
        effect=policy.effect,
    )


def _to_output_policy_object(policy: PolicyRecord) -> OutputPolicyObject:
    """Convert a stored output policy row into the compiler dataclass."""

    _require_policy_fields(policy, ("category", "description", "effect"))
    return OutputPolicyObject(
        category=policy.category or "",
        description=policy.description or "",
        effect=policy.effect,
    )


def _compile_policy_rule_record(policy: PolicyRecord) -> CompiledPolicyRuleRecord:
    """Compile one stored policy row into a persisted rail rule record."""

    if policy.policy_type == "input":
        compiled_policy = compile_policy(_to_input_policy_object(policy))
        return CompiledPolicyRuleRecord(
            policy_id=policy.id,
            rail_type="input",
            rule_text=compiled_policy.input_rail_rule,
            policy_version=policy.policy_version,
            stale=False,
            enabled=True,
        )

    if policy.policy_type == "output":
        output_rules = compile_output_rail_rules((_to_output_policy_object(policy),))
        return CompiledPolicyRuleRecord(
            policy_id=policy.id,
            rail_type="output",
            rule_text=output_rules[0],
            policy_version=policy.policy_version,
            stale=False,
            enabled=True,
        )

    raise ValueError(f"Unsupported policy type: {policy.policy_type}")


@router.get("", response_model=list[PolicyRead])
def list_policies(db: Session = Depends(get_db)) -> list[PolicyRecord]:
    """Return all stored policies."""

    return list(db.scalars(select(PolicyRecord).order_by(PolicyRecord.id)))


@router.post("/compile-preview", response_model=CompilePreviewResponse)
def compile_policy_preview(db: Session = Depends(get_db)) -> CompilePreviewResponse:
    """Preview compiler artifacts generated from enabled policy rows."""

    policies = list(
        db.scalars(
            select(PolicyRecord)
            .where(PolicyRecord.enabled.is_(True))
            .order_by(PolicyRecord.id)
        )
    )

    input_rules: list[str] = []
    blocked_tools: set[str] = set()
    test_prompts: list[CompiledTestPrompt] = []
    output_policies: list[OutputPolicyObject] = []

    try:
        for policy in policies:
            if policy.policy_type == "input":
                compiled_policy = compile_policy(_to_input_policy_object(policy))
                input_rules.append(compiled_policy.input_rail_rule)
                blocked_tools.update(compiled_policy.blocked_tools)
                test_prompts.extend(
                    CompiledTestPrompt(name=test_case.name, prompt=test_case.prompt)
                    for test_case in compiled_policy.test_cases
                )
            elif policy.policy_type == "output":
                output_policies.append(_to_output_policy_object(policy))
            else:
                raise ValueError(f"Unsupported policy type: {policy.policy_type}")

        output_rules = list(compile_output_rail_rules(tuple(output_policies)))
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return CompilePreviewResponse(
        input_rules=input_rules,
        blocked_tools=sorted(blocked_tools),
        test_prompts=test_prompts,
        output_rules=output_rules,
    )


@router.get("/compiled-rules", response_model=list[CompiledPolicyRuleRead])
def list_compiled_policy_rules(
    db: Session = Depends(get_db),
) -> list[CompiledPolicyRuleRecord]:
    """Return stored compiled policy rail rules."""

    return list(
        db.scalars(
            select(CompiledPolicyRuleRecord).order_by(CompiledPolicyRuleRecord.id)
        )
    )


@router.post("/compile-rules", response_model=CompileAndStoreRulesResponse)
def compile_and_store_policy_rules(
    db: Session = Depends(get_db),
) -> CompileAndStoreRulesResponse:
    """Compile enabled policies into stored NeMo rail rule text."""

    policies = list(
        db.scalars(
            select(PolicyRecord)
            .where(PolicyRecord.enabled.is_(True))
            .order_by(PolicyRecord.id)
        )
    )

    try:
        compiled_rules = [_compile_policy_rule_record(policy) for policy in policies]
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    db.execute(delete(CompiledPolicyRuleRecord))
    db.add_all(compiled_rules)
    db.commit()

    for compiled_rule in compiled_rules:
        db.refresh(compiled_rule)

    return CompileAndStoreRulesResponse(rules=compiled_rules)


@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(policy_id: int, db: Session = Depends(get_db)) -> PolicyRecord:
    """Return one stored policy by ID."""

    policy = db.get(PolicyRecord, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    return policy


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_db),
) -> PolicyRecord:
    """Create one policy record."""

    policy = PolicyRecord(**payload.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.put("/{policy_id}", response_model=PolicyRead)
def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
) -> PolicyRecord:
    """Update one policy record."""

    policy = db.get(PolicyRecord, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    updates = payload.model_dump(exclude_unset=True)

    if "app" in updates:
        policy.app_id = None
        policy.action_id = None
        policy.resource_id = None
    if "action" in updates:
        policy.action_id = None
    if "resource" in updates:
        policy.resource_id = None

    for field, value in updates.items():
        setattr(policy, field, value)

    policy.policy_version += 1
    db.execute(
        update(CompiledPolicyRuleRecord)
        .where(CompiledPolicyRuleRecord.policy_id == policy.id)
        .values(stale=True)
    )
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policy_id: int, db: Session = Depends(get_db)) -> None:
    """Delete one policy record."""

    policy = db.get(PolicyRecord, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    db.delete(policy)
    db.commit()
