"""
属性を持つ中間エンティティ（注文明細）のモデリング確認。
実行： uv run pytest 01_data_layer/data_modeling -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from order_schema import Customer, Product, Shop


def make_shop():
    shop = Shop()
    shop.customers.append(Customer(1, "alice"))
    shop.products.append(Product(100, "book", price=1200))
    shop.products.append(Product(101, "pen", price=150))
    return shop


def test_order_total_uses_quantity_and_unit_price():
    shop = make_shop()
    shop.place_order(500, customer_id=1, lines=[(100, 2), (101, 3)])
    # 2*1200 + 3*150 = 2850
    assert shop.order_total(500) == 2850


def test_order_item_holds_relationship_attributes():
    shop = make_shop()
    shop.place_order(500, customer_id=1, lines=[(100, 2)])
    items = shop.items_of_order(500)
    assert len(items) == 1
    # 中間エンティティが数量・単価という「関係の属性」を持つ
    assert items[0].quantity == 2
    assert items[0].unit_price == 1200


def test_unit_price_is_snapshot_not_reference():
    shop = make_shop()
    shop.place_order(500, customer_id=1, lines=[(100, 2)])
    # 注文後に商品価格を変更しても、確定済みの注文金額は変わらない
    shop._product(100).price = 9999
    assert shop.order_total(500) == 2400   # 2 * 1200 のまま


def test_orders_of_customer():
    shop = make_shop()
    shop.place_order(500, customer_id=1, lines=[(100, 1)])
    shop.place_order(501, customer_id=1, lines=[(101, 1)])
    assert sorted(o.id for o in shop.orders_of_customer(1)) == [500, 501]
