from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from _management_auth import install_management_admin_override

from nemo_mcp_guardrails.api.main import app
from seed_normalized_policy_metadata import main as seed_normalized_metadata


def main() -> None:
    """Verify policy options follow enabled database tool mappings."""

    install_management_admin_override()
    seed_normalized_metadata()
    with TestClient(app) as client:
        response = client.get("/policy-options")
        assert response.status_code == 200, response.text

    connectors = {item["value"]: item for item in response.json()}
    assert "github" in connectors
    assert "sharepoint" not in connectors

    actions = {
        action["value"]: action
        for action in connectors["github"]["actions"]
    }
    merge_resources = {
        resource["value"] for resource in actions["merge"]["resources"]
    }
    comment_resources = {
        resource["value"] for resource in actions["comment"]["resources"]
    }
    create_resources = {
        resource["value"] for resource in actions["create"]["resources"]
    }

    assert merge_resources == {"pull_request"}
    assert comment_resources == {"issue"}
    assert {"issue", "pull_request", "repository"} <= create_resources

    print("Policy metadata API checks passed.")
    print("- Only connectors with enabled tool mappings are returned.")
    print("- Actions expose only their mapped resources.")


if __name__ == "__main__":
    main()
