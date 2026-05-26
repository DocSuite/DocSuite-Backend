def test_auth_routes_are_registered(client) -> None:
    paths = {route.path for route in client.app.routes}
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/audits" in paths
