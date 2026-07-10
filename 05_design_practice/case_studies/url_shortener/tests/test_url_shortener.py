"""
URL短縮サービスの動作確認。
実行： uv run pytest 05_design_practice/case_studies/url_shortener -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from url_shortener import ShortenerService, decode_base62, encode_base62


def test_encode_base62_small_values():
    assert encode_base62(0) == "0"
    assert encode_base62(61) == "Z"      # アルファベット最後の文字
    assert encode_base62(62) == "10"     # 桁上がり


def test_base62_round_trip():
    for n in [0, 1, 61, 62, 12345, 568000000000]:
        assert decode_base62(encode_base62(n)) == n


def test_shorten_returns_distinct_codes():
    svc = ShortenerService()
    c1 = svc.shorten("https://a.example")
    c2 = svc.shorten("https://b.example")
    assert c1 != c2


def test_resolve_returns_original_url():
    svc = ShortenerService()
    code = svc.shorten("https://example.com/x")
    assert svc.resolve(code) == "https://example.com/x"


def test_resolve_unknown_returns_none():
    svc = ShortenerService()
    assert svc.resolve("nope") is None


def test_clicks_counted_on_resolve():
    svc = ShortenerService()
    code = svc.shorten("https://example.com/x")
    assert svc.clicks(code) == 0
    svc.resolve(code)
    svc.resolve(code)
    assert svc.clicks(code) == 2


def test_clicks_not_counted_for_unknown():
    svc = ShortenerService()
    svc.resolve("nope")
    assert svc.clicks("nope") == 0


def test_codes_stay_short_for_sequential_ids():
    svc = ShortenerService()
    # 連番採番なので、最初のうちのコードは1〜2文字に収まる
    codes = [svc.shorten(f"https://e/{i}") for i in range(100)]
    assert all(len(c) <= 2 for c in codes)
