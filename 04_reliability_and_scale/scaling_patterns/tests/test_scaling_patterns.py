"""
スケーリングパターンの動作確認。
実行： uv run pytest 04_reliability_and_scale/scaling_patterns -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scaling_patterns import ConsistentHashRing, RoundRobinBalancer, modulo_shard


def test_round_robin_cycles():
    lb = RoundRobinBalancer(["s1", "s2", "s3"])
    assert [lb.next() for _ in range(7)] == ["s1", "s2", "s3", "s1", "s2", "s3", "s1"]


def test_consistent_hash_is_deterministic():
    ring = ConsistentHashRing(["a", "b", "c"])
    # 同じキーは常に同じノードへ
    assert ring.get_node("key42") == ring.get_node("key42")


def test_empty_ring_returns_none():
    assert ConsistentHashRing([]).get_node("k") is None


def test_consistent_hash_moves_far_fewer_keys_than_modulo():
    keys = [f"key{i}" for i in range(1000)]

    # 素朴な modulo：ノード追加でほぼ全キーが動く
    before_mod = {k: modulo_shard(k, ["a", "b", "c"]) for k in keys}
    after_mod = {k: modulo_shard(k, ["a", "b", "c", "d"]) for k in keys}
    moved_mod = sum(before_mod[k] != after_mod[k] for k in keys)

    # コンシステントハッシュ：動くのは一部だけ
    ring = ConsistentHashRing(["a", "b", "c"])
    before_ring = {k: ring.get_node(k) for k in keys}
    ring.add("d")
    after_ring = {k: ring.get_node(k) for k in keys}
    moved_ring = sum(before_ring[k] != after_ring[k] for k in keys)

    assert moved_mod > 600                 # modulo は過半どころかほぼ全部
    assert moved_ring < 400                # consistent は 1/4 程度に収まる
    assert moved_ring < moved_mod


def test_remove_reassigns_only_that_nodes_keys():
    keys = [f"key{i}" for i in range(500)]
    ring = ConsistentHashRing(["a", "b", "c"])
    before = {k: ring.get_node(k) for k in keys}
    ring.remove("c")
    after = {k: ring.get_node(k) for k in keys}
    # c に載っていたキーだけが移動し、a/b のキーは動かない
    for k in keys:
        if before[k] != "c":
            assert after[k] == before[k]
    assert "c" not in set(after.values())
