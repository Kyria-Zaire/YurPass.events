"""Health endpoint tests."""

EXPECTED_HEALTH_KEYS = {
    "status",
    "service",
    "version",
    "environment",
    "database",
    "redis",
}


def test_api_health_returns_full_payload(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200

    payload = response.json()
    assert set(payload.keys()) == EXPECTED_HEALTH_KEYS
    assert payload["status"] == "ok"
    assert payload["service"] == "yurpass-backend"
    assert payload["version"] == "0.1.0"
    assert payload["environment"] == "dev"
    assert payload["database"] in {"connected", "not_configured"}
    assert payload["redis"] in {"connected", "not_configured"}


def test_api_health_without_dependencies_is_stable(client) -> None:
    response = client.get("/api/health")
    payload = response.json()

    assert payload["status"] == "ok"
    assert "postgresql" not in response.text.lower()
    assert "redis://" not in response.text
    assert "password" not in response.text.lower()


def test_legacy_health_endpoint_removed(client) -> None:
    response = client.get("/health")
    assert response.status_code == 404
