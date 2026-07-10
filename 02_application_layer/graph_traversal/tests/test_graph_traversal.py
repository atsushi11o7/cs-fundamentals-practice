"""
グラフ探索の動作確認。
実行： uv run pytest 02_application_layer/graph_traversal -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_traversal import (
    bfs,
    build_undirected,
    connected_component,
    dfs,
    shortest_hops,
)


def sample_graph():
    #   a - b - d
    #   |   |
    #   c   e
    return build_undirected([("a", "b"), ("a", "c"), ("b", "d"), ("b", "e")])


def test_build_undirected_is_bidirectional():
    g = build_undirected([("a", "b")])
    assert "b" in g["a"]
    assert "a" in g["b"]


def test_bfs_visits_nearest_first():
    g = sample_graph()
    # 隣接の登録順に探索するので順序は決定的
    assert bfs(g, "a") == ["a", "b", "c", "d", "e"]


def test_dfs_goes_deep_first():
    g = sample_graph()
    assert dfs(g, "a") == ["a", "b", "d", "e", "c"]


def test_bfs_and_dfs_visit_same_set():
    g = sample_graph()
    assert set(bfs(g, "a")) == set(dfs(g, "a"))


def test_shortest_hops():
    g = sample_graph()
    assert shortest_hops(g, "a", "a") == 0
    assert shortest_hops(g, "a", "b") == 1
    assert shortest_hops(g, "a", "e") == 2      # a -> b -> e
    assert shortest_hops(g, "c", "e") == 3      # c -> a -> b -> e


def test_shortest_hops_unreachable():
    g = sample_graph()
    assert shortest_hops(g, "a", "zzz") is None


def test_cycle_does_not_loop_forever():
    # 三角形（循環あり）。visited が無いと無限ループする
    g = build_undirected([("a", "b"), ("b", "c"), ("c", "a")])
    assert set(bfs(g, "a")) == {"a", "b", "c"}
    assert set(dfs(g, "a")) == {"a", "b", "c"}


def test_connected_component():
    g = sample_graph()
    assert connected_component(g, "a") == {"a", "b", "c", "d", "e"}
