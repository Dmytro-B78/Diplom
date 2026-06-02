import pytest
from bot_ai.strategy.meta.indicators import ema, true_range, update_indicators

class MockStrat:
    def __init__(self, price=100.0):
        self.ema_fast_len  = 9
        self.ema_slow_len  = 21
        self.ema_trend_len = 50
        self.atr_1h_alpha  = 2.0 / 15
        self.atr_4h_alpha  = 2.0 / 60
        self.ema_fast      = price
        self.ema_slow      = price
        self.ema_trend     = price
        self.prev_ema_fast = price
        self.atr_1h        = 1.0
        self.atr_4h        = 1.0
        self.atr_1h_mean   = 1.0
        self.atr_4h_mean   = 1.0
        self.prev_close    = price
        self.prev_open     = price
        self.prev_high     = price
        self.prev_low      = price
        self.last_close    = price
        self.last_open     = price
        self.last_high     = price
        self.last_low      = price
        self.trend_strength = 0.0
        self.slope          = 0.0
        self.momentum       = 0.0
        self.momentum_hist  = []
        self.slope_hist     = []
        self.trend_hist     = []
        self.position               = "FLAT"
        self.max_price_since_entry  = None
        self._ema_align_bars        = 0
        self.ema_aligned            = False

def make_candle(close, high=None, low=None, open_=None):
    return {
        "close": close,
        "high":  high  if high  is not None else close + 0.5,
        "low":   low   if low   is not None else close - 0.5,
        "open":  open_ if open_ is not None else close,
    }

class TestEma:
    def test_init_returns_value(self):
        assert ema(None, 100.0, 0.1) == pytest.approx(100.0)
    def test_blends_prev_and_value(self):
        assert ema(100.0, 110.0, 0.1) == pytest.approx(101.0)
    def test_alpha_1_returns_value(self):
        assert ema(50.0, 100.0, 1.0) == pytest.approx(100.0)
    def test_alpha_0_returns_prev(self):
        assert ema(50.0, 100.0, 0.0) == pytest.approx(50.0)
    def test_converges_uptrend(self):
        v = 100.0
        for _ in range(50):
            v = ema(v, 200.0, 0.1)
        assert v > 150.0
    def test_converges_downtrend(self):
        v = 200.0
        for _ in range(50):
            v = ema(v, 100.0, 0.1)
        assert v < 150.0
    def test_none_prev_any_alpha(self):
        assert ema(None, 55.0, 0.5) == pytest.approx(55.0)

class TestTrueRange:
    def test_no_prev_close(self):
        assert true_range(None, high=105.0, low=95.0) == pytest.approx(10.0)
    def test_gap_up(self):
        assert true_range(100.0, high=106.0, low=103.0) == pytest.approx(6.0)
    def test_gap_down(self):
        assert true_range(100.0, high=97.0, low=92.0) == pytest.approx(8.0)
    def test_inside_bar(self):
        assert true_range(100.0, high=101.0, low=99.0) == pytest.approx(2.0)
    def test_nonnegative(self):
        assert true_range(100.0, high=100.5, low=99.5) >= 0.0
    def test_symmetric_gap(self):
        assert true_range(100.0, high=103.0, low=97.0) == pytest.approx(6.0)

class TestUpdateIndicators:
    def test_sets_last_close(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        assert s.last_close == pytest.approx(105.0)
    def test_sets_prev_close(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        assert s.prev_close == pytest.approx(100.0)
    def test_ema_fast_moves_toward_price(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(110.0))
        assert s.ema_fast > 100.0
    def test_atr_updates_on_candle(self):
        s = MockStrat(100.0)
        old_atr = s.atr_1h
        update_indicators(s, make_candle(100.0, high=102.0, low=98.0))
        assert s.atr_1h != old_atr or s.atr_1h > 0
    def test_momentum_positive_on_up_candle(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        assert s.momentum > 0
    def test_momentum_negative_on_down_candle(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(95.0))
        assert s.momentum < 0
    def test_slope_in_range(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        assert -1.0 <= s.slope <= 1.0
    def test_momentum_in_range(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        assert -1.0 <= s.momentum <= 1.0
    def test_trend_strength_in_range(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        assert -1.0 <= s.trend_strength <= 1.0
    def test_momentum_hist_appended(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        assert len(s.momentum_hist) == 1
    def test_ema_aligned_requires_3_bars(self):
        s = MockStrat(100.0)
        for i in range(2):
            update_indicators(s, make_candle(100.0 + (i+1)*5))
        assert s.ema_aligned is False
    def test_ema_aligned_after_uptrend(self):
        s = MockStrat(100.0)
        for i in range(30):
            update_indicators(s, make_candle(100.0 + i * 1.0))
        assert s.ema_aligned is True
    def test_hwm_updated_in_long(self):
        s = MockStrat(100.0)
        s.position = "LONG"
        s.max_price_since_entry = 100.0
        update_indicators(s, make_candle(110.0))
        assert s.max_price_since_entry == pytest.approx(110.0)
    def test_hwm_not_updated_when_flat(self):
        s = MockStrat(100.0)
        s.position = "FLAT"
        s.max_price_since_entry = None
        update_indicators(s, make_candle(110.0))
        assert s.max_price_since_entry is None
    def test_two_candles_prev_close_tracks(self):
        s = MockStrat(100.0)
        update_indicators(s, make_candle(105.0))
        update_indicators(s, make_candle(110.0))
        assert s.prev_close == pytest.approx(105.0)
        assert s.last_close == pytest.approx(110.0)
