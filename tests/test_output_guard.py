from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.output_guard import (
    compile_blocked_output_phrases,
    extract_blocked_output_phrases,
    find_blocked_output_phrase,
)


def main() -> None:
    """Verify deterministic output phrase extraction and matching."""

    assert extract_blocked_output_phrases("Cannot say 'hello'.") == ("hello",)
    assert extract_blocked_output_phrases('The bot must not include "private data".') == (
        "private data",
    )
    assert extract_blocked_output_phrases(
        "Do not allow the word 'hello' in the response output."
    ) == ("hello",)
    assert extract_blocked_output_phrases("Don't say the phrase 'Project Alpha'.") == (
        "Project Alpha",
    )
    assert extract_blocked_output_phrases("dont have word 'adib'.") == ("adib",)
    assert extract_blocked_output_phrases("No word 'blocked'.") == ("blocked",)
    assert extract_blocked_output_phrases("No profanities.") == ()

    phrases = compile_blocked_output_phrases(
        ("Cannot say 'hello'.", 'Do not mention "Project Alpha".')
    )
    assert phrases == ("hello", "Project Alpha")
    assert find_blocked_output_phrase("Hello! How can I help?", phrases) == "hello"
    assert (
        find_blocked_output_phrase("The PROJECT ALPHA launch is tomorrow.", phrases)
        == "Project Alpha"
    )
    assert find_blocked_output_phrase("A harmless response.", phrases) is None
    assert find_blocked_output_phrase("shelloworld", ("hello",)) is None

    print("Deterministic output phrase checks passed.")


if __name__ == "__main__":
    main()
