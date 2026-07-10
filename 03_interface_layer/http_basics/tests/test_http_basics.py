"""
HTTP の解析・組み立ての動作確認。
実行： uv run pytest 03_interface_layer/http_basics -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http_basics import build_response, parse_request


def test_parse_request_line():
    raw = "GET /users/1 HTTP/1.1\r\nHost: x\r\n\r\n"
    req = parse_request(raw)
    assert req.method == "GET"
    assert req.path == "/users/1"
    assert req.version == "HTTP/1.1"


def test_parse_query_string():
    raw = "GET /search?q=cat&page=2 HTTP/1.1\r\n\r\n"
    req = parse_request(raw)
    assert req.path == "/search"
    assert req.query == {"q": "cat", "page": "2"}


def test_parse_headers_are_case_insensitive():
    raw = "GET / HTTP/1.1\r\nContent-Type: application/json\r\nHOST: x\r\n\r\n"
    req = parse_request(raw)
    # ヘッダ名は小文字化して引ける
    assert req.headers["content-type"] == "application/json"
    assert req.headers["host"] == "x"


def test_parse_body():
    raw = "POST /users HTTP/1.1\r\nContent-Type: application/json\r\n\r\n{\"n\":1}"
    req = parse_request(raw)
    assert req.method == "POST"
    assert req.body == '{"n":1}'


def test_build_response_status_line():
    res = build_response(404)
    assert res.startswith("HTTP/1.1 404 Not Found\r\n")


def test_build_response_auto_content_length():
    body = "hello"
    res = build_response(200, {}, body)
    assert "Content-Length: 5\r\n" in res
    # ヘッダとボディは空行で区切られ、末尾に本文が来る
    assert res.endswith("\r\n\r\nhello")


def test_build_response_content_length_utf8_bytes():
    body = "あ"                       # UTF-8 で 3 バイト
    res = build_response(200, {}, body)
    assert "Content-Length: 3\r\n" in res


def test_round_trip_parse_of_built_response_headers():
    res = build_response(201, {"Content-Type": "text/plain"}, "ok")
    # レスポンスもリクエストと同じヘッダ/ボディ構造なので、境界で分割できる
    head, _, body = res.partition("\r\n\r\n")
    assert body == "ok"
    assert "Content-Type: text/plain" in head
