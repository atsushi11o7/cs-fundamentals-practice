"""
web_performance.py — Webパフォーマンスのサーバ側の核（標準ライブラリのみ）

パフォーマンス改善の多くはフロント側（画像・遅延読み込み等）だが、サーバ側にも
コードで実装できる定番がある。ここでは2つを扱う。

- 条件付きリクエスト（ETag → 304 Not Modified）：内容が変わっていなければ本文を再送しない
- 圧縮（gzip）：本文のバイト数を減らして転送を速くする

どちらも「無駄な転送を減らす」ことで速くする。実ネットワークは使わず核だけを確認する。
"""
import gzip
import hashlib


def etag_for(body):
    """本文から ETag（内容の指紋）を計算する。内容が同じなら同じ ETag になる。

    ETag は二重引用符で囲むのが HTTP の慣習。
    """
    digest = hashlib.md5(body.encode("utf-8")).hexdigest()
    return f'"{digest}"'


def handle_conditional_get(body, if_none_match=None):
    """条件付き GET を処理し、(status, headers, body) を返す。

    クライアントが前回の ETag を If-None-Match で送ってくる。
    それが現在の ETag と一致すれば内容は変わっていない → 304 Not Modified（本文なし）。
    一致しなければ 200 + 本文 + 現在の ETag を返す。
    本文の再送を省けるので、変化の少ないリソースで効く。
    """
    etag = etag_for(body)
    if if_none_match == etag:
        return (304, {"ETag": etag}, "")        # 本文を送らない
    return (200, {"ETag": etag}, body)


def gzip_compress(text):
    """テキストを gzip 圧縮したバイト列を返す。"""
    return gzip.compress(text.encode("utf-8"))


def gzip_decompress(data):
    """gzip 圧縮されたバイト列を元のテキストに戻す。"""
    return gzip.decompress(data).decode("utf-8")


def compression_ratio(text):
    """圧縮後 / 圧縮前 のバイト数比を返す。小さいほどよく縮んでいる。

    繰り返しの多いテキスト（HTML/JSON/CSS など）はよく縮む。
    逆に短い/ランダムなデータは gzip のヘッダ分でむしろ増えることもある。
    """
    raw = len(text.encode("utf-8"))
    compressed = len(gzip_compress(text))
    return compressed / raw


if __name__ == "__main__":
    body = '{"items": [1, 2, 3]}'

    # 1回目：ETag 付きで本文を返す
    status, headers, sent = handle_conditional_get(body)
    print("1st:", status, headers)                 # 200 {'ETag': '"..."'}

    # 2回目：クライアントが同じ ETag を送る → 内容不変なら 304（本文なし）
    status, headers, sent = handle_conditional_get(body, if_none_match=headers["ETag"])
    print("2nd:", status, "body再送:", bool(sent))  # 304 body再送: False

    # gzip：繰り返しの多いテキストはよく縮む
    html = "<div>hello</div>" * 500
    print("圧縮比:", round(compression_ratio(html), 4))   # 0.0x（大幅に縮む）
