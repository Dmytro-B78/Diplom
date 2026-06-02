import pytest, csv
from bot_ai.engine.offline_runner import load_csv, _check_intrabar_stops, _build_trade_record
from bot_ai.strategy.meta.trail_engine import TrailState

def make_csv(rows, tmp_path):
    p = tmp_path / "test.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        for r in rows: w.writerow(r)
    return str(p)

class MockStrat:
    def __init__(self, entry=100.0):
        self.entry_price            = entry
        self.abs_loss_stop_pct      = -0.06
        self.max_price_since_entry  = 110.0
        self.hwm_drawdown_stop_pct  = -0.05
        self.ema_fast               = 105.0
        self.atr_1h                 = 2.0
        self.ema_fast_stop_mult     = 0.5
        self.trail_state            = None

def make_candle(low=100.0, high=105.0, close=103.0):
    return {"open": 101.0, "high": high, "low": low, "close": close}

def make_meta():
    return {"close": 103.0, "atr_1h": 2.0, "slope": 0.0,
            "momentum": 0.0, "mtf_bias": 0.0, "atr_regime_1h": "normal"}

def make_trade(entry=100.0, entry_index=0):
    return {"entry_price": entry, "entry_index": entry_index,
            "entry_time_ms": 1710000000000, "atr_1h": 2.0, "atr_4h": 3.0,
            "regime": "normal", "global_regime": "normal", "confidence": 0.15}

class TestLoadCsv:
    def test_basic(self, tmp_path):
        rows = [[1710000000000, 100.0, 101.0, 99.0, 100.5, 10.0]]
        assert len(load_csv(make_csv(rows, tmp_path))) == 1
    def test_fields(self, tmp_path):
        rows = [[1710000000000, 100.0, 101.0, 99.0, 100.5, 10.0]]
        r = load_csv(make_csv(rows, tmp_path))[0]
        for key in ("timestamp", "open", "high", "low", "close"):
            assert key in r
    def test_values(self, tmp_path):
        rows = [[1710000000000, 100.0, 101.0, 99.0, 100.5, 10.0]]
        r = load_csv(make_csv(rows, tmp_path))[0]
        assert r["close"] == pytest.approx(100.5)
        assert r["high"]  == pytest.approx(101.0)
    def test_skips_short_rows(self, tmp_path):
        rows = [[1710000000000, 100.0],
                [1710003600000, 100.0, 101.0, 99.0, 100.5, 10.0]]
        assert len(load_csv(make_csv(rows, tmp_path))) == 1
    def test_skips_invalid_floats(self, tmp_path):
        rows = [["ts", "open", "high", "low", "close"],
                [1710000000000, 100.0, 101.0, 99.0, 100.5, 10.0]]
        assert len(load_csv(make_csv(rows, tmp_path))) == 1
    def test_empty(self, tmp_path):
        assert load_csv(make_csv([], tmp_path)) == []
    def test_multiple_rows(self, tmp_path):
        rows = [[1710000000000 + i*3600000, 100.0+i, 101.0+i, 99.0+i, 100.5+i, 10.0]
                for i in range(10)]
        assert len(load_csv(make_csv(rows, tmp_path))) == 10
    def test_timestamp_is_int(self, tmp_path):
        rows = [[1710000000000, 100.0, 101.0, 99.0, 100.5, 10.0]]
        assert isinstance(load_csv(make_csv(rows, tmp_path))[0]["timestamp"], int)

