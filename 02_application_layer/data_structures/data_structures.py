"""
data_structures.py — 基本データ構造の使い分け（標準ライブラリのみ）

辞書・リスト・集合・両端キュー（deque）を、それぞれが得意な場面で使う小さな例。
「どれを選ぶか」の判断を、動くコードで確かめる。
"""
from collections import deque


def has_duplicates(items):
    """重複が含まれるかを集合で判定する（O(n)）。

    リストで「今までに見たか」を毎回 in で調べると O(n^2) になる。
    集合はメンバー判定が平均 O(1) なので、全体を O(n) に保てる。
    """
    seen = set()
    for item in items:
        if item in seen:
            return True
        seen.add(item)
    return False


def dedupe_preserve_order(items):
    """重複を除きつつ、初出の順序を保って返す。

    順序を保つのはリスト、重複判定は集合、と役割で使い分けるのがポイント。
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


class Stack:
    """LIFO（後入れ先出し）。リスト末尾への append/pop はどちらも O(1)。"""

    def __init__(self):
        self._items = []

    def push(self, x):
        self._items.append(x)

    def pop(self):
        # 空なら IndexError（呼び出し側で空チェックする前提）
        return self._items.pop()

    def peek(self):
        return self._items[-1]

    def __len__(self):
        return len(self._items)


class Queue:
    """FIFO（先入れ先出し）。deque なら両端の操作が O(1)。

    list で先頭を pop(0) すると、以降の要素をずらすため O(n) になる。
    キューには deque を使うのが定石。
    """

    def __init__(self):
        self._items = deque()

    def enqueue(self, x):
        self._items.append(x)

    def dequeue(self):
        return self._items.popleft()

    def __len__(self):
        return len(self._items)


if __name__ == "__main__":
    print(has_duplicates([1, 2, 3, 2]))            # True
    print(has_duplicates([1, 2, 3]))               # False
    print(dedupe_preserve_order([3, 1, 3, 2, 1]))  # [3, 1, 2]

    s = Stack()
    s.push(1); s.push(2)
    print(s.pop(), s.pop())                        # 2 1（後入れ先出し）

    q = Queue()
    q.enqueue("a"); q.enqueue("b")
    print(q.dequeue(), q.dequeue())                # a b（先入れ先出し）
