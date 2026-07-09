"""
キャッシュの動作確認。
実行： uv run pytest 01_data_layer/caching -v
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from caching import SimpleCache, UserRepository


def test_cache_hit_avoids_db():
    repo = UserRepository(SimpleCache(ttl_seconds=60))
    repo.db["u1"] = "Alice"

    assert repo.get_user("u1") == "Alice"   # ミス→DB
    assert repo.get_user("u1") == "Alice"   # ヒット→DBに行かない
    assert repo.db_read_count == 1          # DBアクセスは1回だけ


def test_update_invalidates_cache():
    repo = UserRepository(SimpleCache(ttl_seconds=60))
    repo.db["u1"] = "Alice"

    repo.get_user("u1")                     # キャッシュに載る
    repo.update_user("u1", "Alice2")        # 更新→無効化
    assert repo.get_user("u1") == "Alice2"  # 最新が返る
    assert repo.db_read_count == 2          # 取り直しでDB再アクセス


def test_ttl_expiry():
    cache = SimpleCache(ttl_seconds=0.05)
    cache.set("k", "v")
    assert cache.get("k") == "v"            # 期限内
    time.sleep(0.1)
    assert cache.get("k") is None           # 期限切れ


def test_missing_key_returns_none():
    cache = SimpleCache(ttl_seconds=60)
    assert cache.get("nope") is None
