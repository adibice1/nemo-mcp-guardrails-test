from fastapi import APIRouter, Depends

from nemo_mcp_guardrails.api.auth import require_authenticated_app
from nemo_mcp_guardrails.api.runtime_schemas import (
    GuardrailsRunRequest,
    GuardrailsRuntimeContextResponse,
)
from nemo_mcp_guardrails.database.models import AppRecord
from nemo_mcp_guardrails.database.policy_loader import load_input_policy_entries
from nemo_mcp_guardrails.prompt_rule_compiler import (
    build_rails_config_with_prompt_rules,
)
from nemo_mcp_guardrails.tool_guard import blocked_tool_names_for_app


router = APIRouter(prefix="/v1/guardrails", tags=["guardrails-runtime"])


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


@router.post("/run", response_model=GuardrailsRuntimeContextResponse)
def prepare_guardrails_runtime(
    payload: GuardrailsRunRequest,
    app: AppRecord = Depends(require_authenticated_app),
) -> GuardrailsRuntimeContextResponse:
    """Prepare and describe the authenticated app's guardrail context."""

    prompt_rule_config = build_rails_config_with_prompt_rules(
        "config",
        app_id=app.id,
    )
    input_policies = load_input_policy_entries(app_id=app.id)
    blocked_tools = blocked_tool_names_for_app(app_id=app.id)

    return GuardrailsRuntimeContextResponse(
        status="context_ready",
        app_id=app.id,
        client_id=app.client_id,
        input_policy_count=len(input_policies),
        input_rule_count=prompt_rule_config.input_rule_count,
        output_rule_count=prompt_rule_config.output_rule_count,
        blocked_tools=sorted(blocked_tools),
    )
