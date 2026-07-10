"""
url_shortener.py — URL短縮サービスのドメインの核（標準ライブラリのみ）

design_method の型のうち「データ設計」と「構成（主要操作）」をコードにしたもの。
短縮コードの採番（base62）、コード↔元URLの対応、解決とクリック計測を実装する。
キャッシュ・分散・レート制限は 01/04 の実装を参照する前提で、ここでは核に集中する。
"""
import string

# base62: 0-9 a-z A-Z の62文字。数値IDを短い文字列コードに変換するのに使う。
ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(ALPHABET)


def encode_base62(n):
    """非負整数を base62 の文字列に変換する。

    連番IDを短いコードにする。桁が増えるほど表せる数が62倍になるので、
    少ない文字数で膨大なURLを識別できる（例: 6文字で約568億通り）。
    """
    if n == 0:
        return ALPHABET[0]
    chars = []
    while n > 0:
        n, remainder = divmod(n, BASE)
        chars.append(ALPHABET[remainder])
    return "".join(reversed(chars))


def decode_base62(code):
    """base62 の文字列を整数に戻す（コードからIDを復元する）。"""
    n = 0
    for ch in code:
        n = n * BASE + ALPHABET.index(ch)
    return n


class ShortenerService:
    """URL短縮のドメインサービス。

    連番IDを base62 でコード化して採番する（ハッシュではなく連番なのは、
    衝突が起きず・短く・確定的だから）。トレードオフとして連番は推測されやすいので、
    秘匿が要る用途では乱数コード＋衝突チェックにするなどの判断が要る。
    """

    def __init__(self, start_id=1):
        self._next_id = start_id
        self._url_by_code = {}       # code -> 元URL（データ設計の中心）
        self._clicks = {}            # code -> クリック数（運用監視の計測）

    def shorten(self, long_url):
        """元URLを登録し、短縮コードを返す。"""
        code = encode_base62(self._next_id)
        self._next_id += 1
        self._url_by_code[code] = long_url
        self._clicks[code] = 0
        return code

    def lookup(self, code):
        """短縮コードから元URLを返す（無ければ None）。副作用なしの純粋な読み取り。

        コード→URL の対応は不変なので、この読み取りはキャッシュに向く
        （→ 01_data_layer/caching）。app.py ではこの前段にキャッシュを挟む。
        """
        return self._url_by_code.get(code)

    def record_click(self, code):
        """コードのクリック数を1増やす（計測。キャッシュヒットでも数えたいので分離）。"""
        if code in self._clicks:
            self._clicks[code] += 1

    def resolve(self, code):
        """解決＝読み取り + クリック計測。単体で使うときの便宜メソッド。

        読み取り経路をキャッシュで最適化する app.py 側では、
        lookup（キャッシュ対象）と record_click（計測）を分けて呼ぶ。
        """
        url = self.lookup(code)
        if url is not None:
            self.record_click(code)
        return url

    def clicks(self, code):
        """コードのクリック数を返す（未知のコードは 0）。"""
        return self._clicks.get(code, 0)


if __name__ == "__main__":
    print(encode_base62(0), encode_base62(61), encode_base62(62))   # 0 Z 10

    svc = ShortenerService()
    code = svc.shorten("https://example.com/very/long/path")
    print("code:", code)                          # 1（ID=1 の base62）
    print("resolve:", svc.resolve(code))          # 元URL（クリック+1）
    svc.resolve(code)                             # もう一度アクセス
    print("clicks:", svc.clicks(code))            # 2
    print("unknown:", svc.resolve("zzzz"))        # None
