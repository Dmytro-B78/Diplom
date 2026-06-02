import pytest
from bot_ai.risk.risk_guard import RiskGuard

def make_rg(**kw):
    defaults = dict(
        base_risk_pct=0.01, max_risk_pct=0.01,
        daily_loss_limit=0.02, weekly_loss_limit=0.05,
        max_open_positions=4,
    )
    defaults.update(kw)
    return RiskGuard(**defaults)

def open_signal(sym):
    return {"signal": "OPEN_LONG", "symbol": sym}

def close_signal(sym):
    return {"signal": "CLOSE_LONG", "symbol": sym}

class TestInit:
    def test_daily_pnl_zero(self):
        assert make_rg()._daily_pnl == pytest.approx(0.0)
    def test_weekly_pnl_zero(self):
        assert make_rg()._weekly_pnl == pytest.approx(0.0)
    def test_kill_switch_off(self):
        assert make_rg()._kill_switch is False
    def test_no_positions_at_start(self):
        assert make_rg()._positions == {}

class TestOpenLong:
    def test_open_long_accepted(self):
        rg = make_rg()
        r = rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        assert r is not None and r["action"] == "OPEN_LONG"
    def test_open_long_registers_position(self):
        rg = make_rg()
        rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        assert "SOLUSDT" in rg._positions
    def test_open_long_duplicate_blocked(self):
        rg = make_rg()
        rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        assert rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT") is None
    def test_open_long_max_positions_blocked(self):
        rg = make_rg(max_open_positions=2)
        rg.process_meta_signal(open_signal("SYM1USDT"), "SYM1USDT")
        rg.process_meta_signal(open_signal("SYM2USDT"), "SYM2USDT")
        assert rg.process_meta_signal(open_signal("SYM3USDT"), "SYM3USDT") is None
    def test_none_signal_returns_none(self):
        assert make_rg().process_meta_signal(None) is None
    def test_two_different_symbols_accepted(self):
        rg = make_rg(max_open_positions=4)
        r1 = rg.process_meta_signal(open_signal("BTCUSDT"), "BTCUSDT")
        r2 = rg.process_meta_signal(open_signal("ETHUSDT"), "ETHUSDT")
        assert r1 is not None and r2 is not None

class TestCloseLong:
    def test_close_long_accepted(self):
        rg = make_rg()
        rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        r = rg.process_meta_signal(close_signal("SOLUSDT"), "SOLUSDT")
        assert r is not None and r["action"] == "CLOSE_LONG"
    def test_close_long_removes_position(self):
        rg = make_rg()
        rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        rg.process_meta_signal(close_signal("SOLUSDT"), "SOLUSDT")
        assert "SOLUSDT" not in rg._positions
    def test_close_long_not_in_position_returns_none(self):
        rg = make_rg()
        assert rg.process_meta_signal(close_signal("SOLUSDT"), "SOLUSDT") is None
    def test_reopen_after_close(self):
        rg = make_rg()
        rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        rg.process_meta_signal(close_signal("SOLUSDT"), "SOLUSDT")
        r = rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        assert r is not None

class TestKillSwitch:
    def test_kill_switch_daily_limit(self):
        rg = make_rg(daily_loss_limit=0.02)
        rg.record_trade_result(-0.021)
        assert rg._kill_switch is True
    def test_kill_switch_blocks_open(self):
        rg = make_rg(daily_loss_limit=0.02)
        rg.record_trade_result(-0.021)
        assert rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT") is None
    def test_kill_switch_weekly_limit(self):
        rg = make_rg(weekly_loss_limit=0.05)
        rg.record_trade_result(-0.051)
        assert rg._kill_switch is True
    def test_reset_daily_clears_pnl(self):
        rg = make_rg()
        rg.record_trade_result(-0.01)
        rg.reset_daily()
        assert rg._daily_pnl == pytest.approx(0.0)
    def test_reset_weekly_clears_kill_switch(self):
        rg = make_rg(weekly_loss_limit=0.05)
        rg.record_trade_result(-0.051)
        rg.reset_weekly()
        assert rg._kill_switch is False
    def test_kill_switch_not_triggered_below_limit(self):
        rg = make_rg(daily_loss_limit=0.02)
        rg.record_trade_result(-0.019)
        assert rg._kill_switch is False
    def test_multiple_losses_accumulate(self):
        rg = make_rg(daily_loss_limit=0.02)
        rg.record_trade_result(-0.011)
        rg.record_trade_result(-0.011)
        assert rg._kill_switch is True

class TestPositionSize:
    def test_position_size_positive(self):
        assert make_rg().compute_position_size(1.0, 0.91, 1000.0, "normal") > 0
    def test_position_size_zero_distance(self):
        assert make_rg().compute_position_size(1.0, 1.0, 1000.0, "normal") == pytest.approx(0.0)
    def test_extreme_regime_smaller(self):
        rg = make_rg()
        sz_normal  = rg.compute_position_size(1.0, 0.91, 1000.0, "normal")
        sz_extreme = rg.compute_position_size(1.0, 0.91, 1000.0, "extreme")
        assert sz_extreme < sz_normal
    def test_larger_balance_larger_size(self):
        rg = make_rg()
        sz_small = rg.compute_position_size(1.0, 0.91, 500.0, "normal")
        sz_large = rg.compute_position_size(1.0, 0.91, 2000.0, "normal")
        assert sz_large > sz_small

class TestForceClose:
    def test_force_close_removes_position(self):
        rg = make_rg()
        rg.process_meta_signal(open_signal("SOLUSDT"), "SOLUSDT")
        rg.force_close("SOLUSDT")
        assert "SOLUSDT" not in rg._positions
    def test_force_close_unknown_no_error(self):
        make_rg().force_close("UNKNOWN")

class TestStatus:
    def test_status_keys(self):
        s = make_rg().status()
        assert "kill_switch" in s
        assert "position_count" in s
        assert "daily_pnl" in s
    def test_status_position_count(self):
        rg = make_rg()
        rg.process_meta_signal(open_signal("BTCUSDT"), "BTCUSDT")
        assert rg.status()["position_count"] == 1
    def test_status_kill_switch_reflects_state(self):
        rg = make_rg(daily_loss_limit=0.02)
        rg.record_trade_result(-0.021)
        assert rg.status()["kill_switch"] is True
