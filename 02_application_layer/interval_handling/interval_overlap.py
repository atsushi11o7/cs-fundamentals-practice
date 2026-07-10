"""
interval_overlap.py — 区間の重なり判定（標準ライブラリのみ）

予約・スケジュール・範囲チェックなどで頻出する「区間が重なるか」の判定と、
それを使った予約管理の最小実装。
"""


def overlaps(s1, e1, s2, e2):
    """区間 [s1, e1) と [s2, e2) が重なるかを返す。

    境界が接するだけ（e1 == s2 など）は「重ならない」扱い。
    重ならない条件は「片方が完全に前」or「完全に後」。その否定が重なり。
    """
    return not (e1 <= s2 or e2 <= s1)


def has_any_overlap(intervals):
    """区間のリスト [(s, e), ...] の中に、重なるペアが1つでもあるか。

    ソートしてから隣接だけ見ることで O(N log N) で判定する。
    """
    ordered = sorted(intervals)          # 開始時刻でソート
    for i in range(1, len(ordered)):
        prev_s, prev_e = ordered[i - 1]
        cur_s, cur_e = ordered[i]
        # ソート済みなので、隣が重なるかだけ見ればよい
        if cur_s < prev_e:
            return True
    return False


class BookingManager:
    """予約管理の最小実装。重ならなければ登録、重なれば拒否。"""

    def __init__(self):
        self.bookings = []               # 登録済みの (start, end)

    def book(self, start, end):
        """予約を試みる。成功で True、既存と重なれば False。"""
        for s, e in self.bookings:
            if overlaps(start, end, s, e):
                return False
        self.bookings.append((start, end))
        return True


if __name__ == "__main__":
    print(overlaps(10, 12, 11, 13))   # True（重なる）
    print(overlaps(10, 12, 12, 14))   # False（境界接触）
    print(has_any_overlap([(10, 12), (12, 14), (11, 13)]))  # True

    m = BookingManager()
    print(m.book(10, 12))   # True
    print(m.book(11, 13))   # False（10-12と重なる）
    print(m.book(12, 14))   # True（境界接触はOK）
