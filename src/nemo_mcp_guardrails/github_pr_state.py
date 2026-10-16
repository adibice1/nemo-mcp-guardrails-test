"""Read PR branches from a trusted connector response, never agent arguments."""

import asyncio
import json

from nemo_mcp_guardrails.github_resource_bindings import InvalidResourceArguments, _argument_value


def parse_pr_branches(result: object, arguments: dict) -> dict:
    """Require the requested PR identity and complete branch metadata."""
    try:
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict) and result[0].get("type") == "text":
            result = result[0]["text"]
        if isinstance(result, str):
            if len(result) > 512 * 1024:
                raise ValueError("Oversized metadata.")
            result = json.loads(result)
        if not isinstance(result, dict):
            raise ValueError("Missing metadata.")
        if type(result.get("number")) is not int or result["number"] != arguments["pullNumber"]:
            raise ValueError("Unexpected PR identity.")
        head, base = result["head"], result["base"]
        full_name = base["repo"]["full_name"]
        expected_name = f"{arguments['owner']}/{arguments['repo']}"
        if not isinstance(full_name, str) or full_name.casefold() != expected_name.casefold():
            raise ValueError("Unexpected repository identity.")
        return {
            "head": _argument_value("source_branch", head["ref"]),
            "base": _argument_value("target_branch", base["ref"]),
        }
    except (ValueError, TypeError, KeyError, RecursionError):
        raise InvalidResourceArguments("Trusted PR branch metadata is unavailable.") from None


def pr_branch_reader(tools: tuple):
    """Build a bounded reader restricted to the pinned MCP get-PR method."""
    reader = next((tool for tool in tools if tool.name == "pull_request_read"), None)

    async def read(arguments: dict) -> dict:
        """Use only validated repository identity and PR number for the lookup."""
        try:
            if reader is None:
                raise ValueError("No trusted reader.")
            owner, repo = arguments.get("owner"), arguments.get("repo")
            if any(not isinstance(value, str) or not value or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-" for char in value) for value in (owner, repo)):
                raise ValueError("Invalid repository identity.")
            number = _argument_value("number", arguments.get("pullNumber"))
            result = await asyncio.wait_for(reader.ainvoke({
                "method": "get", "owner": owner, "repo": repo, "pullNumber": number,
            }), timeout=15)
            return parse_pr_branches(result, {"owner": owner, "repo": repo, "pullNumber": number})
        except Exception:
            raise InvalidResourceArguments("Trusted PR branch lookup failed.") from None

    return read
