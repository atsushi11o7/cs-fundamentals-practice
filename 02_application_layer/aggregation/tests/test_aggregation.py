"""
集計機能の動作確認。
実行： uv run pytest 02_application_layer/aggregation -v
"""
import os
import sys

# 親フォルダの aggregation.py を import できるようにする
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aggregation import (
    sum_by_key,
    count_items,
    group_by_key,
    count_items_with_counter,
)


def test_sum_by_key():
    assert sum_by_key([("a", 10), ("b", 5), ("a", 3)]) == {"a": 13, "b": 5}


def test_sum_by_key_empty():
    assert sum_by_key([]) == {}


def test_count_items():
    assert count_items(["a", "b", "a"]) == {"a": 2, "b": 1}


def test_count_items_matches_counter_version():
    items = ["x", "y", "x", "z", "x"]
    assert count_items(items) == count_items_with_counter(items)


def test_group_by_key():
    assert group_by_key([("a", 1), ("b", 2), ("a", 3)]) == {"a": [1, 3], "b": [2]}


def test_group_by_key_preserves_order():
    # 同じキー内の値は登場順を保つ
    assert group_by_key([("a", 3), ("a", 1), ("a", 2)]) == {"a": [3, 1, 2]}
