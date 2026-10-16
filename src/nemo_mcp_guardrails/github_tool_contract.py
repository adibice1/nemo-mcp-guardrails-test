"""Compile reviewed GitHub write routes without constructing a live runtime."""

from dataclasses import dataclass, field
from typing import Any

from nemo_mcp_guardrails.github_resource_bindings import (
    GithubBranchBinding, GithubResourceBinding, InvalidResourceArguments, compile_resource_binding,
)
from nemo_mcp_guardrails.policy_compiler import (
    GITHUB_METADATA_TOOL_MAPPINGS, GITHUB_WRITE_TOOL_MAPPINGS, InputPolicyObject,
)


REVIEWED_MCP_IMAGE = (
    "ghcr.io/github/github-mcp-server@sha256:"
    "e3816a476a977cfb836e7d221510011436c654d11861db66ecfd826601aba6a4"
)
REVIEWED_NATIVE_BINARY = "/usr/local/bin/github-mcp-server"
METHODS = {
    "issue_write": frozenset({"create", "update"}),
    "pull_request_review_write": frozenset({
        "create", "submit_pending", "delete_pending", "resolve_thread", "unresolve_thread",
    }),
}


@dataclass(frozen=True)
class WriteRoute:
    """Identify a direct or indirect write, including shared-tool discriminators."""

    tool_name: str
    method: str | None = None
    auto_init_only: bool = False

    def applies(self, arguments: dict[str, Any]) -> bool:
        """Reject unreviewed methods or malformed side-effect switches."""

        if self.tool_name in METHODS:
            method = arguments.get("method")
            if not isinstance(method, str) or method not in METHODS[self.tool_name]:
                raise InvalidResourceArguments("The write method cannot be established.")
            if self.method is not None and method != self.method:
                return False
        if self.auto_init_only:
            auto_init = arguments.get("autoInit", False)
            if type(auto_init) is not bool:
                raise InvalidResourceArguments("Repository initialization cannot be established.")
            return auto_init
        return True


FILE_COMMITS = (WriteRoute("create_or_update_file"), WriteRoute("push_files"),
                WriteRoute("delete_file"), WriteRoute("merge_pull_request"))
INITIALIZATION = (WriteRoute("create_repository", auto_init_only=True), WriteRoute("fork_repository"))
EXTRA_ROUTES = {
    ("update", "issue"): (WriteRoute("update_pull_request"), WriteRoute("merge_pull_request")),
    ("update", "pull_request"): (WriteRoute("issue_write", "update"), WriteRoute("merge_pull_request")),
    ("create", "branch"): (WriteRoute("push_files"), WriteRoute("create_or_update_file"), *INITIALIZATION),
    ("create", "file"): (WriteRoute("push_files"), WriteRoute("merge_pull_request"), *INITIALIZATION),
    ("update", "file"): (WriteRoute("push_files"), WriteRoute("merge_pull_request")),
    ("delete", "file"): (WriteRoute("merge_pull_request"),),
    ("push", "file"): (*FILE_COMMITS, *INITIALIZATION),
    ("create", "repository"): (WriteRoute("fork_repository"),),
}


@dataclass(frozen=True)
class GithubExecutionRule:
    """Keep immutable write routes and authoritative target bindings together."""

    routes: tuple[WriteRoute, ...]
    bindings: tuple[GithubResourceBinding | GithubBranchBinding, ...] = field(repr=False)

    @property
    def tool_names(self) -> frozenset[str]:
        """Return reporting names; this set alone is not an execution decision."""

        return frozenset(route.tool_name for route in self.routes)

    def matches(self, tool_name: str, arguments: dict[str, Any], *, branch_state: dict | None = None) -> bool:
        """Match a policy or refuse an indeterminate target before any tool call."""

        routes = tuple(route for route in self.routes if route.tool_name == tool_name)
        if not routes:
            return False
        if not isinstance(arguments, dict):
            raise InvalidResourceArguments("Tool arguments must be an object.")
        if not any(route.applies(arguments) for route in routes):
            return False
        if not self.bindings:
            return True
        for binding in self.bindings:
            if binding.tool_name == tool_name:
                if isinstance(binding, GithubBranchBinding):
                    return binding.matches(tool_name, arguments, branch_state=branch_state)
                return binding.matches(tool_name, arguments)
        raise InvalidResourceArguments("The policy target is not observable for this write route.")


