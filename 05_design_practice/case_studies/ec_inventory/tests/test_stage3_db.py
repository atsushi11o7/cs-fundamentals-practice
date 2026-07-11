"""
EC在庫 stage3（実DB・トランザクション・API）の動作確認。
実行： uv run pytest 05_design_practice/case_studies/ec_inventory -v
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage3_db import EcApp, OrderDB


@pytest.fixture
def db():
    d = OrderDB()
    d.add_customer(1, "alice")
    d.add_product(100, "book", price=1200, stock=5)
    d.add_product(101, "pen", price=150, stock=10)
    return d


def test_place_order_decrements_stock(db):
    db.place_order(1, [(100, 2)])
    assert db.product(100)["stock"] == 3


def test_order_total(db):
    order_id = db.place_order(1, [(100, 2), (101, 3)])
    assert db.order_total(order_id) == 2850


def test_insufficient_stock_rolls_back_whole_order(db):
    # 2明細目が在庫不足 → トランザクション全体がロールバック
    order_id = db.place_order(1, [(100, 1), (101, 999)])
    assert order_id is None
    assert db.product(100)["stock"] == 5      # 1つ目の減算も取り消される（原子性）
    assert db.product(101)["stock"] == 10


def test_cannot_oversell(db):
    assert db.place_order(1, [(100, 6)]) is None   # 在庫5に6個
    assert db.product(100)["stock"] == 5


def test_check_constraint_blocks_negative_stock(db):
    # 条件なしで在庫を負にしようとすると CHECK 制約が最後の砦として弾く
    with pytest.raises(sqlite3.IntegrityError):
        with db.conn:
            db.conn.execute("UPDATE products SET stock = stock - 999 WHERE id = 100")


def test_invalid_quantity_raises(db):
    with pytest.raises(ValueError):
        db.place_order(1, [(100, 0)])


# --- API ---

def test_api_create_order_201(db):
    app = EcApp(db)
    status, body = app.handle(
        "POST", "/orders", {"customer_id": 1, "lines": [[100, 2], [101, 3]]}
    )
    assert status == 201
    assert body["total"] == 2850


def test_api_insufficient_stock_409(db):
    app = EcApp(db)
    status, _ = app.handle("POST", "/orders", {"customer_id": 1, "lines": [[100, 999]]})
    assert status == 409


def test_api_invalid_quantity_400(db):
    app = EcApp(db)
    assert app.handle("POST", "/orders", {"customer_id": 1, "lines": [[100, 0]]})[0] == 400


def test_api_missing_fields_400(db):
    app = EcApp(db)
    assert app.handle("POST", "/orders", {"customer_id": 1})[0] == 400


def test_api_get_product(db):
    app = EcApp(db)
    status, product = app.handle("GET", "/products/100")
    assert status == 200
    assert product["stock"] == 5


def test_api_get_unknown_product_404(db):
    app = EcApp(db)
    assert app.handle("GET", "/products/999")[0] == 404
