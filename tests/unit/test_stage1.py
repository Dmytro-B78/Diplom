# ================================================================
# File: tests/unit/test_stage1.py
# Stage1-Lite v4.6 — unit tests (23 total)
# Covers: hard gate, 6 reject reasons, 3 ATR regimes,
#         daily_gate tightening, return structure, edge cases.
# ================================================================
import pytest
from src.stubs.stage1_stub import stage1_check


BASE_PASS = {
    "mtf_4h_aligned": True,
    "daily_gate":     True,
    "atr_regime_1h":  "normal",
    "confidence":     0.30,
    "slope":          0.05,
    "momentum":       0.15,
    "trend_strength": 0.20,
    "mtf_bias_4h":    0.20,
}


def _state(**overrides):
    return {**BASE_PASS, **overrides}


class TestHardGate:
    def test_4h_not_aligned_blocks_entry(self):
        passed, info = stage1_check(_state(mtf_4h_aligned=False))
        assert passed is False
        assert info["reason"] == "4h_not_aligned"

    def test_4h_aligned_allows_entry(self):
        passed, info = stage1_check(BASE_PASS)
        assert passed is True
        assert info["reason"] == "stage1_pass"


REJECT_CASES = [
    ("confidence",      0.05,  "low_confidence"),
    ("confidence",      0.70,  "confidence_ceiling"),
    ("slope",           0.005, "low_slope"),
    ("momentum",       -0.05,  "low_momentum"),
    ("trend_strength",  0.05,  "weak_trend"),
    ("mtf_bias_4h",     0.05,  "mtf_bias_too_weak"),
]


class TestRejectReasonsNormalRegime:
    @pytest.mark.parametrize("field,value,reason", REJECT_CASES)
    def test_reject(self, field, value, reason):
        passed, info = stage1_check(_state(**{field: value}))
        assert passed is False
        assert info["reason"] == reason


REGIME_PASS_CASES = [
    ("normal", 0.30, 0.05, 0.15, 0.20, 0.20),
    ("high",   0.20, 0.05, 0.30, 0.30, 0.50),
    ("low",    0.03, 0.02, 0.00, 0.10, 0.05),
]


class TestPassAllRegimes:
    @pytest.mark.parametrize(
        "regime,conf,slope,momentum,trend,bias", REGIME_PASS_CASES
    )
    def test_pass(self, regime, conf, slope, momentum, trend, bias):
        state = _state(
            atr_regime_1h=regime,
            confidence=conf, slope=slope, momentum=momentum,
            trend_strength=trend, mtf_bias_4h=bias,
        )
        passed, info = stage1_check(state)
        assert passed is True
        assert info["reason"] == "stage1_pass"


class TestDailyGate:
    def test_daily_gate_false_raises_min_momentum(self):
        passed, info = stage1_check(_state(daily_gate=False, momentum=0.15))
        assert passed is False
        assert info["reason"] == "low_momentum"

    def test_daily_gate_false_raises_min_slope(self):
        passed, info = stage1_check(
            _state(daily_gate=False, slope=0.02, momentum=0.35)
        )
        assert passed is False
        assert info["reason"] == "low_slope"

    def test_daily_gate_false_passes_with_sufficient_values(self):
        passed, info = stage1_check(
            _state(daily_gate=False, momentum=0.35, slope=0.06)
        )
        assert passed is True
        assert info["reason"] == "stage1_pass"


class TestReturnStructure:
    def test_pass_result_contains_all_keys(self):
        _, info = stage1_check(BASE_PASS)
        for key in (
            "reason", "confidence", "slope", "momentum",
            "trend_strength", "mtf_bias_4h", "atr_regime_1h",
            "daily_gate", "mtf_4h_aligned",
        ):
            assert key in info, f"Missing key: {key}"

    def test_fail_result_contains_reason(self):
        _, info = stage1_check(_state(mtf_4h_aligned=False))
        assert "reason" in info


class TestHighRegimeThresholds:
    def _high(self, **kw):
        base = dict(
            atr_regime_1h="high",
            confidence=0.20, slope=0.05, momentum=0.30,
            trend_strength=0.30, mtf_bias_4h=0.50,
        )
        base.update(kw)
        return _state(**base)

    def test_high_regime_rejects_weak_mtf_bias(self):
        passed, info = stage1_check(self._high(mtf_bias_4h=0.30))
        assert passed is False
        assert info["reason"] == "mtf_bias_too_weak"

    def test_high_regime_rejects_low_momentum(self):
        passed, info = stage1_check(self._high(momentum=0.15))
        assert passed is False
        assert info["reason"] == "low_momentum"

    def test_high_regime_rejects_weak_trend(self):
        passed, info = stage1_check(self._high(trend_strength=0.20))
        assert passed is False
        assert info["reason"] == "weak_trend"

    def test_high_regime_rejects_low_slope(self):
        passed, info = stage1_check(self._high(slope=0.02))
        assert passed is False
        assert info["reason"] == "low_slope"


class TestEdgeCases:
    def test_confidence_exactly_at_min_conf_passes(self):
        passed, _ = stage1_check(_state(confidence=0.10))
        assert passed is True

    def test_confidence_exactly_at_max_conf_passes(self):
        passed, _ = stage1_check(_state(confidence=0.65))
        assert passed is True

    def test_minimal_state_defaults_to_low_confidence(self):
        passed, info = stage1_check({"mtf_4h_aligned": True})
        assert passed is False
        assert info["reason"] == "low_confidence"
