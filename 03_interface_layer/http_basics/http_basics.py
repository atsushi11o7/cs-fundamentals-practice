"""
http_basics.py — HTTP リクエスト/レスポンスを自前で解析・組み立てる（標準ライブラリのみ）

http.server や requests に頼らず、「HTTP が実際にやり取りしている文字列」を
手で解析・生成する。これにより、メソッド・パス・ヘッダ・ボディ・ステータスコードが
プロトコル上どう表現されているかを、ネットワーク無しで確認できる。

HTTP メッセージの形（テキスト）:

    <リクエスト行 or ステータス行>\r\n
    <ヘッダ名>: <値>\r\n
    ...\r\n
    \r\n              ← 空行がヘッダとボディの境界
    <ボディ>
"""
from dataclasses import dataclass

CRLF = "\r\n"

# よく使うステータスコードと理由句
STATUS_REASON = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    429: "Too Many Requests",
    500: "Internal Server Error",
}


@dataclass
class Request:
    method: str          # GET, POST, ...
    path: str            # クエリを除いたパス（例: /users/1）
    query: dict          # ?a=1&b=2 を {"a": "1", "b": "2"} にしたもの
    version: str         # HTTP/1.1 など
    headers: dict        # ヘッダ名は小文字化して格納（HTTP のヘッダは大小無視）
    body: str


def _parse_query(query_string):
    """"a=1&b=2" を {"a": "1", "b": "2"} に。空なら空 dict。"""
    result = {}
    if not query_string:
        return result
    for pair in query_string.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
        else:
            key, value = pair, ""
        result[key] = value
    return result


def parse_request(raw):
    """生の HTTP リクエスト文字列を Request に解析する。

    ヘッダとボディは最初の空行（\r\n\r\n）で分割する。
    リクエスト行「METHOD PATH VERSION」からメソッド・パス・クエリ・バージョンを取り出す。
    """
    head, _, body = raw.partition(CRLF + CRLF)
    lines = head.split(CRLF)

    method, target, version = lines[0].split(" ")
    path, _, query_string = target.partition("?")

    headers = {}
    for line in lines[1:]:
        if not line:
            continue
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()

    return Request(
        method=method,
        path=path,
        query=_parse_query(query_string),
        version=version,
        headers=headers,
        body=body,
    )


def build_response(status, headers=None, body="", version="HTTP/1.1"):
    """ステータス・ヘッダ・ボディから、生の HTTP レスポンス文字列を組み立てる。

    Content-Length は本文の長さから自動で付与する（未指定時）。
    ボディ長を正しく伝えないと、受信側は本文の終端を判断できない。
    """
    reason = STATUS_REASON.get(status, "")
    headers = dict(headers or {})

    # Content-Length を自動付与（呼び出し側が明示していなければ）
    if not any(k.lower() == "content-length" for k in headers):
        headers["Content-Length"] = str(len(body.encode("utf-8")))

    lines = [f"{version} {status} {reason}"]
    for name, value in headers.items():
        lines.append(f"{name}: {value}")
    head = CRLF.join(lines)
    return head + CRLF + CRLF + body


if __name__ == "__main__":
    raw = (
        "GET /users/1?verbose=true HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Accept: application/json\r\n"
        "\r\n"
    )
    req = parse_request(raw)
    print(req.method, req.path, req.query)          # GET /users/1 {'verbose': 'true'}
    print(req.headers["host"])                       # example.com

    res = build_response(200, {"Content-Type": "application/json"}, '{"id":1}')
    print("---response---")
    print(res)
