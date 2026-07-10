"""
レート制限の動作確認。
実行： uv run pytest 04_reliability_and_scale/rate_limiting -v
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate_limiting import FixedWindowLimiter, TokenBucketLimiter


def test_fixed_window_blocks_over_limit():
    fw = FixedWindowLimiter(limit=3, window_seconds=10)
    results = [fw.allow("user") for _ in range(5)]
    assert results == [True, True, True, False, False]


def test_fixed_window_resets_after_window():
    fw = FixedWindowLimiter(limit=1, window_seconds=0.05)
    assert fw.allow("user") is True
    assert fw.allow("user") is False
    time.sleep(0.1)
    assert fw.allow("user") is True     # 新しいウィンドウで復活


def test_fixed_window_per_key():
    fw = FixedWindowLimiter(limit=1, window_seconds=10)
    assert fw.allow("a") is True
    assert fw.allow("b") is True         # キーが違えば独立
    assert fw.allow("a") is False


def test_token_bucket_initial_burst():
    tb = TokenBucketLimiter(capacity=3, refill_per_second=1)
    results = [tb.allow("user") for _ in range(5)]
    assert results == [True, True, True, False, False]


def test_token_bucket_refills_over_time():
    tb = TokenBucketLimiter(capacity=1, refill_per_second=100)
    assert tb.allow("user") is True
    assert tb.allow("user") is False
    time.sleep(0.05)                     # 補充を待つ
    assert tb.allow("user") is True
