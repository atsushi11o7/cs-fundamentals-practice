"""
aggregation.py — 集計の基本機能（標準ライブラリのみ）

「キーごとに値をまとめる」という、実装で最も頻出する処理をまとめたもの。
辞書を軸に、合計・カウント・グルーピングの3パターンを扱う。
"""
from collections import defaultdict, Counter


def sum_by_key(pairs):
    """(key, value) のペア列を受け取り、key ごとに value を合計して辞書で返す。

    例: [("a", 10), ("b", 5), ("a", 3)] -> {"a": 13, "b": 5}
    """
    totals = {}
    for key, value in pairs:
        totals[key] = totals.get(key, 0) + value
    return totals


def count_items(items):
    """要素列を受け取り、各要素の出現回数を辞書で返す。

    例: ["a", "b", "a"] -> {"a": 2, "b": 1}
    """
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def group_by_key(pairs):
    """(key, value) のペア列を受け取り、key ごとに value のリストをまとめる。

    例: [("a", 1), ("b", 2), ("a", 3)] -> {"a": [1, 3], "b": [2]}
    """
    groups = defaultdict(list)
    for key, value in pairs:
        groups[key].append(value)
    return dict(groups)


# --- 標準ライブラリを使うと短く書ける版（参考） ---

def count_items_with_counter(items):
    """count_items を collections.Counter で書いた版。中身は同じ。"""
    return dict(Counter(items))


if __name__ == "__main__":
    # 動作の確認（軽く）
    print(sum_by_key([("a", 10), ("b", 5), ("a", 3)]))   # {'a': 13, 'b': 5}
    print(count_items(["a", "b", "a"]))                   # {'a': 2, 'b': 1}
    print(group_by_key([("a", 1), ("b", 2), ("a", 3)]))   # {'a': [1, 3], 'b': [2]}
