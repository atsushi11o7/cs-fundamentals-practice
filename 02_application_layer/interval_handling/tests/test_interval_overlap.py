"""
区間重なり判定の動作確認。
実行： uv run pytest 02_application_layer/interval_handling -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interval_overlap import overlaps, has_any_overlap, BookingManager


def test_overlaps_true():
    assert overlaps(10, 12, 11, 13) is True


def test_overlaps_boundary_touch_is_false():
    assert overlaps(10, 12, 12, 14) is False


def test_overlaps_completely_separate():
    assert overlaps(10, 12, 20, 22) is False


def test_has_any_overlap_true():
    assert has_any_overlap([(10, 12), (12, 14), (11, 13)]) is True


def test_has_any_overlap_false():
    assert has_any_overlap([(10, 12), (12, 14), (14, 16)]) is False


def test_has_any_overlap_empty():
    assert has_any_overlap([]) is False


def test_booking_manager():
    m = BookingManager()
    assert m.book(10, 12) is True
    assert m.book(11, 13) is False    # 重なる
    assert m.book(12, 14) is True     # 境界接触OK
