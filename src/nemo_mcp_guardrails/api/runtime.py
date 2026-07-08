import os
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.auth import require_authenticated_app
from nemo_mcp_guardrails.api.runtime_schemas import (
    GuardrailsRunRequest,
    GuardrailsRunResponse,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import AppRecord
from nemo_mcp_guardrails.database.conversation_store import (
    ConversationTurn,
    append_conversation_turns,
    load_conversation_turns,
)
from nemo_mcp_guardrails.guarded_execution import execute_guarded_message
from nemo_mcp_guardrails.policy_compiler import (
    GITHUB_ACTION_SYNONYMS,
    GITHUB_RESOURCE_SYNONYMS,
    GITHUB_WRITE_TOOL_MAPPINGS,
)
from nemo_mcp_guardrails.runtime_factory import (
    ConnectorAccessError,
    GuardrailsRuntimeParts,
    build_guardrails_runtime_parts,
)


DEFAULT_MAX_RUNTIME_CONTEXT_CHARS = 24000
RUNTIME_DEBUG_ENV = "NEMO_RUNTIME_DEBUG"

router = APIRouter(prefix="/v1/guardrails", tags=["guardrails-runtime"])


@dataclass(frozen=True)
class RuntimeHistoryContext:
    """Store selected conversation history and metadata for one request."""

    source_turns: tuple[ConversationTurn, ...]
    selected_turns: tuple[ConversationTurn, ...]
    received_count: int
    loaded_count: int
    truncated: bool


@dataclass(frozen=True)
class RuntimeBlockExplanation:
    """Human-readable explanation for one blocked runtime response."""

    stage: str
    reason: str
    policy_id: int | None = None
    policy_name: str | None = None


@router.get("/auth-check")
def authentication_check(
    app: AppRecord = Depends(require_authenticated_app),
) -> dict[str, str | int]:
    """Confirm runtime credentials without loading guardrails or tools."""

    return {
        "status": "authenticated",
        "app_id": app.id,
        "client_id": app.client_id,
    }


def _rail_status_text(status: object | None) -> str | None:
    """Return a stable string for a NeMo rail status."""

    if status is None:
        return None

    return str(getattr(status, "value", status))


def _display_token(value: str | None) -> str:
    """Return one policy token formatted for human-facing text."""

    return (value or "").replace("_", " ").strip()


def _policy_display_name(
    *,
    connector: str,
    action: str,
    resource: str,
    custom_resource: str | None = None,
) -> str:
    """Return a compact readable policy label."""

    label = (
        f"{_display_token(connector).title()} "
        f"{_display_token(action)} {_display_token(resource)}"
    )
    if custom_resource:
        label = f"{label} matching {custom_resource}"
    return label


def _policy_reason(
    *,
    action: str,
    resource: str,
    custom_resource: str | None = None,
) -> str:
    """Return the user-facing reason for one input policy."""

    reason = f"Blocked due to request to {_display_token(action)} a GitHub {_display_token(resource)}."
    if custom_resource:
        reason = (
            f"Blocked due to request to {_display_token(action)} a GitHub "
            f"{_display_token(resource)} matching {custom_resource}."
        )
    return reason


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    """Return whether normalized text contains any phrase."""

    return any(phrase.casefold() in text for phrase in phrases)


def _matching_input_policy_explanation(
    message: str,
    runtime_parts: GuardrailsRuntimeParts,
) -> RuntimeBlockExplanation | None:
    """Best-effort match between a blocked prompt and an app input policy."""

    normalized_message = message.casefold()

    for entry in runtime_parts.input_policy_entries:
        policy = entry.policy
        action_synonyms = GITHUB_ACTION_SYNONYMS.get(
            policy.action,
            (policy.action,),
        )
        resource_synonyms = GITHUB_RESOURCE_SYNONYMS.get(
            policy.resource,
            (policy.resource,),
        )
        if not _contains_any(normalized_message, tuple(action_synonyms)):
            continue
        if not _contains_any(normalized_message, tuple(resource_synonyms)):
            continue

        custom_resource = policy.custom_resource
        if custom_resource and custom_resource.casefold() not in normalized_message:
            continue

        return RuntimeBlockExplanation(
            stage="input",
            reason=_policy_reason(
                action=policy.action,
                resource=policy.resource,
                custom_resource=custom_resource,
            ),
            policy_id=entry.source_id,
            policy_name=_policy_display_name(
                connector=policy.connector,
                action=policy.action,
                resource=policy.resource,
                custom_resource=custom_resource,
            ),
        )

    return None


def _tool_policy_explanation(tool_name: str | None) -> RuntimeBlockExplanation:
    """Return a readable reason for a tool-guard block."""

    for (action, resource), tool_names in GITHUB_WRITE_TOOL_MAPPINGS.items():
        if tool_name in tool_names:
            return RuntimeBlockExplanation(
                stage="tool",
                reason=_policy_reason(action=action, resource=resource),
                policy_name=_policy_display_name(
                    connector="github",
                    action=action,
                    resource=resource,
                ),
            )

    tool_label = tool_name or "requested MCP tool"
    return RuntimeBlockExplanation(
        stage="tool",
        reason=f"Blocked because {tool_label} is restricted by policy.",
    )


def _output_policy_explanation(
    *,
    source: str | None,
    categories: tuple[str, ...],
    blocked_phrase: str | None,
) -> RuntimeBlockExplanation:
    """Return a readable reason for an output block."""

    if blocked_phrase:
        return RuntimeBlockExplanation(
            stage="output",
            reason=(
                "Blocked because the assistant response contained the "
                f"restricted phrase \"{blocked_phrase}\"."
            ),
        )

    if source and source.startswith("azure"):
        category_label = ", ".join(categories)
        reason = "Blocked by Azure content filter."
        if category_label:
            reason = f"Blocked by Azure content filter: {category_label}."
        return RuntimeBlockExplanation(stage="output", reason=reason)

    return RuntimeBlockExplanation(
        stage="output",
        reason="Blocked because the assistant response violated an output safety policy.",
    )


def _block_explanation(
    *,
    message: str,
    runtime_parts: GuardrailsRuntimeParts,
    execution_result: object,
) -> RuntimeBlockExplanation | None:
    """Return a human-readable block explanation for a runtime result."""

    if getattr(execution_result, "status", None) != "blocked":
        return None

    if _rail_status_text(getattr(execution_result, "input_rail_status", None)) == "blocked":
        return _matching_input_policy_explanation(message, runtime_parts) or RuntimeBlockExplanation(
            stage="input",
            reason="Blocked because the request violated an input policy.",
        )

    if getattr(execution_result, "tool_guard_status", None) == "blocked":
        tool_names = tuple(getattr(execution_result, "tool_names", ()))
        return _tool_policy_explanation(tool_names[0] if tool_names else None)

    if _rail_status_text(getattr(execution_result, "output_rail_status", None)) == "blocked":
        return _output_policy_explanation(
            source=getattr(execution_result, "output_rail_source", None),
            categories=tuple(getattr(execution_result, "output_rail_categories", ())),
            blocked_phrase=getattr(execution_result, "blocked_output_phrase", None),
        )

    return RuntimeBlockExplanation(
        stage="runtime",
        reason="Blocked by the guardrails runtime.",
    )


def _runtime_debug_enabled() -> bool:
    """Return whether local runtime debug fields should be exposed."""

    return os.getenv(RUNTIME_DEBUG_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _max_runtime_context_chars() -> int:
    """Return the configured maximum runtime context size."""

    raw_value = os.getenv(
        "NEMO_MAX_RUNTIME_CONTEXT_CHARS",
        str(DEFAULT_MAX_RUNTIME_CONTEXT_CHARS),
    )

    try:
        value = int(raw_value)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="NEMO_MAX_RUNTIME_CONTEXT_CHARS must be an integer",
        ) from error

    if value < 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="NEMO_MAX_RUNTIME_CONTEXT_CHARS must be greater than zero",
        )

    return value


