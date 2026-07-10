"""
graph_traversal.py — グラフ/木の探索（標準ライブラリのみ）

グラフを隣接リスト（dict: ノード -> 隣接ノードのリスト）で表し、
幅優先探索（BFS）と深さ優先探索（DFS）を実装する。
「未訪問集合で無限ループを防ぐ」「BFS は最短ホップ数を求められる」が要点。

例として友人関係のグラフ（無向）を扱う。木はグラフの特殊形なので、同じコードで扱える。
"""
from collections import deque


def build_undirected(edges):
    """辺のリスト [(a, b), ...] から無向グラフ（隣接リスト）を作る。

    無向なので a->b と b->a の両方向を登録する。
    """
    graph = {}
    for a, b in edges:
        graph.setdefault(a, [])
        graph.setdefault(b, [])
        graph[a].append(b)
        graph[b].append(a)
    return graph


def bfs(graph, start):
    """start から幅優先で訪問し、訪問順のリストを返す。

    キュー（deque）で「近いノードから順に」広げる。
    visited で二度訪問を防ぐ（登録はキュー投入時。同じノードの重複投入を避ける）。
    """
    visited = {start}
    order = []
    queue = deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in graph.get(node, []):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return order


def dfs(graph, start):
    """start から深さ優先で訪問し、訪問順のリストを返す（再帰）。

    再帰で「行けるところまで潜ってから戻る」。visited で循環を止める。
    """
    visited = set()
    order = []

    def visit(node):
        visited.add(node)
        order.append(node)
        for nxt in graph.get(node, []):
            if nxt not in visited:
                visit(nxt)

    visit(start)
    return order


def shortest_hops(graph, start, goal):
    """start から goal までの最短ホップ数を BFS で求める。到達不能なら None。

    重みなしグラフでは、BFS が最短経路（最少辺数）を与える。
    start == goal は 0。SNS の「何人たどれば繋がるか」がこれ。
    """
    if start == goal:
        return 0
    visited = {start}
    queue = deque([(start, 0)])
    while queue:
        node, dist = queue.popleft()
        for nxt in graph.get(node, []):
            if nxt == goal:
                return dist + 1
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, dist + 1))
    return None


def connected_component(graph, start):
    """start から到達できるノードの集合を返す（連結成分）。"""
    return set(bfs(graph, start))


if __name__ == "__main__":
    #   a - b - d
    #   |   |
    #   c   e
    g = build_undirected([("a", "b"), ("a", "c"), ("b", "d"), ("b", "e")])
    print("BFS:", bfs(g, "a"))              # a, b, c, d, e（近い順）
    print("DFS:", dfs(g, "a"))              # a, b, d, e, c（潜ってから戻る）
    print("a→e ホップ:", shortest_hops(g, "a", "e"))   # 2
    print("a→x ホップ:", shortest_hops(g, "a", "x"))   # None（未登録＝到達不能）
    print("連結成分:", connected_component(g, "a"))     # {a, b, c, d, e}
