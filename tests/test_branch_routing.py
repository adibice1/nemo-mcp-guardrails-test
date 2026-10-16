"""Offline branch truth tables and real guarded-tool invocation boundaries."""

import asyncio
from dataclasses import FrozenInstanceError
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from _bootstrap import bootstrap_src
bootstrap_src()

from nemo_mcp_guardrails.github_pr_state import parse_pr_branches, pr_branch_reader
from nemo_mcp_guardrails.github_resource_bindings import InvalidResourceArguments
from nemo_mcp_guardrails.github_tool_contract import compile_github_execution_rule, select_reviewed_github_tools
from nemo_mcp_guardrails.input_conditions import prepare_input_conditions
from nemo_mcp_guardrails.policy_compiler import InputPolicyObject, compile_policy
from nemo_mcp_guardrails.resource_conditions import BranchCondition, UnsupportedResourceCondition, parse_resource_condition
from nemo_mcp_guardrails.tool_guard import ToolGuardEvaluationError, ToolGuardRule, ToolGuardViolation, guard_mcp_tool


SELECTOR = 'source_branch != "staging" AND target_branch = "production"'


def make_rule(action: str, selector: str = SELECTOR) -> ToolGuardRule:
    """Compile the same immutable execution object used in app runtimes."""
    policy = InputPolicyObject("github", action, "pull_request", "block", selector)
    execution = compile_github_execution_rule(policy)
    return ToolGuardRule(execution.tool_names, selector, execution, 192, "Branch route")


def fake_tool(name: str):
    """Use an observable async boundary rather than invoking any connector."""
    return SimpleNamespace(name=name, description=name, ainvoke=AsyncMock(return_value="executed"),
                           args_schema={"type": "object", "properties": {}, "additionalProperties": True})


async def expect_error(tool, arguments: dict, error_type: type) -> Exception:
    """Require a controlled error at the actual guarded invocation boundary."""
    try:
        await tool.ainvoke(arguments)
    except error_type as error:
        return error
    raise AssertionError("A prohibited or indeterminate tool call executed")


async def invocation_checks() -> None:
    """Exercise create, metadata-backed merge, forged context and lookup failures."""
    raw = fake_tool("create_pull_request")
    wrapped = guard_mcp_tool(raw, guard_rules=(make_rule("create"),))
    for source, target, blocked in (
        ("feature", "production", True), ("staging", "production", False),
        ("feature", "staging", False), ("staging", "staging", False),
        ("Staging", "production", True), ("alice:staging", "production", False),
    ):
        if blocked:
            error = await expect_error(wrapped, {"head": source, "base": target}, ToolGuardViolation)
            assert error.policy_id == 192
        else:
            assert await wrapped.ainvoke({"head": source, "base": target}) == "executed"
    assert raw.ainvoke.await_count == 4
    for arguments in ({"head": "staging"}, {"base": "staging"}, {"head": "alice:org:staging", "base": "production"}):
        await expect_error(wrapped, arguments, ToolGuardEvaluationError)
    assert raw.ainvoke.await_count == 4
    raw_merge = fake_tool("merge_pull_request")
    args = {"owner": "sample", "repo": "example", "pullNumber": 42,
            "head": "staging", "base": "development"}  # Agent-provided branches are ignored.
    metadata = {"number": 42, "head": {"ref": "feature"},
                "base": {"ref": "production", "repo": {"full_name": "sample/example"}}}
    raw_reader = fake_tool("pull_request_read")
    raw_reader.ainvoke.return_value = [{"type": "text", "text": json.dumps(metadata)}]
    reader = pr_branch_reader((raw_reader,))
    guarded_merge = guard_mcp_tool(raw_merge, guard_rules=(make_rule("merge"),), branch_reader=reader)
    await expect_error(guarded_merge, args, ToolGuardViolation)
    assert raw_reader.ainvoke.call_args.args[0] == {"method": "get", "owner": "sample", "repo": "example", "pullNumber": 42}
    # A matching source/target read alone does not close GitHub's retarget race.
    raw_reader.ainvoke.return_value = {**metadata, "head": {"ref": "staging"}}
    await expect_error(guarded_merge, args, ToolGuardEvaluationError)
    raw_reader.ainvoke.side_effect = TimeoutError("PRIVATE credential-like upstream error")
    error = await expect_error(guarded_merge, args, ToolGuardEvaluationError)
    assert "PRIVATE" not in str(error)
    raw_reader.ainvoke.side_effect = None
    raw_reader.ainvoke.return_value = {**metadata, "number": 43}
    await expect_error(guarded_merge, args, ToolGuardEvaluationError)
    await expect_error(guard_mcp_tool(raw_merge, guard_rules=(make_rule("merge"),)), args, ToolGuardEvaluationError)
    broad = ToolGuardRule(frozenset({"merge_pull_request"}))
    reader_failure = AsyncMock(side_effect=AssertionError("Broad blocks need no lookup"))
    await expect_error(guard_mcp_tool(raw_merge, guard_rules=(make_rule("merge"), broad), branch_reader=reader_failure), args, ToolGuardViolation)
    reader_failure.assert_not_awaited()
    raw_merge.ainvoke.assert_not_awaited()
    # Number-only restrictions retain normal nonmatching merge behavior.
    assert await guard_mcp_tool(raw_merge, guard_rules=(make_rule("merge", "number = 17"),)).ainvoke(args) == "executed"