def _turn_size(turn: ConversationTurn) -> int:
    """Return the approximate size of one conversation turn."""

    return len(turn.role) + len(turn.content)


def _trim_history_to_context_limit(
    turns: tuple[ConversationTurn, ...],
    latest_message: str,
) -> tuple[tuple[ConversationTurn, ...], bool]:
    """Keep the newest prior turns that fit beside the latest message."""

    max_chars = _max_runtime_context_chars()
    latest_message_size = len(latest_message)

    if latest_message_size > max_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "Guardrails request is too large. "
                f"The latest message has {latest_message_size} characters; "
                f"maximum runtime context is {max_chars}. "
                "Shorten the message and retry."
            ),
        )

    remaining_chars = max_chars - latest_message_size
    selected: list[ConversationTurn] = []

    for turn in reversed(turns):
        turn_size = _turn_size(turn)
        if turn_size > remaining_chars:
            break

        selected.append(turn)
        remaining_chars -= turn_size

    selected.reverse()
    selected_turns = tuple(selected)
    return selected_turns, len(selected_turns) < len(turns)


def _payload_history_turns(payload: GuardrailsRunRequest) -> tuple[ConversationTurn, ...]:
    """Convert client-supplied history into persistence/runtime turns."""

    return tuple(
        ConversationTurn(role=message.role, content=message.content)
        for message in payload.conversation_history
    )


