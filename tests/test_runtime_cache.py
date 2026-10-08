import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Any

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails import runtime_factory


def _restore_env(name: str, value: str | None) -> None:
    """Restore one environment variable after an isolated check."""

    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


async def run_checks() -> None:
    """Verify runtime reuse, invalidation, concurrency, and cache disabling."""

    original_revision_loader: Callable[[int], tuple[Any, ...]] = (
        runtime_factory.load_runtime_revision
    )
    original_builder: Callable[[int], Awaitable[Any]] = (
        runtime_factory._build_guardrails_runtime_parts_uncached
    )
    original_ttl = os.environ.get("NEMO_RUNTIME_CACHE_TTL_SECONDS")
    original_max_apps = os.environ.get("NEMO_RUNTIME_CACHE_MAX_APPS")
    revisions = {1: ("revision-1",)}
    builds: list[int] = []

    async def fake_builder(app_id: int) -> object:
        builds.append(app_id)
        await asyncio.sleep(0.01)
        return object()

    try:
        os.environ["NEMO_RUNTIME_CACHE_TTL_SECONDS"] = "300"
        os.environ["NEMO_RUNTIME_CACHE_MAX_APPS"] = "32"
        runtime_factory.load_runtime_revision = lambda app_id: revisions[app_id]
        runtime_factory._build_guardrails_runtime_parts_uncached = fake_builder
        runtime_factory.clear_guardrails_runtime_cache()

        first = await runtime_factory.build_guardrails_runtime_parts(1)
        second = await runtime_factory.build_guardrails_runtime_parts(1)
        assert first is second
        assert builds == [1]

        revisions[1] = ("revision-2",)
        third = await runtime_factory.build_guardrails_runtime_parts(1)
        assert third is not first
        assert builds == [1, 1]

        runtime_factory.clear_guardrails_runtime_cache()
        builds.clear()
        concurrent = await asyncio.gather(
            *(runtime_factory.build_guardrails_runtime_parts(1) for _ in range(3))
        )
        assert concurrent[0] is concurrent[1] is concurrent[2]
        assert builds == [1]

        os.environ["NEMO_RUNTIME_CACHE_TTL_SECONDS"] = "0"
        uncached_first = await runtime_factory.build_guardrails_runtime_parts(1)
        uncached_second = await runtime_factory.build_guardrails_runtime_parts(1)
        assert uncached_first is not uncached_second
        assert builds == [1, 1, 1]
    finally:
        runtime_factory.load_runtime_revision = original_revision_loader
        runtime_factory._build_guardrails_runtime_parts_uncached = original_builder
        runtime_factory.clear_guardrails_runtime_cache()
        _restore_env("NEMO_RUNTIME_CACHE_TTL_SECONDS", original_ttl)
        _restore_env("NEMO_RUNTIME_CACHE_MAX_APPS", original_max_apps)


def main() -> None:
    """Run the offline runtime-cache checks."""

    asyncio.run(run_checks())
    print("Runtime cache checks passed.")
    print("- Repeated requests reuse one app runtime.")
    print("- Database revision changes force a rebuild.")
    print("- Concurrent cold requests share one build.")
    print("- TTL zero disables runtime reuse.")


if __name__ == "__main__":
    main()
