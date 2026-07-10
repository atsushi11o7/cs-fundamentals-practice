"""
並行処理の動作確認。
実行： uv run pytest 04_reliability_and_scale/concurrency -v

注意：UnsafeCounter の競合は環境・タイミング依存で必ずしも再現しない。
      そのため「壊れること」はテストせず、「SafeCounter は常に正しい」ことを検証する。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concurrency import SafeCounter, UnsafeCounter, run_with_threads


def test_safe_counter_is_always_correct():
    expected = 4 * 10000
    result = run_with_threads(SafeCounter(), num_threads=4, times_each=10000)
    assert result == expected


def test_safe_counter_single_thread():
    result = run_with_threads(SafeCounter(), num_threads=1, times_each=1000)
    assert result == 1000


def test_unsafe_counter_never_exceeds_expected():
    # unsafe は「小さくなる」ことはあっても「増えすぎる」ことはない。
    # 競合の有無に関わらず成立する不変条件だけを検証する。
    expected = 4 * 10000
    result = run_with_threads(UnsafeCounter(), num_threads=4, times_each=10000)
    assert result <= expected
