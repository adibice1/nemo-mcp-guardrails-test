"""Bind literal selectors to reviewed GitHub MCP write arguments."""

from dataclasses import dataclass
import re
from typing import Any

from nemo_mcp_guardrails.policy_compiler import GITHUB_WRITE_TOOL_MAPPINGS, InputPolicyObject
from nemo_mcp_guardrails.resource_conditions import (
    BranchCondition, ResourceCondition, UnsupportedResourceCondition, parse_resource_condition,
    condition_terms,
)


REVIEWED_MCP_REVISION = "c3dedbece0bf3834829f638a245fb3c51cd98d0b"
FIELD_BINDINGS = {
    ("create", "issue", "title"): "title",
    ("update", "issue", "number"): "issue_number",
    ("comment", "issue", "number"): "issue_number",
    ("create", "pull_request", "title"): "title",
    ("create", "pull_request", "source_branch"): "head",
    ("create", "pull_request", "target_branch"): "base",
    ("merge", "pull_request", "number"): "pullNumber",
    ("merge", "pull_request", "source_branch"): "head.ref",
    ("merge", "pull_request", "target_branch"): "base.ref",
    ("review", "pull_request", "number"): "pullNumber",
    ("delete", "file", "path"): "path",
    ("push", "file", "path"): "files",
    ("create", "repository", "name"): "name",
    ("fork", "repository", "name"): "repo",
}
TOOL_METHODS = {
    "issue_write": frozenset({"create", "update"}),
    "pull_request_review_write": frozenset({"create", "submit_pending", "delete_pending"}),
}


class InvalidResourceArguments(ValueError):
    """Stop execution when the guarded resource cannot be established."""


def _argument_value(field: str, value: Any, *, qualified_head: bool = False) -> str | int:
    """Validate target values without matching unrelated fields or coercing text."""

    if field == "number":
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if type(value) is not int or not 1 <= value <= 2147483647:
            raise InvalidResourceArguments("A positive resource number is required.")
        return value
    if (
        not isinstance(value, str) or not value.strip() or value != value.strip()
        or any(ord(char) < 32 or 127 <= ord(char) < 160 or 0xD800 <= ord(char) <= 0xDFFF for char in value)
    ):
        raise InvalidResourceArguments("A valid resource string is required.")
    if qualified_head and ":" in value:
        owner, separator, value = value.partition(":")
        if not owner or not separator or ":" in value:
            raise InvalidResourceArguments("A valid source branch is required.")
    if field == "name" and (
        not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", value)
        or value in {".", ".."} or value.endswith(".") or value.casefold().endswith(".git")
    ):
        raise InvalidResourceArguments("A canonical repository name is required.")
    if field in {"path", "branch", "source_branch", "target_branch"}:
        if (
            value != value.strip() or any(part in {"", ".", ".."} for part in value.split("/"))
            or any(char in value for char in "\\%?#:")
            or (field != "path" and value.startswith("refs/"))
            or (field != "path" and any(char in value for char in "~^*[]"))
        ):
            raise InvalidResourceArguments("A canonical resource path or branch is required.")
        if field != "path" and (
            value == "@" or ".." in value or "@{" in value
            or any(char.isspace() for char in value)
            or any(part.startswith(".") or part.endswith((".", ".lock")) for part in value.split("/"))
        ):
            raise InvalidResourceArguments("A canonical Git branch name is required.")
    return value.casefold() if field in {"title", "name"} else value


@dataclass(frozen=True)
class GithubResourceBinding:
    """Describe one observable literal restriction; runtime integration is separate."""

    tool_name: str
    argument: str
    condition: ResourceCondition
    method: str | None = None

    def matches(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        """Match only authoritative targets; invalid arguments raise before execution."""

        if tool_name != self.tool_name:
            return False
        if not isinstance(arguments, dict):
            raise InvalidResourceArguments("Tool arguments must be an object.")
        if tool_name in TOOL_METHODS:
            method = arguments.get("method")
            if not isinstance(method, str) or method not in TOOL_METHODS[tool_name]:
                raise InvalidResourceArguments("The tool method has no reviewed resource binding.")
            if self.method is not None and method != self.method:
                return False
        if self.argument == "files":
            files = arguments.get("files")
            if not isinstance(files, list) or not files or any(not isinstance(item, dict) for item in files):
                raise InvalidResourceArguments("A nonempty file list is required.")
            values = [item.get("path") for item in files]
        else:
            values = [arguments.get(self.argument)]
        normalized = [
            _argument_value(self.condition.field, value, qualified_head=self.argument == "head")
            for value in values
        ]
        expected = _argument_value(self.condition.field, self.condition.value)
        return expected in normalized


@dataclass(frozen=True)
class GithubBranchBinding:
    """Match one branch route using tool arguments or trusted PR metadata."""

    tool_name: str
    condition: ResourceCondition | BranchCondition

    def matches(self, tool_name: str, arguments: dict[str, Any], *, branch_state: dict | None = None) -> bool:
        """Validate every field before evaluating the complete conjunction."""
        if tool_name != self.tool_name:
            return False
        values = arguments if tool_name == "create_pull_request" else branch_state
        if not isinstance(values, dict):
            raise InvalidResourceArguments("Trusted PR branches are unavailable.")
        decisions = []
        for term in condition_terms(self.condition):
            argument = "head" if term.field == "source_branch" else "base"
            value = _argument_value(term.field, values.get(argument), qualified_head=tool_name == "create_pull_request" and argument == "head")
            expected = _argument_value(term.field, term.value)
            decisions.append(value != expected if term.operator == "neq" else value == expected)
        return all(decisions)


def compile_resource_binding(policy: InputPolicyObject) -> GithubResourceBinding | GithubBranchBinding | None:
    """Reject restrictions whose target or action cannot be observed in tool input."""

    key = (policy.action, policy.resource)
    if policy.connector != "github" or policy.effect != "block" or key not in GITHUB_WRITE_TOOL_MAPPINGS:
        raise UnsupportedResourceCondition("Only reviewed GitHub write combinations are supported.")
    condition = parse_resource_condition(policy.resource, policy.custom_resource)
    if condition is None:
        return None
    terms = condition_terms(condition)
    if isinstance(condition, BranchCondition) or (
        key == ("merge", "pull_request") and condition.field in {"source_branch", "target_branch"}
    ):
        if key not in {("create", "pull_request"), ("merge", "pull_request")}:
            raise UnsupportedResourceCondition("Branch routes require PR creation or merging.")
        for term in terms:
            try:
                _argument_value(term.field, term.value)
            except InvalidResourceArguments as error:
                raise UnsupportedResourceCondition("A canonical branch name is required.") from error
        return GithubBranchBinding(GITHUB_WRITE_TOOL_MAPPINGS[key][0], condition)
    argument = FIELD_BINDINGS.get((*key, condition.field))
    if argument is None or (key == ("push", "file") and condition.value == "README.md"):
        raise UnsupportedResourceCondition("This action/resource has no complete reviewed argument binding.")
    try:
        _argument_value(condition.field, condition.value)
    except InvalidResourceArguments as error:
        raise UnsupportedResourceCondition("The resource literal requires administrator review.") from error
    tool_name, = GITHUB_WRITE_TOOL_MAPPINGS[key]
    return GithubResourceBinding(
        tool_name, argument, condition,
        method=policy.action if tool_name == "issue_write" else None,
    )
