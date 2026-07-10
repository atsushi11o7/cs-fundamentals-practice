"""
app.py — URL短縮サービスを、01〜04 の実装を組み合わせて API として動かす

design_method の型の「構成」「スケール対応」を、解説だけでなく実コードで示す集大成。
ドメインの核（ShortenerService）の周りに、他レイヤーの実装を配線する。

- 03 rest_api.Router     — POST /urls・GET /{code} のルーティング（API の形）
- 01 caching.SimpleCache — 解決経路の Cache-Aside（読み取り最適化）
- 04 rate_limiting.TokenBucketLimiter — 発行 API のレート制限（429）

各レイヤーはディレクトリ名が数字始まりで通常の import ができないため、
モジュールのあるディレクトリを sys.path に足してファイル名で import する。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))  # /workspace

# 他レイヤーの実装（と同ディレクトリの核）を import 可能にする
for _path in (
    _HERE,
    os.path.join(_ROOT, "01_data_layer", "caching"),
    os.path.join(_ROOT, "03_interface_layer", "rest_api_design"),
    os.path.join(_ROOT, "04_reliability_and_scale", "rate_limiting"),
):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from caching import SimpleCache                 # 01
from rate_limiting import TokenBucketLimiter    # 04
from rest_api import Router                     # 03
from url_shortener import ShortenerService      # ドメインの核


class UrlShortenerApp:
    """他レイヤーを配線した URL短縮 API。

    handle(method, path, body) にリクエストを渡すと (status, body) を返す。
    """

    def __init__(self, create_capacity=5, cache_ttl=60):
        self.service = ShortenerService()
        # 解決経路のキャッシュ（code -> long_url は不変なのでキャッシュ向き）
        self.cache = SimpleCache(ttl_seconds=cache_ttl)
        # 発行のレート制限（クライアント単位。バースト create_capacity まで）
        self.limiter = TokenBucketLimiter(capacity=create_capacity, refill_per_second=1)
        self.router = self._build_router()

    def _build_router(self):
        r = Router()
        # 管理APIは /api/ 配下に置く。リダイレクトの catch-all `/{code}` と
        # root で衝突しない（/urls を code "urls" と誤解しない）ようにするため。
        r.add("POST", "/api/urls", self._create)
        r.add("GET", "/{code}", self._redirect)
        return r

    def _create(self, params, body):
        """POST /api/urls — 元URLを登録して短縮コードを返す。"""
        body = body or {}
        client = body.get("client", "anon")
        # レート制限（04）：超過なら 429
        if not self.limiter.allow(client):
            return (429, {"error": "rate limit exceeded"})
        long_url = body.get("long_url")
        if not long_url:
            return (400, {"error": "long_url required"})
        code = self.service.shorten(long_url)
        return (201, {"code": code})

    def _redirect(self, params, body):
        """GET /{code} — 元URLへリダイレクト。Cache-Aside で読み取りを最適化。"""
        code = params["code"]
        # Cache-Aside（01）：まずキャッシュ、無ければ核から引いて載せる
        url = self.cache.get(code)
        if url is None:
            url = self.service.lookup(code)
            if url is None:
                return (404, {"error": "not found"})
            self.cache.set(code, url)
        # クリックはキャッシュヒットでも必ず数える（計測は読み取りと別経路）
        self.service.record_click(code)
        return (302, {"location": url})

    def handle(self, method, path, body=None):
        return self.router.dispatch(method, path, body)


if __name__ == "__main__":
    app = UrlShortenerApp(create_capacity=3)

    print(app.handle("POST", "/api/urls", {"long_url": "https://example.com/a"}))
    # (201, {'code': '1'})
    print(app.handle("GET", "/1"))                     # (302, {'location': 'https://example.com/a'})
    print(app.handle("GET", "/1"))                     # 再アクセス（今度はキャッシュから）
    print("clicks:", app.service.clicks("1"))          # 2（キャッシュヒットでも計測）
    print(app.handle("GET", "/999"))                   # (404, ...)

    # レート制限：4回目の発行は 429
    for _ in range(3):
        app.handle("POST", "/api/urls", {"long_url": "https://e", "client": "bob"})
    print(app.handle("POST", "/api/urls", {"long_url": "https://e", "client": "bob"}))
    # (429, {'error': 'rate limit exceeded'})
