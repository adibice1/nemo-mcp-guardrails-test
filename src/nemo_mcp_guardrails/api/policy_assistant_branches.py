"""Compile branch-authoring intent and derive previews from the actual matcher."""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from nemo_mcp_guardrails.github_resource_bindings import GithubBranchBinding
from nemo_mcp_guardrails.resource_conditions import (
    BranchCondition, ResourceCondition, UnsupportedResourceCondition,
    condition_terms, condition_text,
)


class BranchComparison(BaseModel):
    """Describe one exact, case-sensitive branch comparison."""

    model_config = ConfigDict(extra="forbid", strict=True)

    field: Literal["source_branch", "target_branch"]
    operator: Literal["eq", "neq"]
    value: str = Field(min_length=1, max_length=255)


class BranchIntent(BaseModel):
    """Separate matching blocks from a source allowance scoped to one target."""

    model_config = ConfigDict(extra="forbid", strict=True)

    mode: Literal["block_matching", "restrict_target_to_source"]
    terms: list[BranchComparison] = Field(min_length=1, max_length=2)

    def selector(self) -> str:
        """Compile the prohibited scope without allowing an override of other rules."""
        terms = {term.field: term for term in self.terms}
        if len(terms) != len(self.terms):
            raise UnsupportedResourceCondition("Branch fields must be distinct.")
        if self.mode == "restrict_target_to_source" and (
            set(terms) != {"source_branch", "target_branch"}
            or any(term.operator != "eq" for term in self.terms)
        ):
            raise UnsupportedResourceCondition("A scoped allowance needs an exact source and target.")
        return condition_text(BranchCondition(tuple(
            ResourceCondition(term.field, term.value,
                "neq" if self.mode == "restrict_target_to_source" and term.field == "source_branch"
                else term.operator)
            for term in sorted(self.terms, key=lambda term: term.field)
        )))


def branch_preview(
    condition: ResourceCondition | BranchCondition, action: str,
) -> tuple[str, str, list[dict[str, str]]]:
    """Generate branch wording and example decisions from the validated condition."""
    terms = condition_terms(condition)
    operation = "creation" if action == "create" else "merging"
    scope = " and ".join(
        f"the {'source' if term.field == 'source_branch' else 'target'} branch "
        f"{'is not' if term.operator == 'neq' else 'is'} {json.dumps(term.value, ensure_ascii=False)}"
        for term in terms
    )
    explanation = f"Block PR {operation} when {scope}. Other routes do not match this policy."
    if action == "merge":
        explanation += " Selective merging is unavailable: matching merges block; other branch-conditional merges are refused."
    if len(explanation) > 400:
        raise UnsupportedResourceCondition("Branch names are too long for a complete preview.")

    def other(value: str) -> str:
        """Choose a valid, explicitly illustrative different branch name."""
        return "gms-preview-other" if value != "gms-preview-other" else "gms-preview-other-2"

    matching = {"head": "gms-preview-source", "base": "gms-preview-target"}
    for term in terms:
        argument = "head" if term.field == "source_branch" else "base"
        matching[argument] = other(term.value) if term.operator == "neq" else term.value
    cases = [matching]
    for term in terms:
        argument = "head" if term.field == "source_branch" else "base"
        cases.append({**matching, argument: term.value if term.operator == "neq" else other(term.value)})

    binding = GithubBranchBinding("create_pull_request", condition)
    examples = []
    for arguments in cases:
        prompt = (
            f"{'Create' if action == 'create' else 'Merge'} a pull request from "
            f"{json.dumps(arguments['head'], ensure_ascii=False)} into "
            f"{json.dumps(arguments['base'], ensure_ascii=False)}."
        )
        if len(prompt) > 350:
            raise UnsupportedResourceCondition("Branch names are too long for a complete example.")
        examples.append({"prompt": prompt, "expected": "block" if binding.matches(
            "create_pull_request", arguments,
        ) else "not_blocked_by_this_policy"})
    return f"Block PR {operation} by branch", explanation, examples
