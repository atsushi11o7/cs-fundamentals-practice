"""
リアルタイム通信の各方式の動作確認。
実行： uv run pytest 03_interface_layer/realtime_communication -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtime import MessageLog, format_sse, websocket_accept


# --- ロングポーリング ---

def test_poll_returns_all_from_start():
    log = MessageLog()
    log.append("a")
    log.append("b")
    new, cursor = log.poll(0)
    assert new == ["a", "b"]
    assert cursor == 2


def test_poll_no_new_messages():
    log = MessageLog()
    log.append("a")
    _, cursor = log.poll(0)
    # 同じカーソルで再度取りに来ても新着は無い
    assert log.poll(cursor) == ([], 1)


def test_poll_returns_only_new_since_cursor():
    log = MessageLog()
    log.append("a")
    _, cursor = log.poll(0)
    log.append("b")
    log.append("c")
    new, next_cursor = log.poll(cursor)
    assert new == ["b", "c"]         # 取りこぼさず、既読は再取得しない
    assert next_cursor == 3


# --- SSE ---

def test_format_sse_minimal():
    assert format_sse("hello") == "data: hello\n\n"


def test_format_sse_with_event_and_id():
    assert format_sse("hi", event="message", event_id="1") == (
        "id: 1\nevent: message\ndata: hi\n\n"
    )


def test_format_sse_multiline_data():
    # 改行を含む data は各行を data: で始める
    assert format_sse("line1\nline2") == "data: line1\ndata: line2\n\n"


# --- WebSocket ハンドシェイク ---

def test_websocket_accept_rfc_example():
    # RFC 6455 の既知の例
    assert websocket_accept("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_websocket_accept_is_deterministic():
    key = "x3JJHMbDL1EzLkh9GBhXDw=="
    assert websocket_accept(key) == websocket_accept(key)
