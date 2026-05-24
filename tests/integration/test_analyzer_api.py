def test_analyzer_route_is_registered(client) -> None:
    paths = {route.path for route in client.app.routes}
    assert "/api/v1/analyzer/" in paths
