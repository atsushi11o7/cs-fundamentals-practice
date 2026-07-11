"""
予約システム stage3（並行安全 + API）の動作確認。
実行： uv run pytest 05_design_practice/case_studies/booking_system -v
"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage3_concurrency_api import BookingApp, SafeBookingService


def test_create_returns_201():
    app = BookingApp()
    status, body = app.handle(
        "POST", "/bookings", {"resource_id": "roomA", "start": 10, "end": 12}
    )
    assert status == 201
    assert "id" in body


def test_overlap_returns_409():
    app = BookingApp()
    app.handle("POST", "/bookings", {"resource_id": "roomA", "start": 10, "end": 12})
    status, _ = app.handle(
        "POST", "/bookings", {"resource_id": "roomA", "start": 11, "end": 13}
    )
    assert status == 409


def test_missing_fields_returns_400():
    app = BookingApp()
    assert app.handle("POST", "/bookings", {"resource_id": "roomA"})[0] == 400


def test_cancel_returns_204_then_404():
    app = BookingApp()
    _, body = app.handle(
        "POST", "/bookings", {"resource_id": "roomA", "start": 10, "end": 12}
    )
    assert app.handle("DELETE", "/bookings/" + str(body["id"]))[0] == 204
    assert app.handle("DELETE", "/bookings/" + str(body["id"]))[0] == 404


def test_list_bookings():
    app = BookingApp()
    app.handle("POST", "/bookings", {"resource_id": "roomA", "start": 14, "end": 16})
    app.handle("POST", "/bookings", {"resource_id": "roomA", "start": 10, "end": 12})
    status, bookings = app.handle("GET", "/resources/roomA/bookings")
    assert status == 200
    # 開始時刻順に並ぶ（14-16 を先に入れても 10, 14 の順）
    assert [b["start"] for b in bookings] == [10, 14]


def test_concurrent_booking_lets_exactly_one_win():
    # 20スレッドが同じ枠を同時に狙っても、ロックにより成功は1件だけ
    svc = SafeBookingService()
    results = []

    def try_book():
        results.append(svc.book("roomX", 9, 10) is not None)

    threads = [threading.Thread(target=try_book) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(results) == 1
    assert len(svc.bookings_of("roomX")) == 1     # 二重予約は生まれていない
