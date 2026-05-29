import uvicorn

from _bootstrap import bootstrap_src


def main() -> None:
    """Run the local FastAPI development server."""

    bootstrap_src()
    uvicorn.run(
        "nemo_mcp_guardrails.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
