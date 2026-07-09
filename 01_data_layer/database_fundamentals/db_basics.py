"""
db_basics.py — データベース基礎を sqlite3（標準ライブラリ）で確かめる

ストレージエンジンを自作する代わりに、Python 同梱の sqlite3 を使って
「インデックスがなぜ検索を速くするか」「トランザクションで原子性がどう保たれるか」
「外部キー制約が整合性をどう守るか」を、実際に動くコードで観察する。
"""
import sqlite3


def connect():
    """メモリ上のDBに接続し、外部キー制約を有効化して返す。

    SQLite は既定では外部キーを無視するため、明示的に PRAGMA で有効化する。
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn):
    """users（1）と articles（多）の最小スキーマ。1対多を外部キーで表す。

    - email に UNIQUE 制約 → 重複を許さない（同時に索引が自動生成される）
    - articles.user_id は users.id を参照する外部キー
    """
    conn.executescript(
        """
        CREATE TABLE users (
            id    INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name  TEXT NOT NULL
        );
        CREATE TABLE articles (
            id      INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title   TEXT NOT NULL
        );
        """
    )


def query_plan(conn, sql, params=()):
    """EXPLAIN QUERY PLAN の結果（detail 文字列のリスト）を返す。

    'SCAN'（全行を走査）か 'SEARCH ... USING INDEX'（索引で絞り込み）かを
    文字列で観察できる。インデックスの有無で計画がどう変わるかを確認するのに使う。
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return [row[3] for row in rows]


# インデックスの効果を観察する対象クエリ。
# articles.user_id には既定では索引が無いので、最初は全走査になる。
FIND_ARTICLES_SQL = "SELECT id, title FROM articles WHERE user_id = ?"


def create_user_id_index(conn):
    """articles.user_id に索引を張る。以後この列での検索は全走査を避けられる。"""
    conn.execute("CREATE INDEX idx_articles_user ON articles(user_id)")


def add_user_with_articles(conn, user, titles, fail_at=None):
    """1人のユーザーと複数記事を「1つのトランザクション」で追加する。

    途中で失敗したら全体をロールバックし、部分的な書き込みを一切残さない（原子性）。
    `with conn:` は、正常終了で commit・例外で rollback するトランザクション境界。

    user: (id, email, name)
    titles: 記事タイトルのリスト
    fail_at: この index の記事を入れる直前で失敗を発生させる（テスト用）。None なら成功。

    戻り値: 成功したら True、途中失敗でロールバックしたら False。
    """
    try:
        with conn:
            conn.execute(
                "INSERT INTO users(id, email, name) VALUES(?, ?, ?)", user
            )
            for i, title in enumerate(titles):
                if fail_at is not None and i == fail_at:
                    raise ValueError("simulated failure mid-transaction")
                conn.execute(
                    "INSERT INTO articles(id, user_id, title) VALUES(?, ?, ?)",
                    (user[0] * 100 + i, user[0], title),
                )
    except ValueError:
        return False
    return True


def count_rows(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


if __name__ == "__main__":
    conn = connect()
    create_schema(conn)

    # --- インデックスの効果：全走査 → 索引利用 ---
    print("索引なし:", query_plan(conn, FIND_ARTICLES_SQL, (1,)))
    create_user_id_index(conn)
    print("索引あり:", query_plan(conn, FIND_ARTICLES_SQL, (1,)))

    # --- トランザクションの原子性：途中失敗は全ロールバック ---
    ok = add_user_with_articles(conn, (1, "a@example.com", "alice"),
                                ["t1", "t2", "t3"])
    print("成功追加:", ok, "users =", count_rows(conn, "users"))

    ng = add_user_with_articles(conn, (2, "b@example.com", "bob"),
                                ["x1", "x2", "x3"], fail_at=1)
    print("失敗追加:", ng, "users =", count_rows(conn, "users"))  # bob は残らない

    # --- 外部キー制約：存在しない user_id は拒否 ---
    try:
        conn.execute(
            "INSERT INTO articles(id, user_id, title) VALUES(?, ?, ?)",
            (999, 12345, "orphan"),
        )
    except sqlite3.IntegrityError as e:
        print("外部キー違反を拒否:", e)
