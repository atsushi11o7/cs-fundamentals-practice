"""
Stage 2 — データ設計（このケースの主役）

要件が本物に近づく：
- 商品は複数ある。それぞれ価格と在庫を持つ。
- 顧客が、複数の商品をまとめて1回の注文で買う。
- 注文の合計金額を出せる。

ここが EC の中心。stage1 の「在庫カウント1つ」では表せないので、
**エンティティ・関係・不変条件を厳密に設計する**。

## エンティティと関係
- Customer（顧客）  1 ──< Order（注文）        1対多
- Order（注文）     1 ──< OrderItem（注文明細） 1対多
- Product（商品）   1 ──< OrderItem            1対多
  → OrderItem は Order と Product の多対多をつなぐ「属性を持つ中間エンティティ」。
    数量(quantity)と単価(unit_price)という「関係の属性」を持つ（→ 01_data_layer/data_modeling）。

## 不変条件（データに宿るルール）
- 在庫は負にならない（買えるぶんしか売らない）。
- 注文合計 = Σ(数量 × 単価)。合計は明細から導出する（重複して持たない）。
- 単価は「注文した時点の価格」を明細にコピーして確定（スナップショット）。
  後で商品価格が変わっても、過去の注文金額は変わってはいけないから。

## この段の割り切り
- 保存はメモリ（dataclass）。実DB・トランザクション・並行制御は stage3。
- ただし place_order は「全明細の在庫を確認してから減らす」= 部分的に売れた状態を作らない
  （原子性の考え方。stage3 でこれを DB のトランザクションに置き換える）。
"""
from dataclasses import dataclass, field


@dataclass
class Customer:
    id: int
    name: str


@dataclass
class Product:
    id: int
    name: str
    price: int          # 現在の販売価格（将来変わりうる）
    stock: int          # 在庫数


@dataclass
class Order:
    id: int
    customer_id: int    # 1対多：どの顧客の注文か


@dataclass
class OrderItem:
    """注文明細＝属性を持つ中間エンティティ。数量と、注文時点の単価を持つ。"""
    order_id: int
    product_id: int
    quantity: int
    unit_price: int     # Product.price の写しではなく、注文時点の確定値


class Shop:
    """商品・在庫・注文を扱うドメインサービス（メモリ保持）。"""

    def __init__(self):
        self.customers = {}
        self.products = {}
        self.orders = []
        self.order_items = []
        self._next_order_id = 1

    def add_customer(self, customer):
        self.customers[customer.id] = customer

    def add_product(self, product):
        self.products[product.id] = product

    def place_order(self, customer_id, lines):
        """注文を作る。lines は (product_id, quantity) のリスト。

        成功で Order を返す。在庫不足が1つでもあれば **何も変えずに** None を返す
        （部分的に売れた状態を作らない＝原子性）。
        単価はこの時点の Product.price をコピーして確定する。
        """
        # 1) まず全明細の在庫を確認（減らす前にチェックする）
        for product_id, quantity in lines:
            product = self.products.get(product_id)
            if product is None or quantity <= 0 or product.stock < quantity:
                return None

        # 2) 全部OKなら在庫を減らし、注文と明細を作る
        order = Order(self._next_order_id, customer_id)
        self._next_order_id += 1
        self.orders.append(order)
        for product_id, quantity in lines:
            product = self.products[product_id]
            product.stock -= quantity
            self.order_items.append(
                OrderItem(order.id, product_id, quantity, unit_price=product.price)
            )
        return order

    def order_total(self, order_id):
        """注文合計＝明細の Σ(数量 × 単価)。確定済みの単価で計算する。"""
        return sum(
            it.quantity * it.unit_price
            for it in self.order_items
            if it.order_id == order_id
        )

    def orders_of_customer(self, customer_id):
        return [o for o in self.orders if o.customer_id == customer_id]


if __name__ == "__main__":
    shop = Shop()
    shop.add_customer(Customer(1, "alice"))
    shop.add_product(Product(100, "book", price=1200, stock=5))
    shop.add_product(Product(101, "pen", price=150, stock=10))

    order = shop.place_order(1, [(100, 2), (101, 3)])
    print("order:", order.id, "total:", shop.order_total(order.id))  # 2*1200 + 3*150 = 2850
    print("book stock:", shop.products[100].stock)                    # 3（5 - 2）

    # 在庫不足は何も変えずに None（原子性）
    print(shop.place_order(1, [(100, 999)]))                          # None
    print("book stock:", shop.products[100].stock)                    # 3 のまま

    # 単価スナップショット：値上げしても過去の注文金額は不変
    shop.products[100].price = 9999
    print("total after price change:", shop.order_total(order.id))    # 2850 のまま
