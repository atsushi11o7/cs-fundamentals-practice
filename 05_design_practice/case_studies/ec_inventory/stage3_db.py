"""
Stage 3 — 実DB化・トランザクション・並行制御・API

stage2 の設計を、実際の DB（sqlite3）に落とす。ここで「DB でどう不変条件を守るか」を扱う。

## メモリから DB へ移す動機
- 永続化：再起動しても注文・在庫が残る。
- 並行制御：同時注文で最後の1個を取り合う「売り越し」を防ぐ。stage2 の
  「確認してから減らす」は単一スレッドでは正しいが、複数リクエストが割り込むと
  両方が『在庫あり』と判断して売り越す（→ 04_reliability_and_scale/concurrency）。
  予約システムはプロセス内ロックで守ったが、EC は **DB のトランザクションと制約**で守る。

## DB で不変条件を守る2段構え
1. **条件付き減算**：`UPDATE ... SET stock = stock - ? WHERE id = ? AND stock >= ?`。
   在庫が足りる行だけが更新される。更新行数が0なら在庫不足。この1文が不可分なので、
   同時実行でも「確認と減算の隙間」が生まれず、売り越さない。
2. **CHECK 制約**：`stock >= 0`。最後の砦として、どの経路からも在庫を負にできない。

そして注文全体（複数明細の在庫減算＋注文＋明細の作成）を1つの**トランザクション**で囲む。
途中で在庫不足になれば全部ロールバックし、部分的に売れた状態を残さない（原子性）。
"""
import os
import sys

import sqlite3

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
sys.path.insert(0, os.path.join(_ROOT, "03_interface_layer", "rest_api_design"))

from rest_api import Router                 # 03

SCHEMA = """
CREATE TABLE customers (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE products (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    price INTEGER NOT NULL,
    stock INTEGER NOT NULL CHECK (stock >= 0)     -- 在庫は負にならない（最後の砦）
);
CREATE TABLE orders (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id)
);
CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL,
    unit_price INTEGER NOT NULL
);
"""


class InsufficientStock(Exception):
    """在庫不足。トランザクションをロールバックさせるために使う。"""


class OrderDB:
    """sqlite で注文・在庫を扱う。不変条件は制約とトランザクションで守る。"""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def add_customer(self, customer_id, name):
        self.conn.execute("INSERT INTO customers(id, name) VALUES(?, ?)", (customer_id, name))
        self.conn.commit()

    def add_product(self, product_id, name, price, stock):
        self.conn.execute(
            "INSERT INTO products(id, name, price, stock) VALUES(?, ?, ?, ?)",
            (product_id, name, price, stock),
        )
        self.conn.commit()

    def product(self, product_id):
        row = self.conn.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1], "price": row[2], "stock": row[3]}

    def place_order(self, customer_id, lines):
        """注文を作る。成功で order_id、在庫不足なら None。数量が不正なら ValueError。

        全体を1トランザクションで囲む。各明細は条件付き減算で在庫を確保し、
        1つでも不足すれば InsufficientStock で全ロールバック（原子性）。
        単価は減算時点の価格をコピーして確定する。
        """
        for _, quantity in lines:
            if quantity <= 0:
                raise ValueError("invalid quantity")
        try:
            with self.conn:                      # commit / 例外で rollback
                snapshots = []
                for product_id, quantity in lines:
                    cur = self.conn.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                        (quantity, product_id, quantity),
                    )
                    if cur.rowcount == 0:        # 在庫不足 or 商品なし
                        raise InsufficientStock(product_id)
                    price = self.conn.execute(
                        "SELECT price FROM products WHERE id = ?", (product_id,)
                    ).fetchone()[0]
                    snapshots.append((product_id, quantity, price))

                cur = self.conn.execute(
                    "INSERT INTO orders(customer_id) VALUES(?)", (customer_id,)
                )
                order_id = cur.lastrowid
                for product_id, quantity, price in snapshots:
                    self.conn.execute(
                        "INSERT INTO order_items(order_id, product_id, quantity, unit_price)"
                        " VALUES(?, ?, ?, ?)",
                        (order_id, product_id, quantity, price),
                    )
            return order_id
        except InsufficientStock:
            return None

    def order_total(self, order_id):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(quantity * unit_price), 0) FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        return row[0]


class EcApp:
    """OrderDB を 03 のルータで API 化したもの。

    POST /orders          → 201 {order_id, total} / 409（在庫不足）/ 400
    GET  /products/{id}   → 200 {id,name,price,stock} / 404
    """

    def __init__(self, db):
        self.db = db
        self.router = self._build_router()

    def _build_router(self):
        r = Router()
        r.add("POST", "/orders", self._create_order)
        r.add("GET", "/products/{id}", self._get_product)
        return r

    def _create_order(self, params, body):
        body = body or {}
        customer_id = body.get("customer_id")
        lines = body.get("lines")
        if customer_id is None or not lines:
            return (400, {"error": "customer_id and lines required"})
        try:
            order_id = self.db.place_order(customer_id, [tuple(line) for line in lines])
        except ValueError:
            return (400, {"error": "invalid quantity"})
        if order_id is None:
            return (409, {"error": "insufficient stock"})
        return (201, {"order_id": order_id, "total": self.db.order_total(order_id)})

    def _get_product(self, params, body):
        product = self.db.product(int(params["id"]))
        if product is None:
            return (404, {"error": "not found"})
        return (200, product)

    def handle(self, method, path, body=None):
        return self.router.dispatch(method, path, body)


if __name__ == "__main__":
    db = OrderDB()
    db.add_customer(1, "alice")
    db.add_product(100, "book", price=1200, stock=5)
    db.add_product(101, "pen", price=150, stock=10)
    app = EcApp(db)

    print(app.handle("POST", "/orders", {"customer_id": 1, "lines": [[100, 2], [101, 3]]}))
    # (201, {'order_id': 1, 'total': 2850})
    print(app.handle("GET", "/products/100"))            # (200, {... 'stock': 3})
    print(app.handle("POST", "/orders", {"customer_id": 1, "lines": [[100, 999]]}))
    # (409, {'error': 'insufficient stock'})
    print(app.handle("GET", "/products/100"))            # stock は 3 のまま（ロールバック）