class TestCheckIntrabarStops:
    def test_no_stops_triggered(self):
        s = MockStrat(entry=100.0)
        reason, price = _check_intrabar_stops(s, make_candle(low=106.0), make_meta())
        assert reason is None and price is None
    def test_abs_stop_triggered(self):
        s = MockStrat(entry=100.0)
        reason, _ = _check_intrabar_stops(s, make_candle(low=93.0), make_meta())
        assert reason == "ABS_STOP"
    def test_abs_stop_priority_over_hwm(self):
        s = MockStrat(entry=100.0)
        s.max_price_since_entry = 100.0
        s.hwm_drawdown_stop_pct = -0.02
        reason, _ = _check_intrabar_stops(s, make_candle(low=93.0), make_meta())
        assert reason == "ABS_STOP"
    def test_hwm_stop_triggered(self):
        s = MockStrat(entry=100.0)
        s.max_price_since_entry = 110.0
        s.hwm_drawdown_stop_pct = -0.05
        reason, _ = _check_intrabar_stops(s, make_candle(low=104.0), make_meta())
        assert reason == "HWM_DRAWDOWN_STOP"
    def test_trail_stop_triggered(self):
        s = MockStrat(entry=100.0)
        s.max_price_since_entry = 100.0
        s.hwm_drawdown_stop_pct = -0.50
        s.trail_state = TrailState()
        s.trail_state.trail_stop = 98.0
        reason, _ = _check_intrabar_stops(s, make_candle(low=97.0), make_meta())
        assert reason == "TRAIL_STOP"
    def test_ema_stop_triggered(self):
        s = MockStrat(entry=100.0)
        s.max_price_since_entry = 100.0
        s.hwm_drawdown_stop_pct = -0.50
        s.trail_state = TrailState()
        s.trail_state.trail_stop = None
        s.ema_fast = 105.0; s.atr_1h = 2.0
        reason, _ = _check_intrabar_stops(s, make_candle(low=103.0), make_meta())
        assert reason == "EMA_STOP"
    def test_no_trigger_price_above_all_stops(self):
        s = MockStrat(entry=100.0)
        s.max_price_since_entry = 100.0
        reason, _ = _check_intrabar_stops(s, make_candle(low=99.0), make_meta())
        assert reason is None

class TestBuildTradeRecord:
    def test_keys(self):
        s = MockStrat()
        r = _build_trade_record(make_trade(100.0, 0), 105.0, "EMA_STOP", 1710003600000, 5, s)
        for key in ("kind", "entry", "exit", "exit_reason", "pnl_pct", "duration_bars"):
            assert key in r
    def test_pnl_positive(self):
        s = MockStrat()
        r = _build_trade_record(make_trade(100.0, 0), 105.0, "EMA_STOP", 1710003600000, 3, s)
        assert r["pnl_pct"] == pytest.approx(5.0, rel=0.01)
    def test_pnl_negative(self):
        s = MockStrat()
        r = _build_trade_record(make_trade(100.0, 0), 94.0, "ABS_STOP", 1710003600000, 2, s)
        assert r["pnl_pct"] == pytest.approx(-6.0, rel=0.01)
    def test_duration(self):
        s = MockStrat()
        r = _build_trade_record(make_trade(100.0, 2), 105.0, "EMA_STOP", 1710003600000, 10, s)
        assert r["duration_bars"] == 8
    def test_exit_reason(self):
        s = MockStrat()
        r = _build_trade_record(make_trade(100.0, 0), 105.0, "HWM_DRAWDOWN_STOP", 1710003600000, 3, s)
        assert r["exit_reason"] == "HWM_DRAWDOWN_STOP"
    def test_kind_is_trade(self):
        s = MockStrat()
        r = _build_trade_record(make_trade(100.0, 0), 105.0, "EMA_STOP", 1710003600000, 3, s)
        assert r["kind"] == "trade"
    def test_with_trail_state(self):
        s = MockStrat()
        s.trail_state = TrailState()
        s.trail_state.trail_stop = 98.0
        r = _build_trade_record(make_trade(100.0, 0), 105.0, "EMA_STOP", 1710003600000, 3, s)
        assert r["trail_state_exit"] is not None
        assert "phase" in r["trail_state_exit"]
    def test_pnl_breakeven(self):
        s = MockStrat()
        r = _build_trade_record(make_trade(100.0, 0), 100.0, "EMA_STOP", 1710003600000, 1, s)
        assert r["pnl_pct"] == pytest.approx(0.0, abs=0.01)
