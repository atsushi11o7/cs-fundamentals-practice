"""
最小 REST ルータの動作確認。
実行： uv run pytest 03_interface_layer/rest_api_design -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rest_api import make_users_api


def test_post_creates_returns_201():
    api = make_users_api()
    status, user = api.dispatch("POST", "/users", {"name": "alice"})
    assert status == 201
    assert user["id"] == 1
    assert user["name"] == "alice"


def test_get_collection_and_item():
    api = make_users_api()
    api.dispatch("POST", "/users", {"name": "alice"})
    status, users = api.dispatch("GET", "/users")
    assert status == 200
    assert len(users) == 1

    status, user = api.dispatch("GET", "/users/1")
    assert status == 200
    assert user["name"] == "alice"


def test_get_missing_returns_404():
    api = make_users_api()
    assert api.dispatch("GET", "/users/999") == (404, None)


def test_post_is_not_idempotent():
    api = make_users_api()
    api.dispatch("POST", "/users", {"name": "alice"})
    api.dispatch("POST", "/users", {"name": "alice"})
    # 同じ内容でも POST を繰り返すと別リソースが増える
    _, users = api.dispatch("GET", "/users")
    assert [u["id"] for u in users] == [1, 2]


def test_put_replaces_and_is_idempotent():
    api = make_users_api()
    api.dispatch("POST", "/users", {"name": "alice"})

    s1, u1 = api.dispatch("PUT", "/users/1", {"name": "ALICE"})
    s2, u2 = api.dispatch("PUT", "/users/1", {"name": "ALICE"})
    assert s1 == s2 == 200
    # 同じ PUT を繰り返しても状態は変わらない（べき等）
    assert u1 == u2 == {"id": 1, "name": "ALICE"}
    _, users = api.dispatch("GET", "/users")
    assert len(users) == 1


def test_put_missing_returns_404():
    api = make_users_api()
    assert api.dispatch("PUT", "/users/999", {"name": "x"}) == (404, None)


def test_delete_then_get_is_404():
    api = make_users_api()
    api.dispatch("POST", "/users", {"name": "alice"})
    assert api.dispatch("DELETE", "/users/1") == (204, None)
    assert api.dispatch("GET", "/users/1") == (404, None)


def test_unknown_path_returns_404():
    api = make_users_api()
    assert api.dispatch("GET", "/unknown") == (404, None)


def test_wrong_method_returns_405():
    api = make_users_api()
    api.dispatch("POST", "/users", {"name": "alice"})
    # /users/1 は在るが POST は定義されていない → 405
    assert api.dispatch("POST", "/users/1") == (405, None)
