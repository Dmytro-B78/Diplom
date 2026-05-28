"""
conftest.py — общие фикстуры для всех тестов дипломного проекта.
Фикстуры доступны автоматически во всех test_*.py файлах.
"""
import sys
import os
import pytest
from decimal import Decimal

# ─── NT-Tech bot path (direct import support) ────────────────────────────────
_NT_PATH = r"C:\TradingBots\NT"
if os.path.isdir(_NT_PATH) and _NT_PATH not in sys.path:
    sys.path.insert(0, _NT_PATH)

# ─── Фикстуры: рыночные данные ───────────────────────────────────────────────
@pytest.fixture
def normal_market():
    return {
        "symbol": "BTCUSDT",
        "price": Decimal("65000.00"),
        "atr": Decimal("1200.00"),
        "balance": Decimal("1000.00"),
        "side": "BUY",
    }

@pytest.fixture
def low_atr_market():
    return {
        "symbol": "TRXUSDT",
        "price": Decimal("0.1250"),
        "atr": Decimal("0.0003"),
        "balance": Decimal("1000.00"),
        "side": "BUY",
    }

@pytest.fixture
def zero_balance_market():
    return {
        "symbol": "ETHUSDT",
        "price": Decimal("3200.00"),
        "atr": Decimal("80.00"),
        "balance": Decimal("0.00"),
        "side": "BUY",
    }

@pytest.fixture
def sell_market():
    return {
        "symbol": "SOLUSDT",
        "price": Decimal("180.00"),
        "atr": Decimal("5.00"),
        "balance": Decimal("500.00"),
        "side": "SELL",
    }

# ─── Фикстуры: ответы Binance API ────────────────────────────────────────────
@pytest.fixture
def mock_binance_order_response():
    return {
        "symbol": "BTCUSDT",
        "orderId": 123456789,
        "status": "FILLED",
        "side": "BUY",
        "type": "MARKET",
        "origQty": "0.01000000",
        "executedQty": "0.01000000",
        "cummulativeQuoteQty": "650.00000000",
        "fills": [
            {
                "price": "65000.00000000",
                "qty": "0.01000000",
                "commission": "0.00001000",
                "commissionAsset": "BTC",
            }
        ],
    }

@pytest.fixture
def mock_binance_error_response():
    return {
        "code": -2010,
        "msg": "Account has insufficient balance for requested action.",
    }

@pytest.fixture
def mock_binance_klines():
    return [
        [1700000000000, "64000", "65500", "63800", "65000", "100.5"],
        [1700000060000, "65000", "65800", "64900", "65300", "95.2"],
        [1700000120000, "65300", "65400", "64800", "65100", "88.7"],
    ]
