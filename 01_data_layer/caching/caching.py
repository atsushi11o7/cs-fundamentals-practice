"""
caching.py — キャッシュの最小実装（標準ライブラリのみ）

Cache-Aside（Lazy Loading）パターンと、TTL・無効化の考え方を
動く最小コードで示す。外部のRedis等は使わず、辞書でキャッシュを模す。
"""
import time


class SimpleCache:
    """TTL付きの最小キャッシュ。値と「保存時刻」を持つ。"""

    def __init__(self, ttl_seconds):
        self.ttl = ttl_seconds
        self.store = {}                  # key -> (value, saved_at)

    def get(self, key):
        """キャッシュから取得。無い or 期限切れなら None。"""
        entry = self.store.get(key)
        if entry is None:
            return None
        value, saved_at = entry
        if time.time() - saved_at > self.ttl:
            # 期限切れ：捨てて None を返す
            del self.store[key]
            return None
        return value

    def set(self, key, value):
        self.store[key] = (value, time.time())

    def invalidate(self, key):
        """明示的な無効化。元データを更新したら対応するキーを消す。"""
        self.store.pop(key, None)


class UserRepository:
    """Cache-Aside パターンの実例。

    読み取りはまずキャッシュを見て、無ければ「DB」から取り、キャッシュに保存する。
    更新時はキャッシュを無効化して、次回の読み取りで最新を取り直させる。
    """

    def __init__(self, cache):
        self.cache = cache
        self.db = {}                     # 本来はDB。ここでは辞書で代用
        self.db_read_count = 0           # DBアクセス回数（キャッシュ効果の確認用）

    def _db_get(self, user_id):
        self.db_read_count += 1
        return self.db.get(user_id)

    def get_user(self, user_id):
        # 1. まずキャッシュを見る
        cached = self.cache.get(user_id)
        if cached is not None:
            return cached
        # 2. 無ければDBから取る
        value = self._db_get(user_id)
        # 3. 取れたらキャッシュに保存して次回に備える
        if value is not None:
            self.cache.set(user_id, value)
        return value

    def update_user(self, user_id, value):
        self.db[user_id] = value
        # 更新したらキャッシュを無効化（古い値が残らないように）
        self.cache.invalidate(user_id)


if __name__ == "__main__":
    repo = UserRepository(SimpleCache(ttl_seconds=60))
    repo.db["u1"] = "Alice"

    print(repo.get_user("u1"))       # Alice（DBから、db_read_count=1）
    print(repo.get_user("u1"))       # Alice（キャッシュから、db_read_countは増えない）
    print("DB reads:", repo.db_read_count)  # 1

    repo.update_user("u1", "Alice2")  # 更新→キャッシュ無効化
    print(repo.get_user("u1"))       # Alice2（DBから取り直し、db_read_count=2）
    print("DB reads:", repo.db_read_count)  # 2