def compile_github_execution_rule(policy: InputPolicyObject) -> GithubExecutionRule:
    """Include reviewed cross-tool effects without inventing remote resource state."""

    binding = compile_resource_binding(policy)
    key = (policy.action, policy.resource)
    tool_name, = GITHUB_WRITE_TOOL_MAPPINGS[key]
    routes = (WriteRoute(tool_name, policy.action if tool_name == "issue_write" else None),
              *EXTRA_ROUTES.get(key, ()))
    bindings = [] if binding is None else [binding]
    if binding is not None:
        if key == ("update", "issue"):
            bindings.extend(GithubResourceBinding(name, "pullNumber", binding.condition)
                            for name in ("update_pull_request", "merge_pull_request"))
        elif key == ("create", "repository"):
            bindings.append(GithubResourceBinding("fork_repository", "repo", binding.condition))
        elif key == ("push", "file"):
            bindings.extend(GithubResourceBinding(name, "path", binding.condition)
                            for name in ("create_or_update_file", "delete_file"))
    return GithubExecutionRule(tuple(dict.fromkeys(routes)), tuple(bindings))


WRITE_FIELDS = {
    "issue_write": {"method": "string", "title": "string", "issue_number": "number"},
    "add_issue_comment": {"issue_number": "number"},
    "create_pull_request": {"title": "string", "head": "string", "base": "string"},
    "update_pull_request": {"pullNumber": "number"},
    "merge_pull_request": {"pullNumber": "number"},
    "pull_request_review_write": {"method": "string", "pullNumber": "number"},
    "create_branch": {"branch": "string"},
    "create_or_update_file": {"path": "string"},
    "delete_file": {"path": "string"},
    "push_files": {"files": "array"},
    "create_repository": {"name": "string", "autoInit": "boolean"},
    "fork_repository": {"repo": "string"},
}

READ_PR_FIELDS = {"method": "string", "owner": "string", "repo": "string", "pullNumber": "number"}


def select_reviewed_github_tools(tools: list[Any]) -> tuple[Any, ...]:
    """Admit only reviewed names and reject drift in enforcement-relevant schemas."""

    allowed = {name for names in GITHUB_METADATA_TOOL_MAPPINGS.values() for name in names}
    selected = []
    seen = set()
    for tool in tools:
        name = getattr(tool, "name", None)
        if not isinstance(name, str) or name in seen:
            raise ValueError("GitHub MCP tool contract is unavailable.")
        seen.add(name)
        if name not in allowed:
            continue
        schema = getattr(tool, "args_schema", None)
        if not isinstance(schema, dict) or schema.get("type") != "object":
            raise ValueError("GitHub MCP tool contract is unavailable.")
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            raise ValueError("GitHub MCP tool contract is unavailable.")
        fields = READ_PR_FIELDS if name == "pull_request_read" else WRITE_FIELDS.get(name, {})
        for argument, expected in fields.items():
            definition = properties.get(argument)
            types = {expected, "integer"} if expected == "number" else {expected}
            if not isinstance(definition, dict) or not isinstance(definition.get("type"), str) or definition["type"] not in types:
                raise ValueError("GitHub MCP tool contract is unavailable.")
        if name == "pull_request_read":
            methods = properties["method"].get("enum")
            if not isinstance(methods, list) or "get" not in methods or any(not isinstance(method, str) for method in methods):
                raise ValueError("GitHub PR metadata contract is unavailable.")
        if name in METHODS:
            methods = properties["method"].get("enum")
            if not isinstance(methods, list) or any(not isinstance(item, str) for item in methods) or set(methods) != METHODS[name]:
                raise ValueError("GitHub MCP tool contract is unavailable.")
        if name == "push_files":
            items = properties["files"].get("items")
            path = items.get("properties", {}).get("path") if isinstance(items, dict) and isinstance(items.get("properties"), dict) else None
            if (
                not isinstance(items, dict) or items.get("type") != "object"
                or not isinstance(path, dict) or path.get("type") != "string"
            ):
                raise ValueError("GitHub MCP tool contract is unavailable.")
        selected.append(tool)
    if not selected:
        raise ValueError("GitHub MCP tool contract is unavailable.")
    return tuple(selected)
