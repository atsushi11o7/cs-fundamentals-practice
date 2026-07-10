"""
ソート機能の動作確認。
実行： uv run pytest 02_application_layer/sorting -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sorting import sort_by_value_desc, rank, sort_by_multiple_keys


def test_sort_by_value_desc():
    assert sort_by_value_desc({"a": 3, "b": 1, "c": 3}) == [("a", 3), ("c", 3), ("b", 1)]


def test_sort_by_value_desc_empty():
    assert sort_by_value_desc({}) == []


def test_rank_aggregates_and_sorts():
    assert rank([("a", 5), ("b", 3), ("a", 2)]) == [("a", 7), ("b", 3)]


def test_rank_tie_breaks_by_name():
    assert rank([("charlie", 10), ("alice", 10)]) == [("alice", 10), ("charlie", 10)]


def test_sort_by_multiple_keys():
    rows = [
        {"name": "x", "age": 30},
        {"name": "y", "age": 30},
        {"name": "z", "age": 25},
    ]
    result = sort_by_multiple_keys(rows, [("age", True), ("name", False)])
    assert [r["name"] for r in result] == ["x", "y", "z"]
