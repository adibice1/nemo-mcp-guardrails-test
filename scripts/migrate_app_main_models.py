"""Preview/apply additive encrypted-model columns on an explicitly named rehearsal DB."""

import argparse
from _bootstrap import bootstrap_src
bootstrap_src()

from sqlalchemy import text


DDL = (
    "ALTER TABLE llm_configs ADD COLUMN IF NOT EXISTS owner_app_id INTEGER NULL",
    "ALTER TABLE llm_configs ADD COLUMN IF NOT EXISTS encrypted_api_key TEXT NULL",
    "CREATE INDEX IF NOT EXISTS ix_llm_configs_owner_app_id ON llm_configs (owner_app_id)",
    """DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_llm_configs_owner_app'
                       AND conrelid='llm_configs'::regclass) THEN
            ALTER TABLE llm_configs ADD CONSTRAINT fk_llm_configs_owner_app
                FOREIGN KEY (owner_app_id) REFERENCES apps(id) ON DELETE CASCADE;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_llm_configs_owned_credential'
                       AND conrelid='llm_configs'::regclass) THEN
            ALTER TABLE llm_configs ADD CONSTRAINT ck_llm_configs_owned_credential CHECK (
                (owner_app_id IS NULL AND encrypted_api_key IS NULL) OR
                (owner_app_id IS NOT NULL AND encrypted_api_key IS NOT NULL
                 AND credential_reference IS NULL AND endpoint IS NOT NULL));
        END IF;
    END $$""",
)


def migrate(connection, expected_database: str) -> None:
    """Verify target identity before executing transactional PostgreSQL DDL."""
    actual = connection.scalar(text("SELECT current_database()"))
    if actual != expected_database or not actual.startswith("nemo_restore_check_"):
        raise ValueError("Use the exact, explicitly named restored rehearsal database.")
    for statement in DDL:
        connection.execute(text(statement))


def main() -> None:
    """Default to a no-connection preview; never migrate production implicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-database")
    args = parser.parse_args()
    if args.apply and (not args.expected_database
                       or not args.expected_database.startswith("nemo_restore_check_")):
        parser.error("--apply requires --expected-database naming a restored rehearsal database")
    for statement in DDL:
        print(statement)
    if args.apply:
        from nemo_mcp_guardrails.database.connection import engine
        with engine.begin() as connection:
            migrate(connection, args.expected_database)
        print("App-owned main-model schema applied to the verified rehearsal database.")


if __name__ == "__main__":
    main()
