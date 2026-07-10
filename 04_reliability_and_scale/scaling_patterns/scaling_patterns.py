"""
scaling_patterns.py — スケーリングの基本パターン（標準ライブラリのみ）

アクセス増に対する2つの核を、動くコードで確認する。

- ラウンドロビン負荷分散：リクエストを複数のバックエンドへ順番に振り分ける
- コンシステントハッシュ：シャーディングで、ノード増減時の再配置を最小化する

対比として素朴な「ハッシュ % ノード数」も置き、ノード追加時にほぼ全キーが
移動してしまう問題を、コンシステントハッシュがどう緩和するかを示す。
"""
import bisect
import hashlib


class RoundRobinBalancer:
    """バックエンドへ順番に振り分ける最も単純な負荷分散。"""

    def __init__(self, backends):
        self.backends = list(backends)
        self._i = 0

    def next(self):
        backend = self.backends[self._i % len(self.backends)]
        self._i += 1
        return backend


def modulo_shard(key, nodes):
    """素朴なシャーディング：hash(key) % ノード数 で割り当てる。

    単純だが、ノード数が変わると割り算の余りが総入れ替えになり、
    ほぼ全キーの割り当てが変わってしまう（キャッシュ全崩壊などの原因）。
    """
    h = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)
    return nodes[h % len(nodes)]


class ConsistentHashRing:
    """コンシステントハッシュ。ノードとキーを同じ円環上に配置する。

    キーは「円環上で自分以降にある最初のノード」に割り当てる。
    各ノードを複数の仮想ノード（replicas）として置くことで、割り当ての偏りを減らす。
    ノードを1台増減しても、影響を受けるのは円環上で隣接する範囲のキーだけなので、
    再配置がおおむね 1/ノード数 に収まる。
    """

    def __init__(self, nodes=(), replicas=100):
        self.replicas = replicas
        self._ring = {}              # ハッシュ値 -> 実ノード
        self._keys = []              # ソート済みハッシュ値（二分探索用）
        for node in nodes:
            self.add(node)

    def _hash(self, value):
        return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)

    def add(self, node):
        for i in range(self.replicas):
            h = self._hash(f"{node}#{i}")
            self._ring[h] = node
        self._keys = sorted(self._ring)

    def remove(self, node):
        for i in range(self.replicas):
            h = self._hash(f"{node}#{i}")
            self._ring.pop(h, None)
        self._keys = sorted(self._ring)

    def get_node(self, key):
        """key を担当するノードを返す。円環なので末尾を超えたら先頭へ回る。"""
        if not self._ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect(self._keys, h) % len(self._keys)
        return self._ring[self._keys[idx]]


if __name__ == "__main__":
    lb = RoundRobinBalancer(["s1", "s2", "s3"])
    print([lb.next() for _ in range(5)])   # s1 s2 s3 s1 s2

    # ノード追加でどれだけキーが動くか：素朴 modulo vs コンシステントハッシュ
    keys = [f"key{i}" for i in range(1000)]

    before_mod = {k: modulo_shard(k, ["a", "b", "c"]) for k in keys}
    after_mod = {k: modulo_shard(k, ["a", "b", "c", "d"]) for k in keys}
    moved_mod = sum(before_mod[k] != after_mod[k] for k in keys)

    ring = ConsistentHashRing(["a", "b", "c"])
    before_ring = {k: ring.get_node(k) for k in keys}
    ring.add("d")
    after_ring = {k: ring.get_node(k) for k in keys}
    moved_ring = sum(before_ring[k] != after_ring[k] for k in keys)

    print(f"modulo で移動: {moved_mod}/1000")          # ほぼ全部（~750）
    print(f"consistent で移動: {moved_ring}/1000")     # わずか（~250 以下）
