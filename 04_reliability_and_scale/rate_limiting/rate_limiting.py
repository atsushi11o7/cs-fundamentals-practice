"""
rate_limiting.py — レート制限の最小実装（標準ライブラリのみ）

代表的な2方式を実装する：
- 固定ウィンドウ（Fixed Window）：単純だが境界で2倍来る問題がある
- トークンバケット（Token Bucket）：実務で最もよく使われる。バーストを許容しつつ平均を制限
"""
import time


class FixedWindowLimiter:
    """固定ウィンドウ方式。window_seconds ごとにカウントをリセット。"""

    def __init__(self, limit, window_seconds):
        self.limit = limit
        self.window = window_seconds
        self.counters = {}               # key -> (window_start, count)

    def allow(self, key):
        """key のリクエストを許可するなら True、制限超過なら False。"""
        now = time.time()
        window_start, count = self.counters.get(key, (now, 0))

        if now - window_start >= self.window:
            # 新しいウィンドウに入った：リセット
            window_start, count = now, 0

        if count < self.limit:
            self.counters[key] = (window_start, count + 1)
            return True
        self.counters[key] = (window_start, count)
        return False


class TokenBucketLimiter:
    """トークンバケット方式。

    一定速度でトークンが補充され、リクエストごとに1つ消費する。
    トークンがあれば許可、なければ拒否。短時間のバースト（貯めたトークン分）を許容できる。
    """

    def __init__(self, capacity, refill_per_second):
        self.capacity = capacity             # バケットの最大トークン数
        self.refill = refill_per_second      # 1秒あたりの補充量
        self.buckets = {}                    # key -> (tokens, last_time)

    def allow(self, key):
        now = time.time()
        tokens, last = self.buckets.get(key, (self.capacity, now))

        # 経過時間ぶんトークンを補充（上限は capacity）
        tokens = min(self.capacity, tokens + (now - last) * self.refill)

        if tokens >= 1:
            self.buckets[key] = (tokens - 1, now)
            return True
        self.buckets[key] = (tokens, now)
        return False


if __name__ == "__main__":
    # 固定ウィンドウ：1秒に3回まで
    fw = FixedWindowLimiter(limit=3, window_seconds=1)
    print([fw.allow("user") for _ in range(5)])
    # [True, True, True, False, False]

    # トークンバケット：最大3、毎秒1補充
    tb = TokenBucketLimiter(capacity=3, refill_per_second=1)
    print([tb.allow("user") for _ in range(5)])
    # [True, True, True, False, False]（初期3トークンを使い切る）
