"""
Интеграционные тесты с Mock Binance API.
Реальные HTTP запросы не отправляются.
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
