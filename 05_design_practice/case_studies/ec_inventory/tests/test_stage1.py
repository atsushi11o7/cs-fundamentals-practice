"""
EC在庫 stage1 の動作確認。
実行： uv run pytest 05_design_practice/case_studies/ec_inventory -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage1 import Inventory


def test_buy_within_stock_succeeds():
    inv = Inventory(3)
    assert inv.buy(2) is True
    assert inv.stock == 1


def test_buy_over_stock_rejected_and_unchanged():
    inv = Inventory(1)
    assert inv.buy(2) is False
    assert inv.stock == 1              # 在庫は変わらない


def test_buy_exact_stock():
    inv = Inventory(2)
    assert inv.buy(2) is True
    assert inv.stock == 0


def test_stock_never_goes_negative():
    inv = Inventory(1)
    inv.buy(1)
    assert inv.buy(1) is False
    assert inv.stock == 0             # 0 のまま、負にならない


def test_invalid_quantity_rejected():
    inv = Inventory(5)
    assert inv.buy(0) is False
    assert inv.buy(-1) is False
    assert inv.stock == 5
