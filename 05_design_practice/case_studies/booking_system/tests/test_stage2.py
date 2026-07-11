"""
予約システム stage2 の動作確認。
実行： uv run pytest 05_design_practice/case_studies/booking_system -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage2 import BookingService


def test_book_returns_booking_with_id():
    svc = BookingService()
    b = svc.book("roomA", 10, 12)
    assert b.id == 1
    assert b.resource_id == "roomA"


def test_overlap_only_within_same_resource():
    svc = BookingService()
    svc.book("roomA", 10, 12)
    # 同じ部屋の重なりは拒否
    assert svc.book("roomA", 11, 13) is None
    # 別の部屋は同じ時間でも OK
    assert svc.book("roomB", 11, 13) is not None


def test_cancel_frees_the_slot():
    svc = BookingService()
    a = svc.book("roomA", 10, 12)
    assert svc.book("roomA", 11, 13) is None    # まだ埋まっている
    assert svc.cancel(a.id) is True
    assert svc.book("roomA", 11, 13) is not None  # 空いたので予約できる


def test_cancel_unknown_returns_false():
    svc = BookingService()
    assert svc.cancel(999) is False


def test_bookings_of_is_sorted():
    svc = BookingService()
    svc.book("roomA", 14, 16)
    svc.book("roomA", 10, 12)
    assert [b.start for b in svc.bookings_of("roomA")] == [10, 14]


def test_bookings_of_empty_resource():
    svc = BookingService()
    assert svc.bookings_of("nope") == []
