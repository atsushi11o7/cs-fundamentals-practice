"""
realtime.py — リアルタイム通信の要点を小さく動かす（標準ライブラリのみ）

サーバからクライアントへ「更新をすぐ届ける」方式は複数ある。実際のネットワークや
ブラウザは使わず、各方式の"核"だけを取り出して確認する。

- ロングポーリング：クライアントがカーソル（既読位置）を持って新着を取りに来る
- SSE（Server-Sent Events）：サーバ→クライアントの一方向テキストストリームの整形
- WebSocket：接続を確立するハンドシェイク（Sec-WebSocket-Accept）の計算
"""
import base64
import hashlib


# --- ロングポーリング：カーソルで新着を取りに来る ---

class MessageLog:
    """追記型のメッセージログ。クライアントはカーソル（既読数）以降を取得する。

    ロングポーリングの核は「サーバが状態を保持し、クライアントが自分の位置以降を問い合わせる」
    こと。実際はここでサーバが新着が来るまで応答を保留するが、核はこの差分取得にある。
    """

    def __init__(self):
        self._messages = []

    def append(self, message):
        self._messages.append(message)

    def poll(self, cursor):
        """cursor 以降の新着と、次のカーソルを返す。新着が無ければ ([], cursor)。

        cursor を返すことで、クライアントは「どこまで受け取ったか」を更新できる。
        取りこぼしを防ぐ鍵はこのカーソル（オフセット）にある。
        """
        new = self._messages[cursor:]
        return new, cursor + len(new)


# --- SSE：一方向テキストストリームの整形 ---

def format_sse(data, event=None, event_id=None):
    """Server-Sent Events の1メッセージをテキストに整形する。

    `field: value` の行を並べ、**空行でメッセージの終端**を表す。
    data が改行を含む場合は、各行を data: で始める（SSE の仕様）。
    """
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if event is not None:
        lines.append(f"event: {event}")
    for line in str(data).split("\n"):
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


# --- WebSocket：ハンドシェイクの accept キー計算 ---

# RFC 6455 で定められた固定 GUID
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def websocket_accept(client_key):
    """WebSocket ハンドシェイクの Sec-WebSocket-Accept を計算する。

    クライアントの Sec-WebSocket-Key に固定 GUID を連結し、SHA-1 → base64。
    サーバがこれを返すことで「WebSocket を理解しているサーバだ」と示し、接続が確立する。
    HTTP から WebSocket へ「アップグレード」する握手の核。
    """
    digest = hashlib.sha1((client_key + WS_GUID).encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


if __name__ == "__main__":
    # ロングポーリング
    log = MessageLog()
    log.append("hello")
    log.append("world")
    new, cursor = log.poll(0)
    print("poll(0):", new, "next cursor:", cursor)   # ['hello', 'world'] 2
    print("poll(2):", log.poll(2))                    # ([], 2) 新着なし
    log.append("again")
    print("poll(2):", log.poll(2))                    # (['again'], 3)

    # SSE
    print(repr(format_sse("hi", event="message", event_id="1")))
    # 'id: 1\nevent: message\ndata: hi\n\n'

    # WebSocket accept（RFC 6455 の例）
    print(websocket_accept("dGhlIHNhbXBsZSBub25jZQ=="))
    # s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
