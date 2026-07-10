"""
探索の動作確認。
実行： uv run pytest 02_application_layer/searching -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from searching import binary_search, contains, linear_search, lower_bound


def test_linear_search_found():
    assert linear_search([4, 2, 7, 1], 7) == 2


def test_linear_search_not_found():
    assert linear_search([4, 2, 7, 1], 9) == -1


def test_linear_search_empty():
    assert linear_search([], 1) == -1


def test_binary_search_found():
    data = [1, 3, 5, 7, 9, 11]
    assert binary_search(data, 7) == 3
    assert binary_search(data, 1) == 0
    assert binary_search(data, 11) == 5


def test_binary_search_not_found():
    assert binary_search([1, 3, 5, 7, 9, 11], 8) == -1
    assert binary_search([], 1) == -1


def test_binary_search_matches_linear_on_sorted():
    data = list(range(0, 100, 2))          # 偶数のみ
    for t in range(0, 100):
        expected = linear_search(data, t)
        assert binary_search(data, t) == expected


def test_lower_bound_insertion_point():
    data = [1, 3, 5, 7, 9, 11]
    assert lower_bound(data, 8) == 4        # 8 を入れるなら index 4
    assert lower_bound(data, 0) == 0        # 全要素より小 → 先頭
    assert lower_bound(data, 100) == 6      # 全要素より大 → 末尾(len)


def test_lower_bound_leftmost_on_duplicates():
    assert lower_bound([1, 2, 2, 2, 3], 2) == 1


def test_contains():
    data = [1, 3, 5, 7, 9, 11]
    assert contains(data, 5) is True
    assert contains(data, 6) is False
