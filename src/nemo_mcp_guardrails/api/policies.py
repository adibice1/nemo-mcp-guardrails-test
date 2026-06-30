from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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
    compile_output_rail_rules,
    compile_policy,
)
from nemo_mcp_guardrails.policy_rule_service import (
    refresh_all_compiled_policy_rules,
    refresh_compiled_policy_rule,
    to_input_policy_object,
    to_output_policy_object,
)
from nemo_mcp_guardrails.policy_service import (
    find_equivalent_policy,
    resolve_policy_references,
)


router = APIRouter(prefix="/policies", tags=["policies"])


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
                compiled_policy = compile_policy(to_input_policy_object(policy))
                input_rules.append(compiled_policy.input_rail_rule)
                blocked_tools.update(compiled_policy.blocked_tools)
                test_prompts.extend(
                    CompiledTestPrompt(name=test_case.name, prompt=test_case.prompt)
                    for test_case in compiled_policy.test_cases
                )
            elif policy.policy_type == "output":
                output_policies.append(to_output_policy_object(policy))
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

    try:
        compiled_rules = refresh_all_compiled_policy_rules(db)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

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
    resolve_policy_references(policy, db)
    equivalent = find_equivalent_policy(policy, db)
    if equivalent is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "equivalent_policy_exists",
                "policy_id": equivalent.id,
            },
        )
    db.add(policy)

    try:
        db.flush()
        refresh_compiled_policy_rule(db, policy)
    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

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

    for field, value in updates.items():
        setattr(policy, field, value)

    resolve_policy_references(policy, db)
    equivalent = find_equivalent_policy(
        policy,
        db,
        exclude_policy_id=policy.id,
    )
    if equivalent is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "equivalent_policy_exists",
                "policy_id": equivalent.id,
            },
        )
    policy.policy_version += 1

    try:
        refresh_compiled_policy_rule(db, policy)
    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

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
