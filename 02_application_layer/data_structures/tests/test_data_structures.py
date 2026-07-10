"""
データ構造の使い分けの動作確認。
実行： uv run pytest 02_application_layer/data_structures -v
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_structures import Queue, Stack, dedupe_preserve_order, has_duplicates


def test_has_duplicates_true():
    assert has_duplicates([1, 2, 3, 2]) is True


def test_has_duplicates_false():
    assert has_duplicates([1, 2, 3]) is False


def test_has_duplicates_empty():
    assert has_duplicates([]) is False


def test_dedupe_preserves_first_seen_order():
    assert dedupe_preserve_order([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_dedupe_no_duplicates():
    assert dedupe_preserve_order([1, 2, 3]) == [1, 2, 3]


def test_stack_is_lifo():
    s = Stack()
    s.push(1)
    s.push(2)
    s.push(3)
    assert len(s) == 3
    assert s.peek() == 3
    assert s.pop() == 3
    assert s.pop() == 2
    assert s.pop() == 1
    assert len(s) == 0


def test_stack_pop_empty_raises():
    with pytest.raises(IndexError):
        Stack().pop()


def test_queue_is_fifo():
    q = Queue()
    q.enqueue("a")
    q.enqueue("b")
    q.enqueue("c")
    assert q.dequeue() == "a"
    assert q.dequeue() == "b"
    assert q.dequeue() == "c"
    assert len(q) == 0
