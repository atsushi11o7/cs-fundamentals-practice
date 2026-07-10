"""
Webパフォーマンス（サーバ側）の動作確認。
実行： uv run pytest 04_reliability_and_scale/web_performance -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_performance import (
    compression_ratio,
    etag_for,
    gzip_compress,
    gzip_decompress,
    handle_conditional_get,
)


def test_etag_same_content_same_etag():
    assert etag_for("hello") == etag_for("hello")


def test_etag_differs_by_content():
    assert etag_for("hello") != etag_for("world")


def test_conditional_get_returns_body_without_validator():
    status, headers, body = handle_conditional_get("data")
    assert status == 200
    assert body == "data"
    assert "ETag" in headers


def test_conditional_get_returns_304_when_etag_matches():
    body = "data"
    _, headers, _ = handle_conditional_get(body)
    status, _, sent = handle_conditional_get(body, if_none_match=headers["ETag"])
    assert status == 304
    assert sent == ""                     # 本文を再送しない


def test_conditional_get_returns_200_when_content_changed():
    _, headers, _ = handle_conditional_get("old")
    old_etag = headers["ETag"]
    # 内容が変わっていれば、古い ETag では 304 にならず本文が返る
    status, _, body = handle_conditional_get("new", if_none_match=old_etag)
    assert status == 200
    assert body == "new"


def test_gzip_round_trip():
    text = "the quick brown fox"
    assert gzip_decompress(gzip_compress(text)) == text


def test_repetitive_text_compresses_well():
    html = "<div>hello</div>" * 500
    assert compression_ratio(html) < 0.5      # 繰り返しが多いので大幅に縮む
