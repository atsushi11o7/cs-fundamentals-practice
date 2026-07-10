"""
sorting.py — ソートの基本機能（標準ライブラリのみ）

実装で頻出する「複合キーでの並べ替え」を中心に、
sorted と key の使い方をまとめたもの。
"""


def sort_by_value_desc(d):
    """辞書を value の降順で並べ、(key, value) のリストで返す。

    例: {"a": 3, "b": 1, "c": 3} -> [("a", 3), ("c", 3), ("b", 1)]
    （同値の場合は key の昇順で安定させる）
    """
    return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))


def rank(records):
    """(name, score) のリストを集計し、score 降順・name 昇順で並べて返す。

    集計とソートの組み合わせ（実務頻出パターン）。
    例: [("a", 5), ("b", 3), ("a", 2)] -> [("a", 7), ("b", 3)]
    """
    totals = {}
    for name, score in records:
        totals[name] = totals.get(name, 0) + score
    return sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))


def sort_by_multiple_keys(rows, keys):
    """辞書のリストを、複数キーで並べ替える。

    keys は (フィールド名, 降順か) のタプルのリスト。
    例: sort_by_multiple_keys(rows, [("age", True), ("name", False)])
        → age 降順、同値なら name 昇順
    """
    def sort_key(row):
        result = []
        for field, descending in keys:
            value = row[field]
            # 数値なら降順は符号反転で表現。文字列はここでは昇順のみ想定。
            if descending and isinstance(value, (int, float)):
                result.append(-value)
            else:
                result.append(value)
        return tuple(result)
    return sorted(rows, key=sort_key)


if __name__ == "__main__":
    print(sort_by_value_desc({"a": 3, "b": 1, "c": 3}))
    # [('a', 3), ('c', 3), ('b', 1)]
    print(rank([("a", 5), ("b", 3), ("a", 2)]))
    # [('a', 7), ('b', 3)]
    rows = [{"name": "x", "age": 30}, {"name": "y", "age": 30}, {"name": "z", "age": 25}]
    print(sort_by_multiple_keys(rows, [("age", True), ("name", False)]))
    # age降順→30の2人が先、その中でname昇順(x,y)、最後にz
