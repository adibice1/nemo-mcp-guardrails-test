from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from _management_auth import install_management_admin_override

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import LlmConfigRecord


def main() -> None:
    """Verify LLM configurations can be created and safely listed."""

    install_management_admin_override()
    suffix = uuid4().hex
    enabled_name = f"Enabled config {suffix}"
    disabled_name = f"Disabled config {suffix}"
    created_id: int | None = None

    with SessionLocal() as db:
        records = [
            LlmConfigRecord(
                name=enabled_name,
                provider="azure_openai",
                model_name="demo-main",
                endpoint="https://example.openai.azure.com",
                credential_reference="env:SECRET_MAIN",
                enabled=True,
            ),
            LlmConfigRecord(
                name=disabled_name,
                provider="azure_openai",
                model_name="demo-disabled",
                credential_reference="env:SECRET_DISABLED",
                enabled=False,
            ),
        ]
        db.add_all(records)
        db.commit()

        try:
            with TestClient(app) as client:
                created_name = f"Created config {suffix}"
                create_response = client.post(
                    "/llm-configs",
                    json={
                        "name": created_name,
                        "provider": "azure_openai",
                        "model_name": "created-deployment",
                        "endpoint": "https://created.openai.azure.com",
                        "credential_reference": "env:CREATED_AZURE_KEY",
                        "enabled": True,
                    },
                )
                assert create_response.status_code == 201, create_response.text
                created_id = create_response.json()["id"]
                assert "credential_reference" not in create_response.json()

                duplicate_response = client.post(
                    "/llm-configs",
                    json={
                        "name": created_name,
                        "provider": "azure_openai",
                        "model_name": "another-deployment",
                        "enabled": True,
                    },
                )
                assert duplicate_response.status_code == 409

                invalid_reference_response = client.post(
                    "/llm-configs",
                    json={
                        "name": f"Invalid config {suffix}",
                        "provider": "azure_openai",
                        "model_name": "invalid-deployment",
                        "credential_reference": "env:INVALID VARIABLE",
                        "enabled": True,
                    },
                )
                assert invalid_reference_response.status_code == 400

                response = client.get("/llm-configs")
            assert response.status_code == 200, response.text

            items = {
                item["name"]: item
                for item in response.json()
                if item["name"] in {enabled_name, disabled_name}
            }
            assert set(items) == {enabled_name, disabled_name}
            assert items[enabled_name]["enabled"] is True
            assert items[disabled_name]["enabled"] is False
            assert all("credential_reference" not in item for item in items.values())
        finally:
            if created_id is not None:
                created = db.get(LlmConfigRecord, created_id)
                if created is not None:
                    db.delete(created)
            for record in records:
                db.delete(record)
            db.commit()

    print("LLM configuration API checks passed.")
    print("- Enabled and disabled configurations are readable.")
    print("- Azure configurations can be created with env references.")
    print("- Duplicate names and invalid env references are rejected.")
    print("- Credential references are not returned.")


if __name__ == "__main__":
    main()
