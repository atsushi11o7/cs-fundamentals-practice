"""
EC在庫 stage2（データ設計）の動作確認。
実行： uv run pytest 05_design_practice/case_studies/ec_inventory -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage2 import Customer, Product, Shop


def make_shop():
    shop = Shop()
    shop.add_customer(Customer(1, "alice"))
    shop.add_product(Product(100, "book", price=1200, stock=5))
    shop.add_product(Product(101, "pen", price=150, stock=10))
    return shop


def test_place_order_decrements_stock():
    shop = make_shop()
    shop.place_order(1, [(100, 2)])
    assert shop.products[100].stock == 3


def test_order_total_from_line_items():
    shop = make_shop()
    order = shop.place_order(1, [(100, 2), (101, 3)])
    assert shop.order_total(order.id) == 2 * 1200 + 3 * 150   # 2850


def test_insufficient_stock_rejects_whole_order():
    shop = make_shop()
    # 2明細のうち2つ目が在庫不足 → 注文全体が失敗し、1つ目の在庫も減らない（原子性）
    order = shop.place_order(1, [(100, 1), (101, 999)])
    assert order is None
    assert shop.products[100].stock == 5      # 減っていない
    assert shop.products[101].stock == 10
    assert shop.orders == []                  # 注文も作られていない


def test_stock_never_oversold():
    shop = make_shop()
    assert shop.place_order(1, [(100, 6)]) is None   # 在庫5に6個は不可
    assert shop.products[100].stock == 5


def test_unit_price_is_snapshot():
    shop = make_shop()
    order = shop.place_order(1, [(100, 2)])
    shop.products[100].price = 9999           # 後から値上げ
    assert shop.order_total(order.id) == 2400  # 2 * 1200 のまま


def test_orders_of_customer():
    shop = make_shop()
    shop.place_order(1, [(100, 1)])
    shop.place_order(1, [(101, 1)])
    assert len(shop.orders_of_customer(1)) == 2


def test_invalid_quantity_rejected():
    shop = make_shop()
    assert shop.place_order(1, [(100, 0)]) is None
    assert shop.products[100].stock == 5
