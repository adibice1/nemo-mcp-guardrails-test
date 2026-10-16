"""Parse literal resource selectors; tool-field binding is a separate step."""

import json
import re
from dataclasses import dataclass


class UnsupportedResourceCondition(ValueError):
    """Reject conditions outside literal equality and bounded PR branch routing."""


@dataclass(frozen=True)
class ResourceCondition:
    """Preserve one resource field and its exact literal value."""

    field: str
    value: str | int
    operator: str = "eq"


@dataclass(frozen=True)
class BranchCondition:
    """Represent at most two distinct branch comparisons joined by AND."""

    terms: tuple[ResourceCondition, ...]


def condition_terms(condition: ResourceCondition | BranchCondition) -> tuple[ResourceCondition, ...]:
    """Expose a shared immutable comparison representation."""
    return condition.terms if isinstance(condition, BranchCondition) else (condition,)


def condition_text(condition: ResourceCondition | BranchCondition) -> str:
    """Render canonical selectors without interpreting their literal values."""
    return " AND ".join(
        f"{term.field} {'!=' if term.operator == 'neq' else '='} {json.dumps(term.value, ensure_ascii=False)}"
        for term in condition_terms(condition)
    )


def _branch_condition(text: str) -> ResourceCondition | BranchCondition:
    """Parse quoted branch equality/inequality without arbitrary Boolean logic."""
    pattern = re.compile(r'(source_branch|target_branch)\s*(!=|=)\s*("(?:[^"\\]|\\.)*")', re.IGNORECASE)
    terms = []
    while text:
        match = pattern.match(text)
        if match is None:
            raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
        field, operator, literal = match.groups()
        terms.append(ResourceCondition(field.lower(), _literal_text(literal, legacy=False),
                                       "neq" if operator == "!=" else "eq"))
        text = text[match.end():]
        if not text:
            break
        separator = re.match(r"\s+AND\s+", text, re.IGNORECASE)
        if separator is None:
            raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
        text = text[separator.end():]
        if not text:
            raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
    if len(terms) > 2 or len({term.field for term in terms}) != len(terms):
        raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
    terms.sort(key=lambda term: term.field)
    if len(terms) == 1 and terms[0].operator == "eq":
        return terms[0]
    return BranchCondition(tuple(terms))


RESOURCE_FIELDS = {
    "issue": ("title", "number"),
    "pull_request": ("title", "number", "source_branch", "target_branch"),
    "file": ("path",),
    "branch": ("branch",),
    "repository": ("name",),
}
RESOURCE_PREFIXES = {
    "issue": r"issues?",
    "pull_request": r"pull[ _]requests?",
    "file": r"files?",
    "branch": r"branch(?:es)?",
    "repository": r"repositor(?:y|ies)",
}
UNSUPPORTED_MESSAGE = (
    "Use one supported resource field with a quoted literal equality, "
    "or a simple legacy resource name. PR branch selectors also support != "
    "and AND between source_branch and target_branch. Other logic and workflows are unsupported."
)


def _literal_text(text: str, *, legacy: bool) -> str:
    """Read a quoted string or a legacy single-token literal without coercion."""

    if text.startswith('"'):
        try:
            value = json.loads(text)
        except (ValueError, RecursionError) as error:
            raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE) from error
    elif re.fullmatch(r"'[^'\\]*'", text):
        value = text[1:-1]
    elif legacy and re.fullmatch(r"[\w./-]+", text):
        value = text
    else:
        raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)

    if (
        not isinstance(value, str) or not value.strip()
        or any(
            ord(char) < 32 or 127 <= ord(char) < 160 or 0xD800 <= ord(char) <= 0xDFFF
            for char in value
        )
    ):
        raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
    return value


def parse_resource_condition(
    resource: str,
    custom_resource: str | None,
) -> ResourceCondition | BranchCondition | None:
    """Parse reviewed selectors while preserving literal identity and branch case."""

    if custom_resource is None:
        return None
    if not isinstance(custom_resource, str) or len(custom_resource) > 1000:
        raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
    text = custom_resource.strip()
    if not text:
        return None
    if resource not in RESOURCE_FIELDS:
        raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)

    fields = RESOURCE_FIELDS[resource]
    if resource == "pull_request" and re.match(r"(?:source_branch|target_branch)\s*(?:!=|=)", text, re.IGNORECASE):
        return _branch_condition(text)
    explicit = re.fullmatch(r"([a-z_]+)\s*=\s*(.+)", text, flags=re.IGNORECASE)
    if explicit:
        field, value_text = explicit.group(1).lower(), explicit.group(2)
    else:
        text = re.sub(
            rf"^(?:{RESOURCE_PREFIXES[resource]})\s+", "", text, flags=re.IGNORECASE,
        )
        number = re.fullmatch(r"(?:#\s*|number(?:ed)?\s+)([0-9]+)", text, re.IGNORECASE)
        if number and "number" in fields:
            field, value_text = "number", number.group(1)
        else:
            field = fields[0]
            qualifiers = rf"(?:name|named|called|titled|{field})"
            value_text = re.sub(rf"^{qualifiers}\s+", "", text, flags=re.IGNORECASE)

    if field not in fields:
        raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
    if field == "number":
        if not re.fullmatch(r"[1-9][0-9]*", value_text):
            raise UnsupportedResourceCondition(UNSUPPORTED_MESSAGE)
        value: str | int = int(value_text)
    else:
        value = _literal_text(value_text, legacy=explicit is None)
    return ResourceCondition(field, value)
