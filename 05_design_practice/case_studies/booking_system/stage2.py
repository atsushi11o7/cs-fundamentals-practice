"""
Stage 2 — 複数リソースとデータモデル：要件が広がる

要件が増える：
- 会議室は複数ある。予約は「どの部屋か」を持ち、重なり判定は同じ部屋の中だけで行う。
- 予約をキャンセルできる。
- 部屋ごとの予約一覧が欲しい。

stage1 の「(start, end) のタプルのリスト」では、もう足りない。
「どの部屋の・どの予約か」を識別する必要が出たので、ここでデータモデルを起こす。

- Booking：id・resource_id・start・end を持つエンティティ
- 部屋（resource_id）ごとに予約を引けるよう、resource_id をキーに持つ

id を振るのは、後でキャンセルや参照のとき「その1件」を一意に指すため（→ 主キーの発想）。
"""
import os
import sys
from dataclasses import dataclass

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_ROOT, "02_application_layer", "interval_handling"))

from interval_overlap import overlaps


@dataclass
class Booking:
    id: int
    resource_id: str
    start: int
    end: int


class BookingService:
    """複数リソースの予約。重なり判定は同じ resource_id の中だけ。"""

    def __init__(self):
        self._by_resource = {}           # resource_id -> [Booking]
        self._next_id = 1

    def book(self, resource_id, start, end):
        """予約を試みる。成功で Booking、同じ部屋の既存と重なれば None。"""
        for b in self._by_resource.get(resource_id, []):
            if overlaps(start, end, b.start, b.end):
                return None
        booking = Booking(self._next_id, resource_id, start, end)
        self._next_id += 1
        self._by_resource.setdefault(resource_id, []).append(booking)
        return booking

    def cancel(self, booking_id):
        """予約を取り消す。取り消せたら True、該当が無ければ False。"""
        for bookings in self._by_resource.values():
            for i, b in enumerate(bookings):
                if b.id == booking_id:
                    del bookings[i]
                    return True
        return False

    def bookings_of(self, resource_id):
        """部屋の予約を開始時刻順で返す。"""
        return sorted(self._by_resource.get(resource_id, []), key=lambda b: b.start)


if __name__ == "__main__":
    svc = BookingService()
    a = svc.book("roomA", 10, 12)
    print(a)                                   # Booking(id=1, resource_id='roomA', ...)
    print(svc.book("roomA", 11, 13))           # None（roomA で重なる）
    print(svc.book("roomB", 11, 13).id)        # 2（別の部屋なので OK）

    svc.cancel(a.id)                            # roomA 10-12 を取り消す
    print(svc.book("roomA", 11, 13).id)        # 3（空いたので予約できる）
    print([b.id for b in svc.bookings_of("roomA")])   # [3]
