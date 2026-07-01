from starlette.routing import Match

from app import app


def _match_delete_route(path: str):
    scope = {
        'type': 'http',
        'method': 'DELETE',
        'path': path,
        'root_path': '',
        'headers': [],
        'query_string': b'',
    }
    for route in app.router.routes:
        if not hasattr(route, 'matches'):
            continue
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            return route, child_scope
    return None, {}


def test_recognition_history_delete_route_is_not_captured_by_power_id_route():
    route, child_scope = _match_delete_route('/personal/internal-power/recognition-history')

    assert route is not None
    assert route.endpoint.__name__ == 'clear_personal_internal_power_recognition_history'
    assert child_scope.get('path_params') == {}


def test_numeric_internal_power_delete_route_still_matches_power_id():
    route, child_scope = _match_delete_route('/personal/internal-power/123')

    assert route is not None
    assert route.endpoint.__name__ == 'delete_personal_internal_power'
    assert child_scope.get('path_params') == {'power_id': 123}
