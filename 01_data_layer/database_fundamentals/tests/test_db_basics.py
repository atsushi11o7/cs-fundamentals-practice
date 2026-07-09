"""
データベース基礎（sqlite3）の動作確認。
実行： uv run pytest 01_data_layer/database_fundamentals -v
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_basics import (
    FIND_ARTICLES_SQL,
    add_user_with_articles,
    connect,
    count_rows,
    create_schema,
    create_user_id_index,
    query_plan,
)


@pytest.fixture
def conn():
    c = connect()
    create_schema(c)
    yield c
    c.close()


def test_index_changes_query_plan(conn):
    # 索引が無いうちは全走査（SCAN）
    before = query_plan(conn, FIND_ARTICLES_SQL, (1,))
    assert any("SCAN" in d for d in before)

    # 索引を張ると索引利用（SEARCH ... USING INDEX）に変わる
    create_user_id_index(conn)
    after = query_plan(conn, FIND_ARTICLES_SQL, (1,))
    assert any("USING INDEX" in d for d in after)
    assert not any("SCAN" in d for d in after)


def test_transaction_commits_on_success(conn):
    ok = add_user_with_articles(conn, (1, "a@example.com", "alice"), ["t1", "t2"])
    assert ok is True
    assert count_rows(conn, "users") == 1
    assert count_rows(conn, "articles") == 2


def test_transaction_rolls_back_on_failure(conn):
    # 2件目の記事の直前で失敗させる → ユーザーも記事も一切残らない（原子性）
    ok = add_user_with_articles(
        conn, (2, "b@example.com", "bob"), ["x1", "x2", "x3"], fail_at=1
    )
    assert ok is False
    assert count_rows(conn, "users") == 0
    assert count_rows(conn, "articles") == 0


def test_foreign_key_rejects_orphan(conn):
    # 存在しない user_id を参照する記事は外部キー制約で拒否される
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO articles(id, user_id, title) VALUES(?, ?, ?)",
            (999, 12345, "orphan"),
        )


def test_unique_constraint_rejects_duplicate_email(conn):
    conn.execute("INSERT INTO users(id, email, name) VALUES(1, 'dup@x.com', 'a')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO users(id, email, name) VALUES(2, 'dup@x.com', 'b')")
