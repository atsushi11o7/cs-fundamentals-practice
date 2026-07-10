"""
searching.py — 探索の基本（標準ライブラリのみ）

線形探索と二分探索を自前で実装し、「ソート済みなら二分探索が効く」ことと、
境界を求める探索（lower_bound）の書き方を確認する。
標準ライブラリには bisect があるが、ここでは原理を理解するため自分で書く。
"""


def linear_search(seq, target):
    """先頭から順に走査し、target のインデックスを返す。無ければ -1。

    ソートされていなくても使える代わりに O(n)。
    """
    for i, value in enumerate(seq):
        if value == target:
            return i
    return -1


def binary_search(seq, target):
    """ソート済み seq に対する二分探索。target のインデックス、無ければ -1。

    探索範囲を毎回半分に狭めるので O(log n)。seq が昇順であることが前提。
    範囲は半開区間 [lo, hi) で持ち、lo == hi で「見つからず」終了する。
    """
    lo, hi = 0, len(seq)
    while lo < hi:
        mid = (lo + hi) // 2
        if seq[mid] == target:
            return mid
        if seq[mid] < target:
            lo = mid + 1          # 中央より右にしか無い
        else:
            hi = mid              # 中央より左にしか無い（mid は候補外）
    return -1


def lower_bound(seq, target):
    """ソート済み seq で「target 以上が最初に現れる位置」を返す。

    target が無くても、挿入すべき位置（insertion point）を返す。
    範囲の絞り込みで「答えの境界」を求める探索の典型形。
    - 全要素が target 未満 → len(seq) を返す
    - 重複がある場合は最も左の位置を返す
    """
    lo, hi = 0, len(seq)
    while lo < hi:
        mid = (lo + hi) // 2
        if seq[mid] < target:
            lo = mid + 1          # mid は target 未満なので候補外、右へ
        else:
            hi = mid              # mid は条件を満たしうる、左を詰める
    return lo


def contains(seq, target):
    """ソート済み seq に target が含まれるかを二分探索で判定する。"""
    return binary_search(seq, target) != -1


if __name__ == "__main__":
    data = [1, 3, 5, 7, 9, 11]
    print(linear_search(data, 7))    # 3
    print(binary_search(data, 7))    # 3
    print(binary_search(data, 8))    # -1
    print(lower_bound(data, 8))      # 4（8 を入れるなら index 4）
    print(lower_bound([1, 2, 2, 2, 3], 2))  # 1（最も左の 2）
    print(contains(data, 11))        # True
