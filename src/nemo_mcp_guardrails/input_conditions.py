"""Serialize reviewed input selectors without losing their literal identity."""

from dataclasses import replace
import json

from nemo_mcp_guardrails.github_resource_bindings import compile_resource_binding
from nemo_mcp_guardrails.policy_compiler import InputPolicyObject
from nemo_mcp_guardrails.resource_conditions import (
    BranchCondition, ResourceCondition, UnsupportedResourceCondition, parse_resource_condition,
    condition_text,
)


CONDITION_VERSION_KEY = "resource_condition_version"


def _condition_mapping(conditions: object) -> dict:
    """Reject unknown fields and non-integer or unsupported format markers."""

    if conditions is None:
        return {}
    if not isinstance(conditions, dict) or set(conditions) - {"custom_resource", CONDITION_VERSION_KEY}:
        raise UnsupportedResourceCondition("Unsupported input condition fields.")
    if CONDITION_VERSION_KEY in conditions and (
        type(conditions[CONDITION_VERSION_KEY]) is not int or conditions[CONDITION_VERSION_KEY] not in {1, 2}
    ):
        raise UnsupportedResourceCondition("Unsupported input condition format.")
    return dict(conditions)


def _serialize(condition: ResourceCondition | BranchCondition) -> dict:
    """Keep path/branch case and punctuation while folding title/name case."""

    if isinstance(condition, BranchCondition):
        selector = condition_text(condition)
        if len(selector) > 1000:
            raise UnsupportedResourceCondition("The canonical branch selector is too long.")
        return {"custom_resource": selector, CONDITION_VERSION_KEY: 2}
    value = condition.value
    if condition.field in {"title", "name"}:
        value = value.casefold()
    selector = f"{condition.field} = {json.dumps(value, ensure_ascii=False)}"
    if len(selector) > 1000:
        raise UnsupportedResourceCondition("The canonical resource selector is too long.")
    return {
        "custom_resource": selector,
        CONDITION_VERSION_KEY: 1,
    }


def canonical_versioned_conditions(resource: str, conditions: object) -> dict:
    """Canonicalize an explicitly versioned selector without legacy text folding."""

    values = _condition_mapping(conditions)
    if CONDITION_VERSION_KEY not in values or not isinstance(values.get("custom_resource"), str):
        raise UnsupportedResourceCondition("A versioned resource selector is required.")
    condition = parse_resource_condition(resource, values["custom_resource"])
    if condition is None:
        raise UnsupportedResourceCondition("A format marker requires a nonempty selector.")
    return _serialize(condition)


def prepare_input_conditions(policy: InputPolicyObject, conditions: object) -> dict:
    """Validate supported write selectors before preparing their stored format."""

    values = _condition_mapping(conditions)
    custom_resource = values.get("custom_resource")
    if custom_resource is not None and not isinstance(custom_resource, str):
        raise UnsupportedResourceCondition("Input custom resources must be text.")
    binding = compile_resource_binding(replace(policy, custom_resource=custom_resource))
    if custom_resource is None or not custom_resource.strip():
        if CONDITION_VERSION_KEY in values:
            raise UnsupportedResourceCondition("A format marker requires a nonempty selector.")
        return {}
    if binding is None:
        raise UnsupportedResourceCondition("A nonempty resource selector is required.")
    prepared = _serialize(binding.condition)
    if CONDITION_VERSION_KEY in values and values[CONDITION_VERSION_KEY] != prepared[CONDITION_VERSION_KEY]:
        raise UnsupportedResourceCondition("The selector does not match its format version.")
    return prepared
