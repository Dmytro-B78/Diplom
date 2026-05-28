# ================================================================
# Stub: exit_intelligence.py  (mirrors real interface)
# Real file: bot_ai/strategy/meta/exit_intelligence.py
# ================================================================

MOMENTUM_FLIP_THRESH    = -0.5
MOMENTUM_FLIP_BARS      = 2
TREND_FLIP_CONFIRM_BARS = 2
STAGNATION_BARS         = 12
STAGNATION_RR_MIN       = 0.5
MTF_BIAS_FLIP_THRESH    = -0.3


class ExitIntelState:
    def __init__(self):
        self.momentum_flip_bars = 0
        self.trend_flip_bars    = 0
        self.bars_in_trade      = 0
        self.max_rr_seen        = 0.0


def _get_or_create_exit_state(strategy):
    if not hasattr(strategy, "_exit_intel_state") or strategy._exit_intel_state is None:
        strategy._exit_intel_state = ExitIntelState()
    return strategy._exit_intel_state


def reset_exit_intel_state(strategy):
    strategy._exit_intel_state = ExitIntelState()


def _check_momentum_flip(state, meta_state):
    momentum = float(meta_state.get("momentum", 0.0))
    if momentum < MOMENTUM_FLIP_THRESH:
        state.momentum_flip_bars += 1
    else:
        state.momentum_flip_bars = 0
    if state.momentum_flip_bars >= MOMENTUM_FLIP_BARS:
        state.momentum_flip_bars = 0
        return {"reason": "MOMENTUM_FLIP", "momentum": round(momentum, 4), "bars": MOMENTUM_FLIP_BARS}
    return None


def _check_trend_flip(state, strategy, meta_state):
    ema_fast = meta_state.get("ema_fast") or getattr(strategy, "ema_fast", None)
    ema_slow = getattr(strategy, "ema_slow", None)
    if ema_fast is None or ema_slow is None:
        return None
    if ema_fast < ema_slow:
        state.trend_flip_bars += 1
    else:
        state.trend_flip_bars = 0
    if state.trend_flip_bars >= TREND_FLIP_CONFIRM_BARS:
        state.trend_flip_bars = 0
        return {"reason": "TREND_FLIP", "ema_fast": round(ema_fast, 6), "ema_slow": round(ema_slow, 6)}
    return None


def _check_regime_exit(meta_state):
    mtf_bias   = float(meta_state.get("mtf_bias_4h",  0.0))
    global_reg = meta_state.get("global_regime", "normal")
    atr_regime = meta_state.get("atr_regime_1h",  "normal")
    if (
        mtf_bias   < MTF_BIAS_FLIP_THRESH
        and global_reg  in ("high", "normal")
        and atr_regime  in ("high", "extreme")
    ):
        return {"reason": "REGIME_EXIT", "mtf_bias": round(mtf_bias, 4),
                "global_reg": global_reg, "atr_regime": atr_regime}
    return None


def _check_stagnation(state, strategy, meta_state):
    state.bars_in_trade += 1
    if strategy.entry_price is None:
        return None
    atr = meta_state.get("atr_1h") or getattr(strategy, "atr_1h", None)
    if atr is None or atr <= 0:
        return None
    close        = float(meta_state["close"])
    initial_risk = atr * 1.5
    rr           = (close - strategy.entry_price) / initial_risk if initial_risk > 0 else 0.0
    if rr > state.max_rr_seen:
        state.max_rr_seen = rr
    if state.bars_in_trade >= STAGNATION_BARS and state.max_rr_seen < STAGNATION_RR_MIN:
        return {"reason": "STAGNATION", "bars_in_trade": state.bars_in_trade,
                "max_rr_seen": round(state.max_rr_seen, 4)}
    return None


def evaluate_exits(strategy, meta_state):
    if strategy.position != "LONG":
        return None
    state = _get_or_create_exit_state(strategy)

    result = _check_momentum_flip(state, meta_state)
    if result:
        return _build_exit(result, meta_state)

    result = _check_trend_flip(state, strategy, meta_state)
    if result:
        return _build_exit(result, meta_state)

    if strategy.entry_price and strategy.atr_1h:
        close = float(meta_state["close"])
        rr    = (close - strategy.entry_price) / (strategy.atr_1h * 1.5)
        if rr > 0.3:
            result = _check_regime_exit(meta_state)
            if result:
                return _build_exit(result, meta_state)

    result = _check_stagnation(state, strategy, meta_state)
    if result:
        return _build_exit(result, meta_state)

    return None


def _build_exit(reason_dict, meta_state):
    return {
        "kind":        "meta_signal",
        "signal":      "CLOSE_LONG",
        "reason":      reason_dict["reason"],
        "exit_price":  float(meta_state["close"]),    # <-- FIX v5.7: close price (fill), not trigger
        "confidence":  float(meta_state.get("confidence", 0.0)),
        "exit_detail": reason_dict,
    }
