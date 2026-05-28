# ================================================================
# File: tests/integration/test_websocket.py
# LiveLoop WebSocket integration tests (8 total)
# Tests: candle parsing, engine dispatch, error handling.
# ================================================================
import json
import pytest
from unittest.mock import MagicMock
from src.stubs.live_loop_stub import LiveLoop, parse_ws_message


def _make_kline(closed=True, t=1700000000000, o=100.0, h=105.0, l=99.0, c=103.0, v=500.0):
    return json.dumps({
        "e": "kline",
        "k": {
            "t": t, "o": str(o), "h": str(h),
            "l": str(l), "c": str(c), "v": str(v),
            "x": closed,
        }
    })


def _make_loop():
    engine = MagicMock()
    loop   = LiveLoop(engine=engine, symbol="BTCUSDT")
    return loop, engine


class TestParseWsMessage:
    def test_closed_candle_returns_dict(self):
        candle = parse_ws_message(_make_kline(closed=True))
        assert candle is not None
        assert candle["close"] == 103.0

    def test_open_candle_returns_none(self):
        candle = parse_ws_message(_make_kline(closed=False))
        assert candle is None

    def test_invalid_json_returns_none(self):
        candle = parse_ws_message("not-json{{")
        assert candle is None

    def test_candle_fields_are_correct_types(self):
        candle = parse_ws_message(_make_kline())
        assert isinstance(candle["timestamp"], int)
        assert isinstance(candle["open"],      float)
        assert isinstance(candle["high"],      float)
        assert isinstance(candle["low"],       float)
        assert isinstance(candle["close"],     float)
        assert isinstance(candle["volume"],    float)


class TestLiveLoopOnMessage:
    def test_closed_candle_calls_engine(self):
        loop, engine = _make_loop()
        loop._on_message(None, _make_kline(closed=True))
        engine.on_candle.assert_called_once()
        args = engine.on_candle.call_args[0]
        assert args[0] == "BTCUSDT"
        assert args[1]["close"] == 103.0

    def test_open_candle_does_not_call_engine(self):
        loop, engine = _make_loop()
        loop._on_message(None, _make_kline(closed=False))
        engine.on_candle.assert_not_called()

    def test_candle_count_increments_on_closed(self):
        loop, engine = _make_loop()
        loop._on_message(None, _make_kline(closed=True))
        loop._on_message(None, _make_kline(closed=True))
        loop._on_message(None, _make_kline(closed=False))
        assert loop._candle_count == 2

    def test_engine_exception_is_captured_not_raised(self):
        loop, engine = _make_loop()
        engine.on_candle.side_effect = RuntimeError("engine crash")
        loop._on_message(None, _make_kline(closed=True))
        assert len(loop._errors) == 1
        assert "engine crash" in loop._errors[0]
