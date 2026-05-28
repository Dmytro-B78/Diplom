# ================================================================
# File: src/stubs/stage1_stub.py
# Stub: NT-Tech Stage1-Lite v4.6  (STEP-H)
# Source: bot_ai/strategy/meta/stage1.py
# Pure function — no external dependencies, copied verbatim.
# ================================================================
from typing import Dict, Any, Tuple

MAX_CONF_OVERRIDE = 0.65
MIN_MOM_OVERRIDE  = None


def stage1_check(meta_state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:

    mtf_4h_aligned = bool(meta_state.get("mtf_4h_aligned", False))
    if not mtf_4h_aligned:
        return False, {
            "reason":         "4h_not_aligned",
            "mtf_4h_aligned": False,
            "atr_regime_1h":  str(meta_state.get("atr_regime_1h", "normal")),
            "momentum":       float(meta_state.get("momentum", 0.0)),
            "slope":          float(meta_state.get("slope", 0.0)),
        }

    daily_gate     = bool(meta_state.get("daily_gate", False))
    confidence     = float(meta_state.get("confidence",     0.0))
    slope          = float(meta_state.get("slope",          0.0))
    momentum       = float(meta_state.get("momentum",       0.0))
    trend_strength = float(meta_state.get("trend_strength", 0.0))
    mtf_bias_4h    = float(meta_state.get("mtf_bias_4h",   0.0))
    atr_regime_1h  = str(meta_state.get("atr_regime_1h",   "normal"))

    if atr_regime_1h == "high":
        min_conf     = 0.07
        max_conf     = 0.45
        min_slope    = 0.03
        min_momentum = 0.20
        min_trend    = 0.25
        min_mtf_bias = 0.40
    elif atr_regime_1h == "low":
        min_conf     = 0.02
        max_conf     = 0.45
        min_slope    = 0.01
        min_momentum = -0.10
        min_trend    = 0.05
        min_mtf_bias = 0.0
    else:
        min_conf     = 0.10
        max_conf     = 0.45
        min_slope    = 0.01
        min_momentum = 0.0
        min_trend    = 0.10
        min_mtf_bias = 0.10

    if MAX_CONF_OVERRIDE is not None:
        max_conf = MAX_CONF_OVERRIDE

    if MIN_MOM_OVERRIDE is not None:
        min_momentum = max(min_momentum, MIN_MOM_OVERRIDE)

    if not daily_gate:
        min_momentum = max(min_momentum, 0.30)
        min_slope    = max(min_slope,    0.05)

    if confidence < min_conf:
        return False, {
            "reason": "low_confidence", "confidence": confidence,
            "min_conf": min_conf, "atr_regime_1h": atr_regime_1h,
            "daily_gate": daily_gate, "mtf_4h_aligned": mtf_4h_aligned,
            "momentum": momentum, "slope": slope,
        }
    if confidence > max_conf:
        return False, {
            "reason": "confidence_ceiling", "confidence": confidence,
            "max_conf": max_conf, "atr_regime_1h": atr_regime_1h,
            "daily_gate": daily_gate, "mtf_4h_aligned": mtf_4h_aligned,
            "momentum": momentum, "slope": slope,
        }
    if slope < min_slope:
        return False, {
            "reason": "low_slope", "slope": slope,
            "min_slope": min_slope, "atr_regime_1h": atr_regime_1h,
            "daily_gate": daily_gate, "mtf_4h_aligned": mtf_4h_aligned,
            "momentum": momentum,
        }
    if momentum < min_momentum:
        return False, {
            "reason": "low_momentum", "momentum": momentum,
            "min_momentum": min_momentum, "atr_regime_1h": atr_regime_1h,
            "daily_gate": daily_gate, "mtf_4h_aligned": mtf_4h_aligned,
            "slope": slope,
        }
    if trend_strength < min_trend:
        return False, {
            "reason": "weak_trend", "trend_strength": trend_strength,
            "min_trend": min_trend, "atr_regime_1h": atr_regime_1h,
            "daily_gate": daily_gate, "mtf_4h_aligned": mtf_4h_aligned,
            "momentum": momentum, "slope": slope,
        }
    if mtf_bias_4h < min_mtf_bias:
        return False, {
            "reason": "mtf_bias_too_weak", "mtf_bias_4h": mtf_bias_4h,
            "min_mtf_bias": min_mtf_bias, "atr_regime_1h": atr_regime_1h,
            "daily_gate": daily_gate, "mtf_4h_aligned": mtf_4h_aligned,
            "momentum": momentum, "slope": slope,
        }

    return True, {
        "reason":         "stage1_pass",
        "confidence":     confidence,
        "slope":          slope,
        "momentum":       momentum,
        "trend_strength": trend_strength,
        "mtf_bias_4h":    mtf_bias_4h,
        "atr_regime_1h":  atr_regime_1h,
        "daily_gate":     daily_gate,
        "mtf_4h_aligned": mtf_4h_aligned,
        "min_conf":       min_conf,
        "max_conf":       max_conf,
        "min_slope":      min_slope,
        "min_momentum":   min_momentum,
        "min_trend":      min_trend,
        "min_mtf_bias":   min_mtf_bias,
    }
