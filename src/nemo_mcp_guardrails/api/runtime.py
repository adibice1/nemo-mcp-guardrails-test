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
from nemo_mcp_guardrails.runtime_factory import build_guardrails_runtime_parts


DEFAULT_MAX_RUNTIME_CONTEXT_CHARS = 24000

router = APIRouter(prefix="/v1/guardrails", tags=["guardrails-runtime"])


@dataclass(frozen=True)
class RuntimeHistoryContext:
    """Store selected conversation history and metadata for one request."""

    source_turns: tuple[ConversationTurn, ...]
    selected_turns: tuple[ConversationTurn, ...]
    received_count: int
    loaded_count: int
    truncated: bool


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
    runtime_parts = await build_guardrails_runtime_parts(app.id)
    execution_result = await execute_guarded_message(
        rails=runtime_parts.rails,
        agent=runtime_parts.agent,
        message=payload.message,
        output_rail_enabled=runtime_parts.output_rail_enabled,
        conversation_history=[
            turn.as_message() for turn in history_context.selected_turns
        ],
    )
    _store_conversation_turns(
        payload,
        app_id=app.id,
        response=execution_result.response,
        history_context=history_context,
        db=db,
    )

    return GuardrailsRunResponse(
        status=execution_result.status,
        app_id=app.id,
        client_id=app.client_id,
        conversation_id=payload.conversation_id,
        response=execution_result.response,
        input_rail_status=_rail_status_text(execution_result.input_rail_status) or "",
        output_rail_status=_rail_status_text(execution_result.output_rail_status),
        tool_names=list(execution_result.tool_names),
        input_policy_count=runtime_parts.input_policy_count,
        input_rule_count=runtime_parts.prompt_rule_config.input_rule_count,
        output_rule_count=runtime_parts.prompt_rule_config.output_rule_count,
        blocked_tools=sorted(runtime_parts.blocked_tools),
        history_truncated=history_context.truncated,
        history_messages_received=history_context.received_count,
        history_messages_loaded=history_context.loaded_count,
        history_messages_used=len(history_context.selected_turns),
    )
