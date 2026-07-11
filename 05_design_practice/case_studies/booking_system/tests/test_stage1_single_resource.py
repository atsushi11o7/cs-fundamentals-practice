"""
予約システム stage1 の動作確認。
実行： uv run pytest 05_design_practice/case_studies/booking_system -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage1_single_resource import RoomCalendar


def test_first_booking_succeeds():
    cal = RoomCalendar()
    assert cal.book(10, 12) is True


def test_overlapping_booking_rejected():
    cal = RoomCalendar()
    cal.book(10, 12)
    assert cal.book(11, 13) is False


def test_boundary_touch_is_allowed():
    cal = RoomCalendar()
    cal.book(10, 12)
    assert cal.book(12, 14) is True        # 接触は重ならない


def test_bookings_sorted():
    cal = RoomCalendar()
    cal.book(12, 14)
    cal.book(10, 12)
    assert cal.bookings() == [(10, 12), (12, 14)]