def _build_runtime_history_context(
    payload: GuardrailsRunRequest,
    app_id: int,
    db: Session,
) -> RuntimeHistoryContext:
    """Load, bootstrap, and trim runtime conversation history."""

    received_turns = _payload_history_turns(payload)
    stored_turns: tuple[ConversationTurn, ...] = ()

    if payload.conversation_id:
        stored_turns = tuple(
            load_conversation_turns(
                db,
                app_id=app_id,
                conversation_id=payload.conversation_id,
            )
        )

    source_turns = stored_turns or received_turns
    selected_turns, truncated = _trim_history_to_context_limit(
        source_turns,
        payload.message,
    )

    return RuntimeHistoryContext(
        source_turns=source_turns,
        selected_turns=selected_turns,
        received_count=len(received_turns),
        loaded_count=len(stored_turns),
        truncated=truncated,
    )


def _store_conversation_turns(
    payload: GuardrailsRunRequest,
    app_id: int,
    response: str,
    history_context: RuntimeHistoryContext,
    db: Session,
) -> None:
    """Persist bootstrap history and the latest user/assistant turn."""

    if not payload.conversation_id:
        return

    turns_to_store: list[ConversationTurn] = []

    if history_context.loaded_count == 0:
        turns_to_store.extend(history_context.source_turns)

    turns_to_store.extend(
        [
            ConversationTurn(role="user", content=payload.message),
            ConversationTurn(role="assistant", content=response),
        ]
    )

    append_conversation_turns(
        db,
        app_id=app_id,
        conversation_id=payload.conversation_id,
        turns=turns_to_store,
    )
    db.commit()


@router.post("/run", response_model=GuardrailsRunResponse)
async def run_guardrails(
    payload: GuardrailsRunRequest,
    app: AppRecord = Depends(require_authenticated_app),
    db: Session = Depends(get_db),
) -> GuardrailsRunResponse:
    """Execute one authenticated request through the guarded runtime."""

    history_context = _build_runtime_history_context(payload, app.id, db)
    try:
        runtime_parts = await build_guardrails_runtime_parts(app.id)
    except ConnectorAccessError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    execution_result = await execute_guarded_message(
        rails=runtime_parts.rails,
        agent=runtime_parts.agent,
        message=payload.message,
        output_rail_enabled=runtime_parts.output_rail_enabled,
        conversation_history=[
            turn.as_message() for turn in history_context.selected_turns
        ],
        blocked_output_phrases=runtime_parts.blocked_output_phrases,
    )
    block_explanation = _block_explanation(
        message=payload.message,
        runtime_parts=runtime_parts,
        execution_result=execution_result,
    )
    runtime_response = (
        block_explanation.reason
        if block_explanation is not None
        else execution_result.response
    )
    _store_conversation_turns(
        payload,
        app_id=app.id,
        response=runtime_response,
        history_context=history_context,
        db=db,
    )

    debug_enabled = _runtime_debug_enabled()

    return GuardrailsRunResponse(
        status=execution_result.status,
        app_id=app.id,
        client_id=app.client_id,
        conversation_id=payload.conversation_id,
        response=runtime_response,
        input_rail_status=_rail_status_text(execution_result.input_rail_status) or "",
        input_rail_source=execution_result.input_rail_source,
        input_rail_categories=list(execution_result.input_rail_categories),
        output_rail_status=_rail_status_text(execution_result.output_rail_status),
        output_rail_source=execution_result.output_rail_source,
        output_rail_categories=list(execution_result.output_rail_categories),
        tool_guard_status=execution_result.tool_guard_status,
        tool_guard_source=execution_result.tool_guard_source,
        block_stage=block_explanation.stage if block_explanation else None,
        block_reason=block_explanation.reason if block_explanation else None,
        blocked_policy_id=block_explanation.policy_id if block_explanation else None,
        blocked_policy_name=(
            block_explanation.policy_name if block_explanation else None
        ),
        tool_names=list(execution_result.tool_names),
        input_policy_count=runtime_parts.input_policy_count,
        input_rule_count=runtime_parts.prompt_rule_config.input_rule_count,
        output_rule_count=runtime_parts.prompt_rule_config.output_rule_count,
        blocked_tools=sorted(runtime_parts.blocked_tools),
        history_truncated=history_context.truncated,
        history_messages_received=history_context.received_count,
        history_messages_loaded=history_context.loaded_count,
        history_messages_used=len(history_context.selected_turns),
        debug_agent_response=(
            execution_result.raw_agent_response if debug_enabled else None
        ),
        debug_output_rail_source=(
            execution_result.output_rail_source if debug_enabled else None
        ),
        debug_output_rule_texts=(
            [
                rule.rule_text
                for rule in runtime_parts.prompt_rule_config.prompt_rules
                if rule.rail_type == "output"
            ]
            if debug_enabled
            else None
        ),
        debug_tool_trace=(
            [dict(entry) for entry in execution_result.tool_trace]
            if debug_enabled
            else None
        ),
    )