def main() -> None:
    """Verify grammar, compiler, normalization and fail-closed remote boundaries."""
    parsed = parse_resource_condition("pull_request", SELECTOR)
    assert isinstance(parsed, BranchCondition)
    assert parse_resource_condition("pull_request", 'target_branch = "production" and source_branch != "staging"') == parsed
    try:
        parsed.terms = ()
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Branch conditions are mutable")
    for invalid in (
        'source_branch != "staging" OR target_branch = "production"',
        'source_branch != "staging" AND source_branch = "feature"',
        'target_branch = "production" AND', 'source_branch == "staging"',
        'source_branch != "staging" AND title = "release"',
        'source_branch != ""', 'source_branch != "../staging"',
    ):
        try:
            prepare_input_conditions(InputPolicyObject("github", "create", "pull_request", "block"), {"custom_resource": invalid})
        except UnsupportedResourceCondition:
            pass
        else:
            raise AssertionError(f"Unsupported branch expression accepted: {invalid}")
    policy = InputPolicyObject("github", "create", "pull_request", "block", SELECTOR)
    read_tool = fake_tool("pull_request_read")
    for properties in ({}, {"method": {"type": "string", "enum": ["get_diff"]},
                           "owner": {"type": "string"}, "repo": {"type": "string"}, "pullNumber": {"type": "number"}}):
        read_tool.args_schema["properties"] = properties
        try:
            select_reviewed_github_tools([read_tool])
        except ValueError:
            pass
        else:
            raise AssertionError("Unreviewed metadata schema accepted")
    conditions = prepare_input_conditions(policy, {"custom_resource": SELECTOR})
    assert conditions == {"custom_resource": SELECTOR, "resource_condition_version": 2}
    assert prepare_input_conditions(policy, conditions) == conditions
    compiled = compile_policy(policy)
    assert 'does not equal "staging" AND its target branch equals "production"' in compiled.input_rail_rule
    assert "feature/gms-check" in compiled.test_cases[0].prompt
    for action in ("update", "review"):
        try:
            compile_github_execution_rule(InputPolicyObject("github", action, "pull_request", "block", SELECTOR))
        except UnsupportedResourceCondition:
            pass
        else:
            raise AssertionError("Unsupported action accepted branch predicates")
    for metadata in ({}, {"number": 42, "head": {}, "base": {}}, "not JSON"):
        try:
            parse_pr_branches(metadata, {"owner": "a", "repo": "b", "pullNumber": 42})
        except InvalidResourceArguments:
            pass
        else:
            raise AssertionError("Malformed PR metadata was trusted")
    asyncio.run(invocation_checks())
    print("Branch routing passed: conjunction truth tables, canonical storage/compiler and guarded create/merge boundaries.")


if __name__ == "__main__":
    main()
