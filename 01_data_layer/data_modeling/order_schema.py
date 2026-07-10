"""
order_schema.py — 「属性を持つ中間テーブル」を含むデータモデリングの例

schema_example.py の多対多（ArticleTag）は、ペアをつなぐだけで自分の属性を持たなかった。
現実の多対多はしばしば「関係そのものに属性がある」。EC の注文がその典型で、
「どの注文に・どの商品が・いくつ・いくらで入ったか」は関係（明細）の属性になる。

この中間エンティティ（OrderItem = 注文明細）が数量・単価を持つ点と、
単価を「商品を参照する」のではなく「明細にコピーして持つ」設計判断を、動くコードで示す。
"""
from dataclasses import dataclass


@dataclass
class Customer:
    id: int
    name: str


@dataclass
class Product:
    id: int
    name: str
    price: int          # 現在の販売価格（将来変わりうる）


@dataclass
class Order:
    id: int
    customer_id: int    # 1対多：どの顧客の注文か（外部キー相当）


@dataclass
class OrderItem:
    """注文明細 = 属性を持つ中間エンティティ。

    order と product の多対多をつなぐが、関係自身が quantity と unit_price を持つ。
    unit_price は「注文した時点の価格」をコピーして保存する（スナップショット）。
    商品価格は後で変わりうるが、過去の注文金額は変わってはいけないため。
    """
    order_id: int
    product_id: int
    quantity: int
    unit_price: int     # 注文時点の単価のスナップショット（Product.price の写しではなく確定値）


class Shop:
    """各エンティティをリストで保持し、関係をたどる。"""

    def __init__(self):
        self.customers = []
        self.products = []
        self.orders = []
        self.order_items = []

    def _product(self, product_id):
        return next(p for p in self.products if p.id == product_id)

    def place_order(self, order_id, customer_id, lines):
        """注文を作る。lines は (product_id, quantity) のリスト。

        明細の単価は、その時点の Product.price をコピーして確定させる。
        """
        self.orders.append(Order(order_id, customer_id))
        for product_id, quantity in lines:
            price_now = self._product(product_id).price
            self.order_items.append(
                OrderItem(order_id, product_id, quantity, unit_price=price_now)
            )

    def items_of_order(self, order_id):
        return [it for it in self.order_items if it.order_id == order_id]

    def order_total(self, order_id):
        """注文合計 = 各明細の quantity * unit_price の総和。

        現在の商品価格ではなく、明細に確定保存した単価で計算する。
        """
        return sum(it.quantity * it.unit_price for it in self.items_of_order(order_id))

    def orders_of_customer(self, customer_id):
        return [o for o in self.orders if o.customer_id == customer_id]


if __name__ == "__main__":
    shop = Shop()
    shop.customers.append(Customer(1, "alice"))
    shop.products.append(Product(100, "book", price=1200))
    shop.products.append(Product(101, "pen", price=150))

    shop.place_order(500, customer_id=1, lines=[(100, 2), (101, 3)])
    print("合計:", shop.order_total(500))          # 2*1200 + 3*150 = 2850

    # 後から商品価格が変わっても、確定済みの注文金額は変わらない
    shop._product(100).price = 9999
    print("値上げ後の合計:", shop.order_total(500))  # 2850 のまま
    print("alice の注文:", [o.id for o in shop.orders_of_customer(1)])  # [500]
