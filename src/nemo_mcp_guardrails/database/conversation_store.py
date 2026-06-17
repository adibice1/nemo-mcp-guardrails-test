from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.models import ConversationMessageRecord


@dataclass(frozen=True)
class ConversationTurn:
    """Represent one conversation turn passed to the runtime."""

    role: str
    content: str

    def as_message(self) -> dict[str, str]:
        """Return the turn in LangChain chat-message shape."""

        return {"role": self.role, "content": self.content}


def load_conversation_turns(
    db: Session,
    app_id: int,
    conversation_id: str,
) -> list[ConversationTurn]:
    """Load stored conversation turns for one app conversation."""

    records = db.scalars(
        select(ConversationMessageRecord)
        .where(
            ConversationMessageRecord.app_id == app_id,
            ConversationMessageRecord.conversation_id == conversation_id,
        )
        .order_by(ConversationMessageRecord.id)
    )

    return [
        ConversationTurn(role=record.role, content=record.content)
        for record in records
    ]


def append_conversation_turns(
    db: Session,
    app_id: int,
    conversation_id: str,
    turns: Sequence[ConversationTurn],
) -> None:
    """Append conversation turns to one app conversation."""

    if not turns:
        return

    db.add_all(
        ConversationMessageRecord(
            app_id=app_id,
            conversation_id=conversation_id,
            role=turn.role,
            content=turn.content,
        )
        for turn in turns
    )
