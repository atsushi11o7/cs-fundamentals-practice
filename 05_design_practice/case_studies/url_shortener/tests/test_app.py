"""
統合 API アプリ（01 キャッシュ + 03 ルータ + 04 レート制限）の動作確認。
実行： uv run pytest 05_design_practice/case_studies/url_shortener -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import UrlShortenerApp


def test_create_returns_201_with_code():
    app = UrlShortenerApp()
    status, body = app.handle("POST", "/api/urls", {"long_url": "https://example.com/a"})
    assert status == 201
    assert "code" in body


def test_create_without_url_returns_400():
    app = UrlShortenerApp()
    assert app.handle("POST", "/api/urls", {}) == (400, {"error": "long_url required"})


def test_redirect_returns_302_with_location():
    app = UrlShortenerApp()
    _, body = app.handle("POST", "/api/urls", {"long_url": "https://example.com/a"})
    status, resp = app.handle("GET", "/" + body["code"])
    assert status == 302
    assert resp["location"] == "https://example.com/a"


def test_redirect_unknown_returns_404():
    app = UrlShortenerApp()
    assert app.handle("GET", "/zzz")[0] == 404


def test_wrong_method_returns_405():
    app = UrlShortenerApp()
    # /api/urls に GET は無い（POST のみ）→ 03 Router が 405 を返す
    assert app.handle("GET", "/api/urls")[0] == 405


def test_resolve_is_served_from_cache():
    app = UrlShortenerApp()
    _, body = app.handle("POST", "/api/urls", {"long_url": "https://example.com/a"})
    code = body["code"]

    app.handle("GET", "/" + code)                 # 1回目でキャッシュに載る
    # 核のストアから消しても、キャッシュから解決できる＝キャッシュが効いている証拠
    del app.service._url_by_code[code]
    status, resp = app.handle("GET", "/" + code)
    assert status == 302
    assert resp["location"] == "https://example.com/a"


def test_clicks_counted_even_on_cache_hit():
    app = UrlShortenerApp()
    _, body = app.handle("POST", "/api/urls", {"long_url": "https://example.com/a"})
    code = body["code"]
    app.handle("GET", "/" + code)                 # ミス→DB→キャッシュ
    app.handle("GET", "/" + code)                 # ヒット
    assert app.service.clicks(code) == 2          # 計測はキャッシュと独立


def test_create_is_rate_limited():
    app = UrlShortenerApp(create_capacity=3)
    results = [
        app.handle("POST", "/api/urls", {"long_url": "https://e", "client": "bob"})[0]
        for _ in range(4)
    ]
    assert results == [201, 201, 201, 429]        # バースト3まで、4回目は 429


def test_rate_limit_is_per_client():
    app = UrlShortenerApp(create_capacity=1)
    assert app.handle("POST", "/api/urls", {"long_url": "https://e", "client": "a"})[0] == 201
    # 別クライアントは独立して許可される
    assert app.handle("POST", "/api/urls", {"long_url": "https://e", "client": "b"})[0] == 201
    assert app.handle("POST", "/api/urls", {"long_url": "https://e", "client": "a"})[0] == 429
