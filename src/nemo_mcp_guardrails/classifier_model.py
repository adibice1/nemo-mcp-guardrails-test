"""Require a complete, unambiguous classifier decision from compatible models."""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ClassifierResponseError(ValueError):
    """Reject an unusable classification without including provider text."""


class StrictClassifierModel(BaseChatModel):
    """Validate compatible model responses before NeMo parses or logs a decision."""

    wrapped: BaseChatModel

    @property
    def _llm_type(self) -> str:
        """Identify the classifier adapter to LangChain."""
        return "gms_strict_classifier"

    @property
    def model_name(self) -> str:
        """Expose the underlying model name for provider parameter handling."""
        return getattr(self.wrapped, "model_name", "")

    def _decision(self, message: BaseMessage) -> ChatResult:
        """Accept exactly yes/no from a completed, non-tool, non-refused response."""
        if (not isinstance(message, AIMessage) or not isinstance(message.content, str)
                or message.content.strip().lower() not in {"yes", "no"}
                or message.response_metadata.get("finish_reason") != "stop"
                or message.tool_calls or message.invalid_tool_calls
                or message.additional_kwargs.get("refusal")):
            raise ClassifierResponseError("The guardrail model returned an invalid classification.")
        clean = AIMessage(content=message.content.strip().lower(), response_metadata={"finish_reason": "stop"})
        return ChatResult(generations=[ChatGeneration(message=clean)])

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None,
                  run_manager: Any = None, **kwargs: Any) -> ChatResult:
        """Validate a synchronous classification before returning its text."""
        return self._decision(self.wrapped.invoke(messages, stop=stop, **kwargs))

    async def _agenerate(self, messages: list[BaseMessage], stop: list[str] | None = None,
                         run_manager: Any = None, **kwargs: Any) -> ChatResult:
        """Validate an asynchronous classification before returning its text."""
        return self._decision(await self.wrapped.ainvoke(messages, stop=stop, **kwargs))
