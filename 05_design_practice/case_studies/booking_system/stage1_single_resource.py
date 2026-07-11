"""
Stage 1 — 単一リソースの予約：まず一番単純な形

最初に立てる要件は最小限にする。
「1つのリソース（例：会議室）に、時間帯 [start, end) の予約を受け付ける。
 既存の予約と重なるなら断る。」まずこれだけを、一番単純に作る。

守りたい不変条件は「重なる予約を同時に持たない」こと。
重なり判定は 02_application_layer/interval_handling で作った overlaps を再利用する
（同じ考え方を作り直さない）。

この段階の割り切り：
- リソースは1つだけ（複数リソースは stage2 で）
- 単一スレッド前提（並行アクセスは stage3 で）
- 予約は (start, end) のタプルをリストに持つだけ
"""
import os
import sys

# 02 の interval_handling を import できるようにする
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_ROOT, "02_application_layer", "interval_handling"))

from interval_overlap import overlaps


class RoomCalendar:
    """1つのリソースの予約表。重ならなければ登録、重なれば拒否。"""

    def __init__(self):
        self._bookings = []              # [(start, end), ...]

    def book(self, start, end):
        """予約を試みる。成功で True、既存と重なれば False。

        既存すべてと重なりを見るので O(N)。予約が少ないうちはこれで十分。
        """
        for s, e in self._bookings:
            if overlaps(start, end, s, e):
                return False
        self._bookings.append((start, end))
        return True

    def bookings(self):
        """登録済みの予約を開始時刻順で返す。"""
        return sorted(self._bookings)


if __name__ == "__main__":
    cal = RoomCalendar()
    print(cal.book(10, 12))   # True
    print(cal.book(11, 13))   # False（10-12 と重なる）
    print(cal.book(12, 14))   # True（境界が接するだけは重ならない扱い）
    print(cal.bookings())     # [(10, 12), (12, 14)]
