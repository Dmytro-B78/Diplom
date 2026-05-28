# ================================================================
# Stub: intrabar_stops.py  (mirrors real interface)
# Real file: bot_ai/strategy/meta/intrabar_stops.py
# trail_engine dependency is stubbed out below.
# ================================================================

# --- trail_engine stub (avoid real import) ---
def evaluate_intrabar(strategy, low_price):
    ts = getattr(strategy, "trail_state", None)
    if ts is None:
        return None
    stop = getattr(ts, "stop_price", None)
    if stop is not None and low_price <= stop:
        return ("ATR_TRAIL", stop)
    return None

def evaluate_ema_intrabar(strategy, low_price, meta_state):
    return None


def clamp(x, lo, hi):
    if x < lo: return lo
    if x > hi: return hi
    return x


def intrabar_abs_stop(strategy, low_price):
    """Absolute stop: entry_price * (1 + abs_loss_stop_pct)."""
    if strategy.entry_price is None:
        return None
    stop_price = strategy.entry_price * (1.0 + strategy.abs_loss_stop_pct)
    if low_price <= stop_price:
        return ("ABS_STOP", stop_price)
    return None


def intrabar_hwm_stop(strategy, low_price):
    """HWM drawdown stop: max_price * (1 + hwm_drawdown_stop_pct)."""
    if strategy.max_price_since_entry is None:
        return None
    stop_price = strategy.max_price_since_entry * (1.0 + strategy.hwm_drawdown_stop_pct)
    if low_price <= stop_price:
        return ("HWM_DRAWDOWN_STOP", stop_price)
    return None


def intrabar_atr_trail(strategy, low_price):
    return evaluate_intrabar(strategy, low_price)


def intrabar_ema_stop(strategy, low_price, meta_state=None):
    if meta_state is None:
        ts = getattr(strategy, "trail_state", None)
        if ts is None:
            return None
        ema_fast = getattr(strategy, "ema_fast", None)
        atr      = getattr(strategy, "atr_1h",   None)
        if ema_fast is None or atr is None or atr <= 0.0:
            return None
        ema_stop_mult = getattr(strategy, "ema_fast_stop_mult", 0.5)
        stop_price = ema_fast - atr * ema_stop_mult
        if low_price <= stop_price:
            return ("EMA_STOP", stop_price)
        return None
    return evaluate_ema_intrabar(strategy, low_price, meta_state)


def compute_adaptive_trail_mult(strategy):
    ts = getattr(strategy, "trail_state", None)
    if ts is not None:
        return ts.atr_mult
    return 2.0


def adjust_trailing_mult_by_regime(current_mult, local_regime):
    return current_mult
