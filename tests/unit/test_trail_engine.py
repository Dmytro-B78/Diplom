# =============================================================================
# File: tests/unit/test_trail_engine.py
# Diplom — NT-Tech LiveEngine 5.8
# =============================================================================

import pytest
from bot_ai.strategy.meta.trail_engine import (
    TrailState, trail_engine, evaluate_intrabar, evaluate_ema_intrabar,
    reset_trail_state, _compute_rr, _compute_phase,
    PROFIT_LOCK_RR_T1, PROFIT_LOCK_RR_T2, GRACE_BARS,
    PHASE_1_MULT, PHASE_2_MULT, PHASE_3_MULT, LATCH_MULT,
)

class MockStrat:
    def __init__(self, price=100.0, entry=100.0, atr=2.0):
        self.position               = "LONG"
        self.entry_price            = entry
        self.atr_1h                 = atr
        self.ema_fast               = price
        self.max_price_since_entry  = price
        self.abs_loss_stop_pct      = -0.06
        self.trail_state            = None

def make_meta(close=100.0, atr=2.0, slope=0.0, momentum=0.0, bias=0.0, regime="normal"):
    return {"close": close, "atr_1h": atr, "slope": slope,
            "momentum": momentum, "mtf_bias": bias, "atr_regime_1h": regime}

def _run_n_bars(strat, meta, n):
    result = None
    for _ in range(n):
        result = trail_engine(strat, meta)
    return result

class TestComputeRR:
    def test_rr_zero_at_entry(self):
        assert _compute_rr(100.0, 100.0, 2.0) == pytest.approx(0.0)
    def test_rr_one_at_one_atr(self):
        assert _compute_rr(100.0, 102.0, 2.0) == pytest.approx(1.0)
    def test_rr_two_at_two_atrs(self):
        assert _compute_rr(100.0, 104.0, 2.0) == pytest.approx(2.0)
    def test_rr_zero_when_initial_risk_is_zero(self):
        assert _compute_rr(100.0, 105.0, 0.0) == pytest.approx(0.0)
    def test_rr_negative_below_entry(self):
        assert _compute_rr(100.0, 98.0, 2.0) < 0

class TestComputePhase:
    def test_phase1_below_t1(self):
        assert _compute_phase(0.9) == 1
    def test_phase2_at_t1(self):
        assert _compute_phase(PROFIT_LOCK_RR_T1) == 2
    def test_phase2_between_t1_and_t2(self):
        assert _compute_phase(1.5) == 2
    def test_phase3_at_t2(self):
        assert _compute_phase(PROFIT_LOCK_RR_T2) == 3
    def test_phase3_above_t2(self):
        assert _compute_phase(3.0) == 3

class TestTrailStateInit:
    def test_initial_phase_is_1(self):
        assert TrailState().phase == 1
    def test_latch_inactive_by_default(self):
        assert TrailState().latch_active is False
    def test_trail_stop_none_by_default(self):
        assert TrailState().trail_stop is None

class TestTrailEngineNotLong:
    def test_flat_position_returns_none(self):
        s = MockStrat(); s.position = "FLAT"
        assert trail_engine(s, make_meta()) is None
    def test_flat_position_clears_trail_state(self):
        s = MockStrat(); s.position = "LONG"
        trail_engine(s, make_meta()); s.position = "FLAT"
        trail_engine(s, make_meta())
        assert s.trail_state is None

class TestTrailEngineGracePeriod:
    def test_returns_dict_on_first_bar(self):
        assert isinstance(trail_engine(MockStrat(), make_meta()), dict)
    def test_no_trail_stop_during_grace(self):
        s = MockStrat(price=100.0, entry=100.0, atr=2.0)
        r = trail_engine(s, make_meta(close=100.0, atr=2.0))
        assert r["trail_state"]["trail_stop"] is None
    def test_stop_price_below_entry_during_grace(self):
        s = MockStrat(price=100.0, entry=100.0, atr=2.0)
        r = trail_engine(s, make_meta(close=100.0, atr=2.0))
        assert r["stop_price"] < 100.0

class TestTrailEngineAfterGrace:
    def test_trail_stop_set_after_grace(self):
        s = MockStrat(price=105.0, entry=100.0, atr=2.0)
        s.max_price_since_entry = 105.0
        r = _run_n_bars(s, make_meta(close=105.0, atr=2.0), GRACE_BARS + 1)
        assert r["trail_state"]["trail_stop"] is not None
    def test_trail_stop_below_hwm(self):
        s = MockStrat(price=110.0, entry=100.0, atr=2.0)
        s.max_price_since_entry = 110.0
        r = _run_n_bars(s, make_meta(close=110.0, atr=2.0), GRACE_BARS + 1)
        assert r["trail_state"]["trail_stop"] < 110.0
    def test_phase_advances_to_2_at_rr1(self):
        s = MockStrat(price=103.0, entry=100.0, atr=2.0)
        s.max_price_since_entry = 103.0
        r = _run_n_bars(s, make_meta(close=103.0, atr=2.0), GRACE_BARS + 1)
        assert r["trail_state"]["phase"] >= 2

class TestEvaluateIntrabar:
    def test_no_state_returns_none(self):
        s = MockStrat(); s.trail_state = None
        assert evaluate_intrabar(s, 95.0) is None
    def test_no_trail_stop_returns_none(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.trail_stop = None
        assert evaluate_intrabar(s, 95.0) is None
    def test_miss_returns_none(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.trail_stop = 90.0
        assert evaluate_intrabar(s, 95.0) is None
    def test_hit_returns_tuple(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.trail_stop = 95.0
        result = evaluate_intrabar(s, 94.0)
        assert result is not None and result[0] == "TRAIL_STOP"
    def test_exact_hit(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.trail_stop = 95.0
        assert evaluate_intrabar(s, 95.0) is not None
    def test_hit_price_equals_trail_stop(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.trail_stop = 95.0
        assert evaluate_intrabar(s, 94.0)[1] == pytest.approx(95.0)

class TestResetTrailState:
    def test_reset_creates_fresh_state(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.phase = 3
        reset_trail_state(s); assert s.trail_state.phase == 1
    def test_reset_clears_trail_stop(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.trail_stop = 99.0
        reset_trail_state(s); assert s.trail_state.trail_stop is None
    def test_reset_clears_latch(self):
        s = MockStrat(); s.trail_state = TrailState(); s.trail_state.latch_active = True
        reset_trail_state(s); assert s.trail_state.latch_active is False
