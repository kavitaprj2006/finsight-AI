"""
FinSight AI - Smart Alerts Service
Evaluates price, volatility, and drawdown thresholds on data refresh.
"""
from typing import List, Dict, Any
from app.database.repository import Repository
from app.data_providers.factory import get_market_data_provider
from app.analytics.technical_indicators import compute_all_indicators
from app.analytics.risk_metrics import calculate_drawdown
from app.core.constants import (
    ALERT_PRICE_ABOVE, ALERT_PRICE_BELOW, ALERT_VOLATILITY_ABOVE, ALERT_DRAWDOWN_EXCEEDED
)
from app.core.logger import logger

class AlertService:
    def __init__(self):
        self.provider = get_market_data_provider()

    def evaluate_active_alerts(self, user_id: int = 1) -> List[Dict[str, Any]]:
        """
        Evaluates active configured alerts and records alert events upon breach.
        """
        alerts = Repository.get_active_alerts(user_id=user_id)
        triggered_events = []

        for a in alerts:
            sym = a["symbol"]
            mkt = a["market"]
            a_type = a["type"]
            threshold = a["threshold"]

            try:
                # Price threshold alerts
                if a_type in (ALERT_PRICE_ABOVE, ALERT_PRICE_BELOW):
                    q_resp = self.provider.get_quote(sym, mkt)
                    if not q_resp.is_success or q_resp.data is None:
                        continue
                    current_price = q_resp.data.price

                    if a_type == ALERT_PRICE_ABOVE and current_price >= threshold:
                        msg = f"Price target reached: {sym} traded at {current_price:.2f} (above {threshold:.2f})"
                        Repository.record_alert_event(a["id"], sym, current_price, threshold, msg)
                        triggered_events.append({"alert_id": a["id"], "symbol": sym, "message": msg, "value": current_price})

                    elif a_type == ALERT_PRICE_BELOW and current_price <= threshold:
                        msg = f"Stop trigger hit: {sym} dipped to {current_price:.2f} (below {threshold:.2f})"
                        Repository.record_alert_event(a["id"], sym, current_price, threshold, msg)
                        triggered_events.append({"alert_id": a["id"], "symbol": sym, "message": msg, "value": current_price})

                # Volatility threshold alert
                elif a_type == ALERT_VOLATILITY_ABOVE:
                    hist_resp = self.provider.get_historical_ohlcv(sym, mkt)
                    if hist_resp.is_success and hist_resp.data is not None and len(hist_resp.data) > 25:
                        df_ind = compute_all_indicators(hist_resp.data)
                        curr_vol = float(df_ind["Rolling_Vol_21"].iloc[-1] * 100.0)
                        if curr_vol >= threshold:
                            msg = f"Volatility spike: {sym} 21-day annualized vol at {curr_vol:.1f}% (above {threshold:.1f}%)"
                            Repository.record_alert_event(a["id"], sym, curr_vol, threshold, msg)
                            triggered_events.append({"alert_id": a["id"], "symbol": sym, "message": msg, "value": curr_vol})

                # Drawdown alert
                elif a_type == ALERT_DRAWDOWN_EXCEEDED:
                    hist_resp = self.provider.get_historical_ohlcv(sym, mkt)
                    if hist_resp.is_success and hist_resp.data is not None and len(hist_resp.data) > 10:
                        dd_info = calculate_drawdown(hist_resp.data["Close"])
                        curr_dd = abs(float(dd_info["drawdown_series"].iloc[-1] * 100.0))
                        if curr_dd >= threshold:
                            msg = f"Drawdown threshold exceeded: {sym} drawdown is {curr_dd:.1f}% (limit {threshold:.1f}%)"
                            Repository.record_alert_event(a["id"], sym, curr_dd, threshold, msg)
                            triggered_events.append({"alert_id": a["id"], "symbol": sym, "message": msg, "value": curr_dd})

            except Exception as e:
                logger.error(f"Error evaluating alert {a['id']} for {sym}: {e}")

        return triggered_events

alert_service = AlertService()
