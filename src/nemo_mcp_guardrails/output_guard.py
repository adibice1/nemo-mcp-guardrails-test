import re
from collections.abc import Iterable


EXPLICIT_OUTPUT_PHRASE_PATTERN = re.compile(
    r"\b(?:cannot|must\s+not|do\s+not|never)\s+"
    r"(?:say|contain|include|mention)\s+"
    r"(?P<quote>['\"])(?P<phrase>.+?)(?P=quote)",
    re.IGNORECASE,
)


def extract_blocked_output_phrases(rule_text: str) -> tuple[str, ...]:
    """Extract explicit quoted phrases that an output rule prohibits."""

    phrases: list[str] = []
    for match in EXPLICIT_OUTPUT_PHRASE_PATTERN.finditer(rule_text):
        phrase = " ".join(match.group("phrase").split())
        if phrase and phrase.casefold() not in {item.casefold() for item in phrases}:
            phrases.append(phrase)
    return tuple(phrases)


def compile_blocked_output_phrases(rule_texts: Iterable[str]) -> tuple[str, ...]:
    """Compile unique deterministic phrases from a sequence of output rules."""

    phrases: list[str] = []
    seen: set[str] = set()
    for rule_text in rule_texts:
        for phrase in extract_blocked_output_phrases(rule_text):
            normalized = phrase.casefold()
            if normalized not in seen:
                seen.add(normalized)
                phrases.append(phrase)
    return tuple(phrases)


def find_blocked_output_phrase(
    response: str,
    blocked_phrases: Iterable[str],
) -> str | None:
    """Return the first prohibited phrase present in an assistant response."""

    normalized_response = " ".join(response.split()).casefold()
    for phrase in blocked_phrases:
        normalized_phrase = " ".join(phrase.split()).casefold()
        if not normalized_phrase:
            continue

        pattern = re.compile(
            rf"(?<!\w){re.escape(normalized_phrase).replace(r'\ ', r'\s+')}"
            r"(?!\w)"
        )
        if pattern.search(normalized_response):
            return phrase
    return None
