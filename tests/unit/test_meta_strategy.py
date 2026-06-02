import pytest
from bot_ai.strategy.meta_strategy import MetaStrategy

FLAT_CANDLE = {
    "timestamp": 1710000000000,
    "open": 100.0, "high": 100.5,
    "low":   99.5, "close": 100.0,
    "volume": 10.0,
}

def make_candles(n=200, base=100.0, step=0.001):
    candles = []
    price = base
    for i in range(n):
        price *= (1.0 + step)
        half = price * 0.01
        candles.append({
            "timestamp": 1710000000000 + i * 3600000,
            "open":  round(price * 0.999, 6),
            "high":  round(price + half,  6),
            "low":   round(price - half,  6),
            "close": round(price * 1.001, 6),
            "volume": 100.0,
        })
    return candles

def make_candles_down(n=200):
    return make_candles(n, step=-0.001)

def _signal(r):
    if r is None: return None
    if isinstance(r, tuple): return r[0]
    return r

class TestInstantiation:
    def test_default_constructor(self):
        assert MetaStrategy() is not None
    def test_empty_params_dict(self):
        assert MetaStrategy({}) is not None
    def test_initial_position_is_none(self):
        assert MetaStrategy({}).position is None
    def test_initial_bar_index_zero(self):
        assert MetaStrategy({}).bar_index == 0

class TestSmokeUptrend:
    def test_no_crash_200_bars(self):
        ms = MetaStrategy({})
        for c in make_candles(): ms.on_candle(c)
    def test_bar_index_equals_candle_count(self):
        ms = MetaStrategy({})
        candles = make_candles()
        for c in candles: ms.on_candle(c)
        assert ms.bar_index == len(candles)
    def test_ema_fast_initialized_after_warmup(self):
        ms = MetaStrategy({})
        for c in make_candles(): ms.on_candle(c)
        assert ms.ema_fast is not None and ms.ema_fast > 0.0
    def test_output_is_tuple_or_none(self):
        ms = MetaStrategy({})
        for c in make_candles():
            r = ms.on_candle(c)
            assert r is None or isinstance(r, tuple)

class TestSmokeFlatDown:
    def test_no_crash_flat_200_bars(self):
        ms = MetaStrategy({})
        for i in range(200):
            ms.on_candle({**FLAT_CANDLE, "timestamp": FLAT_CANDLE["timestamp"] + i * 3600000})
    def test_no_crash_downtrend(self):
        ms = MetaStrategy({})
        for c in make_candles_down(): ms.on_candle(c)

class TestOutputShape:
    def test_signal_is_none_or_dict(self):
        ms = MetaStrategy({})
        for c in make_candles():
            sig = _signal(ms.on_candle(c))
            assert sig is None or isinstance(sig, dict)
    def test_signal_dict_has_signal_key(self):
        ms = MetaStrategy({})
        for c in make_candles():
            sig = _signal(ms.on_candle(c))
            if sig is not None:
                assert "signal" in sig
    def test_no_double_open_without_close(self):
        ms = MetaStrategy({})
        in_pos = False
        for c in make_candles():
            sig = _signal(ms.on_candle(c))
            if sig:
                s = sig.get("signal")
                if s == "OPEN_LONG":
                    assert not in_pos
                    in_pos = True
                elif s == "CLOSE_LONG":
                    in_pos = False
    def test_atr_positive_after_warmup(self):
        ms = MetaStrategy({})
        for c in make_candles(): ms.on_candle(c)
        assert ms.atr_1h is not None and ms.atr_1h > 0.0
    def test_bar_index_increments_each_candle(self):
        ms = MetaStrategy({})
        ms.on_candle(make_candles(1)[0])
        assert ms.bar_index == 1
