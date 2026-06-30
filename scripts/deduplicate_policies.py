from _bootstrap import bootstrap_src

bootstrap_src()

import argparse

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.policy_service import consolidate_equivalent_policies


def main() -> None:
    """Preview or apply consolidation of legacy equivalent policies."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit consolidation. Without this flag the transaction rolls back.",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        results = consolidate_equivalent_policies(db)
        if args.apply:
            db.commit()
        else:
            db.rollback()

    mode = "applied" if args.apply else "previewed"
    print(f"Policy duplicate consolidation {mode}.")
    if not results:
        print("- no equivalent policy definitions found")
        return

    for result in results:
        print(
            f"- kept policy {result.canonical_policy_id}; "
            f"removed policy {result.removed_policy_id}; "
            f"reassigned app links {result.reassigned_app_assignments}; "
            f"merged app links {result.merged_app_assignments}; "
            f"merged global link {result.global_assignment_merged}"
        )


if __name__ == "__main__":
    main()
