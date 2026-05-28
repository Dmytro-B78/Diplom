# ================================================================
# File: src/stubs/live_loop_stub.py
# Stub: NT-Tech WebSocket Live Loop 2.1
# Source: bot_ai/engine/live_loop.py
#
# Extracted: LiveLoop._on_message logic only.
# Removed: websocket-client, dotenv, LiveEngine, paths imports.
# Purpose: test candle parsing + engine dispatch in isolation.
# ================================================================
import json


def parse_ws_message(message):
    try:
        data = json.loads(message)
    except Exception:
        return None

    k = data.get("k")
    if k is None or not k.get("x", False):
        return None

    return {
        "timestamp": int(k["t"]),
        "open":      float(k["o"]),
        "high":      float(k["h"]),
        "low":       float(k["l"]),
        "close":     float(k["c"]),
        "volume":    float(k["v"]),
    }


class LiveLoop:
    def __init__(self, engine, symbol="SOLUSDT"):
        self.engine        = engine
        self.symbol        = symbol
        self._candle_count = 0
        self._errors       = []

    def _on_message(self, ws, message):
        candle = parse_ws_message(message)
        if candle is None:
            return

        self._candle_count += 1
        try:
            self.engine.on_candle(self.symbol, candle)
        except Exception as e:
            self._errors.append(str(e))

    def _on_error(self, ws, error):
        self._errors.append(str(error))

    def _on_open(self, ws):
        pass

    def _on_close(self, ws, code, msg):
        pass
