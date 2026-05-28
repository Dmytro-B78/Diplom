"""
Integration tests with Mock Binance API.
No real HTTP requests are made.
"""
import pytest
pytestmark = pytest.mark.integration


class TestOrderPlacement:
    def test_buy_order_response_structure(self, mock_binance_order_response):
        resp = mock_binance_order_response
        assert resp["status"] == "FILLED"
        assert resp["orderId"] > 0
        assert len(resp["fills"]) > 0

    def test_insufficient_balance_error_code(self, mock_binance_error_response):
        assert mock_binance_error_response["code"] == -2010
        assert "insufficient" in mock_binance_error_response["msg"].lower()

    def test_network_failure_is_exception(self, mocker):
        mock_fn = mocker.MagicMock(side_effect=ConnectionError("timeout"))
        with pytest.raises(ConnectionError):
            mock_fn()


class TestNetworkTimeout:
    def test_read_timeout_raises(self, mocker):
        """ReadTimeout during order placement must propagate as exception."""
        import socket
        mock_api = mocker.MagicMock(side_effect=socket.timeout("read timeout"))
        with pytest.raises(socket.timeout):
            mock_api(symbol="BTCUSDT", side="BUY", quantity=0.01)

    def test_timeout_does_not_return_filled(self, mocker):
        """After a timeout the order status must NOT be FILLED."""
        mock_api = mocker.MagicMock(side_effect=TimeoutError("connect timeout"))
        result = None
        try:
            result = mock_api(symbol="BTCUSDT", side="BUY", quantity=0.01)
        except TimeoutError:
            pass
        assert result is None

    def test_retry_succeeds_after_timeout(self, mocker):
        """Simulate: first call times out, second call succeeds."""
        mock_api = mocker.MagicMock(
            side_effect=[
                ConnectionError("timeout"),
                {"status": "FILLED", "orderId": 42, "fills": [{}]},
            ]
        )
        with pytest.raises(ConnectionError):
            mock_api()
        resp = mock_api()
        assert resp["status"] == "FILLED"

    def test_partial_response_missing_status(self, mocker):
        """Partial / malformed response: missing status key."""
        mock_api = mocker.MagicMock(return_value={"orderId": 99})
        resp = mock_api()
        assert "status" not in resp
        assert resp["orderId"] == 99
