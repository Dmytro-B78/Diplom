# ================================================================
# File: src/stubs/entry_engine_stub.py
# Stub: NT-Tech Entry Engine v2.0 (Breakout + Re-Entry)
# Source: bot_ai/strategy/meta/entry_engine.py
#
# Changes vs original:
#   - Relative imports replaced with injectable callables
#     (stage1_fn, stage2_fn, breakout_fn) for test isolation.
#   - Default implementations use stage1_stub.
#   - Interface identical to production compute_entry_signal().
# ================================================================
from src.stubs.stage1_stub import stage1_check as _default_stage1


def compute_entry_signal(
    strategy,
    meta_state,
    debug_info,
    *,
    stage1_fn=None,
    stage2_fn=None,
    breakout_fn=None,
):
    if stage1_fn is None:
        stage1_fn = _default_stage1
    if stage2_fn is None:
        stage2_fn = _noop_stage2
    if breakout_fn is None:
        breakout_fn = _noop_breakout

    if strategy.position == "LONG":
        return None

    close       = float(meta_state["close"])
    smooth_conf = float(meta_state.get("confidence",     0.0))
    atr_regime  = meta_state.get("atr_regime_1h",        "normal")
    momentum    = float(meta_state.get("momentum",        0.0))
    slope       = float(meta_state.get("slope",           0.0))
    trend_str   = float(meta_state.get("trend_strength",  0.0))

    if strategy.last_exit_bar_index is not None:
        bars_since_exit = strategy.bar_index - strategy.last_exit_bar_index
    else:
        bars_since_exit = None

    position_state = {
        "last_exit_reason": strategy.last_exit_reason,
        "bars_since_exit":  bars_since_exit,
    }

    if (
        strategy.last_exit_reason == "ABS_STOP"
        and bars_since_exit is not None
        and bars_since_exit < 8
    ):
        debug_info["abs_stop_cooldown"] = {
            "active":          True,
            "bars_since_exit": bars_since_exit,
            "bars_remaining":  8 - bars_since_exit,
        }
        return None

    debug_info["abs_stop_cooldown"] = {"active": False}

    reentry_ok = False
    if (
        strategy.last_exit_reason == "EMA_STOP"
        and bars_since_exit is not None
        and 0 < bars_since_exit <= 12
        and meta_state.get("mtf_4h_aligned", False)
        and trend_str >= 0.0
        and momentum  >  0.0
        and slope     >= 0.0
        and atr_regime != "extreme"
    ):
        s2_pass, _dbg2 = stage2_fn(meta_state, position_state)
        if s2_pass:
            reentry_ok = True

    debug_info["reentry_candidate"] = {
        "last_exit_reason": strategy.last_exit_reason,
        "bars_since_exit":  bars_since_exit,
        "mtf_4h_aligned":   meta_state.get("mtf_4h_aligned", False),
        "trend_strength":   trend_str,
        "slope":            slope,
        "momentum":         momentum,
        "atr_regime":       atr_regime,
        "reentry_ok":       reentry_ok,
    }

    if reentry_ok:
        debug_info["reentry_used"] = True
        return {
            "kind":         "meta_signal",
            "signal":       "OPEN_LONG",
            "reason":       "REENTRY_EMA_STOP",
            "confidence":   smooth_conf,
            "_entry_price": close,
        }

    s1_pass, s1_debug = stage1_fn(meta_state)
    debug_info["stage1"] = s1_debug

    if not s1_pass:
        return None

    breakout = breakout_fn(strategy, meta_state)
    debug_info["breakout"] = breakout

    if breakout is None:
        return None

    return {
        "kind":          "meta_signal",
        "signal":        "OPEN_LONG",
        "reason":        breakout["reason"],
        "confidence":    smooth_conf,
        "atr_1h":        breakout.get("atr_1h"),
        "bars_since_bo": breakout.get("bars_since_bo"),
        "_entry_price":  close,
    }


def _noop_stage2(meta_state, position_state):
    return False, {"reason": "stage2_not_implemented"}


def _noop_breakout(strategy, meta_state):
    return None
