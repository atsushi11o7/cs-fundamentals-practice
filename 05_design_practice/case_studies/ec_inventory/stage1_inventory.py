"""
Stage 1 — 単一商品の在庫：一番単純な形

最初の要件は最小限。「1つの商品に在庫があり、購入されたら在庫を減らす。
在庫が足りなければ売らない。」まずこれだけを、一番単純に作る。

守りたい不変条件は「**在庫が負にならない**」こと（＝売り越さない）。
予約システムが「時間帯が重ならない」を守ったのに対し、EC は「個数（在庫）」を守る。
希少資源が"連続した区間"ではなく"離散したカウント"である点が対比になる。

この段階の割り切り：
- 商品は1つだけ（複数商品・注文明細は stage2 で）
- 単一スレッド前提（並行購入は stage3 で DB のトランザクションと合わせて扱う）
"""


class Inventory:
    """単一商品の在庫。買えれば減らし、足りなければ拒否する。"""

    def __init__(self, stock):
        self._stock = stock

    @property
    def stock(self):
        return self._stock

    def buy(self, quantity):
        """quantity 個の購入を試みる。成功で True、在庫不足なら False。

        不変条件「在庫 >= 0」を守るため、**減らす前に足りるか確認**する。
        足りなければ在庫は一切変えない。
        """
        if quantity <= 0:
            return False                 # 不正な数量は拒否
        if self._stock < quantity:
            return False                 # 在庫不足：売らない（在庫は変えない）
        self._stock -= quantity
        return True


if __name__ == "__main__":
    inv = Inventory(stock=3)
    print(inv.buy(2), inv.stock)    # True 1
    print(inv.buy(2), inv.stock)    # False 1（残り1に2個は売れない、在庫は変わらない）
    print(inv.buy(1), inv.stock)    # True 0
    print(inv.buy(1), inv.stock)    # False 0
