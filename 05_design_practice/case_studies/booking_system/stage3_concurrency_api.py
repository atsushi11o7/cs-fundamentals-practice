"""
Stage 3 — 並行アクセスと API：本番に近づける

要件：同時に複数のリクエストが来る。

stage2 の book() は「重なりを確認 → 追加」の2手順だった。この途中で別リクエストが
割り込むと、両方が『空いている』と判断して**二重予約**が生まれる（レースコンディション）。
04_reliability_and_scale/concurrency で見た check-then-act の競合そのもの。

対策：確認〜追加を1つのロックで囲み、同時に1つしか通さない（SafeBookingService）。
そのうえで、外部インターフェースとして 03 のルータで API 化する（BookingApp）。
重なりで予約できない場合は 409 Conflict を返す。
"""
import os
import sys
import threading

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))

for _path in (
    _HERE,
    os.path.join(_ROOT, "02_application_layer", "interval_handling"),
    os.path.join(_ROOT, "03_interface_layer", "rest_api_design"),
):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from interval_overlap import overlaps       # 02
from rest_api import Router                 # 03
from stage2_multi_resource import Booking                  # 同じケースの stage2 のエンティティを再利用


class SafeBookingService:
    """stage2 の予約サービスに、並行安全性を足したもの。

    stage2 との違いは「book / cancel をロックで囲む」ことだけ。
    確認〜追加が一度に1スレッドしか実行できなくなり、二重予約が起きなくなる。
    """

    def __init__(self):
        self._by_resource = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def book(self, resource_id, start, end):
        with self._lock:                      # 確認〜追加を不可分にする
            for b in self._by_resource.get(resource_id, []):
                if overlaps(start, end, b.start, b.end):
                    return None
            booking = Booking(self._next_id, resource_id, start, end)
            self._next_id += 1
            self._by_resource.setdefault(resource_id, []).append(booking)
            return booking

    def cancel(self, booking_id):
        with self._lock:
            for bookings in self._by_resource.values():
                for i, b in enumerate(bookings):
                    if b.id == booking_id:
                        del bookings[i]
                        return True
            return False

    def bookings_of(self, resource_id):
        with self._lock:
            return sorted(self._by_resource.get(resource_id, []), key=lambda b: b.start)


class BookingApp:
    """SafeBookingService を 03 のルータで API 化したもの。

    POST   /bookings                    → 201 {id} / 409（重なり）/ 400
    DELETE /bookings/{id}               → 204 / 404
    GET    /resources/{id}/bookings     → 200 [{id,start,end}, ...]
    """

    def __init__(self):
        self.service = SafeBookingService()
        self.router = self._build_router()

    def _build_router(self):
        r = Router()
        r.add("POST", "/bookings", self._create)
        r.add("DELETE", "/bookings/{id}", self._cancel)
        r.add("GET", "/resources/{rid}/bookings", self._list)
        return r

    def _create(self, params, body):
        body = body or {}
        try:
            resource_id = body["resource_id"]
            start, end = body["start"], body["end"]
        except KeyError:
            return (400, {"error": "resource_id, start, end required"})
        booking = self.service.book(resource_id, start, end)
        if booking is None:
            return (409, {"error": "time slot conflict"})   # 重なり
        return (201, {"id": booking.id})

    def _cancel(self, params, body):
        if self.service.cancel(int(params["id"])):
            return (204, None)
        return (404, {"error": "not found"})

    def _list(self, params, body):
        bookings = self.service.bookings_of(params["rid"])
        return (200, [{"id": b.id, "start": b.start, "end": b.end} for b in bookings])

    def handle(self, method, path, body=None):
        return self.router.dispatch(method, path, body)


if __name__ == "__main__":
    app = BookingApp()
    print(app.handle("POST", "/bookings", {"resource_id": "roomA", "start": 10, "end": 12}))
    # (201, {'id': 1})
    print(app.handle("POST", "/bookings", {"resource_id": "roomA", "start": 11, "end": 13}))
    # (409, {'error': 'time slot conflict'})
    print(app.handle("GET", "/resources/roomA/bookings"))
    # (200, [{'id': 1, 'start': 10, 'end': 12}])
    print(app.handle("DELETE", "/bookings/1"))     # (204, None)

    # 並行に同じ枠を狙っても、ロックにより1件しか通らない
    svc = SafeBookingService()
    results = []

    def try_book():
        results.append(svc.book("roomX", 9, 10) is not None)

    threads = [threading.Thread(target=try_book) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("成功数:", sum(results))                  # 1（二重予約は起きない）
