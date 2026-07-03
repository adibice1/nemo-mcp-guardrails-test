import os

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.runtime_factory import (
    RuntimeEnvironment,
    RuntimeLlmConfig,
    build_chat_model,
)


def _environment() -> RuntimeEnvironment:
    """Return fake settings that let model construction run without network calls."""

    return RuntimeEnvironment(
        azure_api_key="fake-key",
        azure_endpoint="https://example.openai.azure.com",
        azure_api_version="2024-02-15-preview",
        azure_deployment="default-deployment",
        github_pat="fake-pat",
        github_mcp_read_only="1",
    )


def main() -> None:
    default_model = build_chat_model(_environment(), None, "guardrail")
    assert default_model.deployment_name == "default-deployment"

    configured_model = build_chat_model(
        _environment(),
        RuntimeLlmConfig(
            name="custom azure",
            provider="azure_openai",
            model_name="custom-deployment",
            endpoint=None,
            credential_reference=None,
            enabled=True,
        ),
        "main agent",
    )
    assert configured_model.deployment_name == "custom-deployment"

    os.environ["APP_SPECIFIC_AZURE_KEY"] = "app-specific-key"
    referenced_model = build_chat_model(
        _environment(),
        RuntimeLlmConfig(
            name="referenced azure",
            provider="azure_openai",
            model_name="referenced-deployment",
            endpoint="https://referenced.openai.azure.com",
            credential_reference="env:APP_SPECIFIC_AZURE_KEY",
            enabled=True,
        ),
        "main agent",
    )
    assert referenced_model.openai_api_key.get_secret_value() == "app-specific-key"

    try:
        build_chat_model(
            _environment(),
            RuntimeLlmConfig(
                name="future gemini",
                provider="gemini",
                model_name="gemini-1.5-pro",
                endpoint=None,
                credential_reference=None,
                enabled=True,
            ),
            "main agent",
        )
    except RuntimeError as exc:
        assert "Unsupported main agent LLM provider" in str(exc)
    else:
        raise AssertionError("Unsupported provider should fail clearly")

    try:
        build_chat_model(
            _environment(),
            RuntimeLlmConfig(
                name="disabled azure",
                provider="azure_openai",
                model_name="disabled-deployment",
                endpoint=None,
                credential_reference=None,
                enabled=False,
            ),
            "guardrail",
        )
    except RuntimeError as exc:
        assert "guardrail LLM config is disabled" in str(exc)
    else:
        raise AssertionError("Disabled config should fail clearly")

    print("Runtime LLM selection checks passed.")


if __name__ == "__main__":
    main()
