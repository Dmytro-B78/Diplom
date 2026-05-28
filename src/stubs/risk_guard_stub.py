# Stub: risk_guard.py for diploma tests
# Replace with real imports from C:\TradingBots\NT when ready
from decimal import Decimal


def calculate_position_size(balance, price, atr, risk_pct=0.01):
    if balance <= 0:
        return Decimal("0")
    MAX_RISK = Decimal("0.05")
    risk_pct = min(Decimal(str(risk_pct)), MAX_RISK)
    risk_amount = Decimal(str(balance)) * risk_pct
    stop_distance = Decimal(str(atr)) * Decimal("1.5")
    if stop_distance <= 0:
        return Decimal("0")
    return (risk_amount / stop_distance).quantize(Decimal("0.00000001"))


def should_kill_switch(daily_pnl: float, max_daily_loss: float) -> bool:
    return daily_pnl <= max_daily_loss
