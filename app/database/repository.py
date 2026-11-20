"""
FinSight AI - Database Repository & Data Access Layer
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database.connection import get_db_session
from app.database.models import (
    User, UserPreference, Watchlist, WatchlistItem, StockSymbol,
    MarketDataMetadata, StockFundamental, NewsArticle, SentimentResult,
    PredictionRecord, PortfolioScenario, PortfolioAsset, PaperPortfolio,
    PaperTransaction, PortfolioSnapshot, SavedAlert, AlertEvent,
    MLExperimentMetadata, ModelVersion
)
from app.core.logger import logger

class Repository:
    @staticmethod
    def get_or_create_default_user(username: str = "default_trader", email: str = "trader@finsight.ai") -> User:
        """Retrieves or creates the primary default user."""
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                user = User(username=username, email=email)
                session.add(user)
                session.flush()

                prefs = UserPreference(
                    user_id=user.id,
                    default_market="IN",
                    default_currency="INR",
                    risk_tolerance="Moderate"
                )
                session.add(prefs)
                
                # Create default watchlists
                wl_in = Watchlist(user_id=user.id, name="Indian Large-Cap", market="IN", description="Top Indian Bluechips")
                wl_us = Watchlist(user_id=user.id, name="US Tech Giants", market="US", description="Top US Growth Companies")
                session.add_all([wl_in, wl_us])
                session.flush()

                # Add sample items
                items_in = [
                    WatchlistItem(watchlist_id=wl_in.id, symbol="RELIANCE.NS"),
                    WatchlistItem(watchlist_id=wl_in.id, symbol="TCS.NS"),
                    WatchlistItem(watchlist_id=wl_in.id, symbol="INFY.NS"),
                    WatchlistItem(watchlist_id=wl_in.id, symbol="HDFCBANK.NS"),
                ]
                items_us = [
                    WatchlistItem(watchlist_id=wl_us.id, symbol="AAPL"),
                    WatchlistItem(watchlist_id=wl_us.id, symbol="MSFT"),
                    WatchlistItem(watchlist_id=wl_us.id, symbol="NVDA"),
                ]
                session.add_all(items_in + items_us)
                
                # Create default paper portfolios
                p_in = PaperPortfolio(user_id=user.id, name="Indian Growth Fund", market="IN", currency="INR", initial_cash=1000000.0, available_cash=1000000.0)
                p_us = PaperPortfolio(user_id=user.id, name="US Alpha Strategy", market="US", currency="USD", initial_cash=50000.0, available_cash=50000.0)
                session.add_all([p_in, p_us])

                logger.info(f"Initialized default user '{username}' with starter data.")
            return user

    @staticmethod
    def get_watchlists(user_id: int, market: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            query = session.query(Watchlist).filter(Watchlist.user_id == user_id)
            if market:
                query = query.filter(Watchlist.market == market)
            watchlists = query.all()
            result = []
            for wl in watchlists:
                items = [item.symbol for item in wl.items]
                result.append({
                    "id": wl.id,
                    "name": wl.name,
                    "market": wl.market,
                    "description": wl.description,
                    "symbols": items
                })
            return result

    @staticmethod
    def add_to_watchlist(user_id: int, watchlist_name: str, symbol: str, market: str = "IN") -> bool:
        with get_db_session() as session:
            wl = session.query(Watchlist).filter(
                Watchlist.user_id == user_id,
                Watchlist.name == watchlist_name
            ).first()
            if not wl:
                wl = Watchlist(user_id=user_id, name=watchlist_name, market=market)
                session.add(wl)
                session.flush()

            existing = session.query(WatchlistItem).filter(
                WatchlistItem.watchlist_id == wl.id,
                WatchlistItem.symbol == symbol
            ).first()
            if not existing:
                session.add(WatchlistItem(watchlist_id=wl.id, symbol=symbol))
                return True
            return False

    @staticmethod
    def remove_from_watchlist(user_id: int, watchlist_id: int, symbol: str) -> bool:
        with get_db_session() as session:
            item = session.query(WatchlistItem).join(Watchlist).filter(
                Watchlist.user_id == user_id,
                WatchlistItem.watchlist_id == watchlist_id,
                WatchlistItem.symbol == symbol
            ).first()
            if item:
                session.delete(item)
                return True
            return False

    # Paper Portfolio Management
    @staticmethod
    def get_paper_portfolios(user_id: int, market: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            q = session.query(PaperPortfolio).filter(PaperPortfolio.user_id == user_id)
            if market:
                q = q.filter(PaperPortfolio.market == market)
            portfolios = q.all()
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "market": p.market,
                    "currency": p.currency,
                    "initial_cash": p.initial_cash,
                    "available_cash": p.available_cash,
                    "created_at": p.created_at
                }
                for p in portfolios
            ]

    @staticmethod
    def create_paper_portfolio(user_id: int, name: str, market: str, currency: str, initial_cash: float) -> int:
        with get_db_session() as session:
            p = PaperPortfolio(
                user_id=user_id,
                name=name,
                market=market,
                currency=currency,
                initial_cash=initial_cash,
                available_cash=initial_cash
            )
            session.add(p)
            session.flush()
            return p.id

    @staticmethod
    def record_transaction(portfolio_id: int, symbol: str, tx_type: str, quantity: float, price: float, cost: float = 0.0) -> bool:
        with get_db_session() as session:
            portfolio = session.query(PaperPortfolio).filter(PaperPortfolio.id == portfolio_id).first()
            if not portfolio:
                return False

            total_cost = (quantity * price) + cost
            if tx_type == "BUY":
                if portfolio.available_cash < total_cost:
                    raise ValueError(f"Insufficient funds: available {portfolio.available_cash:.2f}, required {total_cost:.2f}")
                portfolio.available_cash -= total_cost
                realized_pnl = 0.0
            elif tx_type == "SELL":
                # Check current holding
                holdings = Repository.get_portfolio_holdings(portfolio_id)
                current_qty = holdings.get(symbol, {}).get("quantity", 0)
                if current_qty < quantity:
                    raise ValueError(f"Cannot sell {quantity} shares of {symbol}, current holding is {current_qty}")
                
                avg_cost = holdings[symbol]["avg_cost"]
                realized_pnl = (price - avg_cost) * quantity - cost
                portfolio.available_cash += (quantity * price) - cost
            else:
                raise ValueError("Invalid transaction type. Must be BUY or SELL.")

            tx = PaperTransaction(
                portfolio_id=portfolio_id,
                symbol=symbol,
                transaction_type=tx_type,
                quantity=quantity,
                price=price,
                transaction_cost=cost,
                realized_pnl=realized_pnl
            )
            session.add(tx)
            return True

    @staticmethod
    def get_portfolio_holdings(portfolio_id: int) -> Dict[str, Dict[str, float]]:
        """Calculates current holdings from transaction history."""
        with get_db_session() as session:
            txs = session.query(PaperTransaction).filter(
                PaperTransaction.portfolio_id == portfolio_id
            ).order_by(PaperTransaction.executed_at.asc()).all()

            holdings: Dict[str, Dict[str, float]] = {}
            for tx in txs:
                sym = tx.symbol
                if sym not in holdings:
                    holdings[sym] = {"quantity": 0.0, "total_cost": 0.0, "avg_cost": 0.0, "realized_pnl": 0.0}

                if tx.transaction_type == "BUY":
                    holdings[sym]["quantity"] += tx.quantity
                    holdings[sym]["total_cost"] += (tx.quantity * tx.price) + tx.transaction_cost
                    if holdings[sym]["quantity"] > 0:
                        holdings[sym]["avg_cost"] = holdings[sym]["total_cost"] / holdings[sym]["quantity"]
                elif tx.transaction_type == "SELL":
                    holdings[sym]["quantity"] -= tx.quantity
                    holdings[sym]["total_cost"] -= (tx.quantity * holdings[sym]["avg_cost"])
                    holdings[sym]["realized_pnl"] += tx.realized_pnl
                    if holdings[sym]["quantity"] <= 0:
                        holdings[sym]["quantity"] = 0.0
                        holdings[sym]["total_cost"] = 0.0
                        holdings[sym]["avg_cost"] = 0.0

            # Filter out zero-quantity holdings
            return {s: h for s, h in holdings.items() if h["quantity"] > 0}

    @staticmethod
    def get_portfolio_transactions(portfolio_id: int) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            txs = session.query(PaperTransaction).filter(
                PaperTransaction.portfolio_id == portfolio_id
            ).order_by(desc(PaperTransaction.executed_at)).all()
            return [
                {
                    "id": tx.id,
                    "symbol": tx.symbol,
                    "type": tx.transaction_type,
                    "quantity": tx.quantity,
                    "price": tx.price,
                    "cost": tx.transaction_cost,
                    "realized_pnl": tx.realized_pnl,
                    "date": tx.executed_at
                }
                for tx in txs
            ]

    # Smart Alerts
    @staticmethod
    def create_alert(user_id: int, symbol: str, alert_type: str, threshold: float, market: str) -> int:
        with get_db_session() as session:
            alert = SavedAlert(
                user_id=user_id,
                symbol=symbol,
                alert_type=alert_type,
                threshold_value=threshold,
                market=market,
                is_active=True
            )
            session.add(alert)
            session.flush()
            return alert.id

    @staticmethod
    def get_active_alerts(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            q = session.query(SavedAlert).filter(SavedAlert.is_active == True)
            if user_id:
                q = q.filter(SavedAlert.user_id == user_id)
            alerts = q.all()
            return [
                {
                    "id": a.id,
                    "user_id": a.user_id,
                    "symbol": a.symbol,
                    "type": a.alert_type,
                    "threshold": a.threshold_value,
                    "market": a.market,
                    "created_at": a.created_at
                }
                for a in alerts
            ]

    @staticmethod
    def delete_alert(alert_id: int) -> bool:
        with get_db_session() as session:
            alert = session.query(SavedAlert).filter(SavedAlert.id == alert_id).first()
            if alert:
                session.delete(alert)
                return True
            return False

    @staticmethod
    def record_alert_event(alert_id: int, symbol: str, triggered_val: float, threshold_val: float, message: str):
        with get_db_session() as session:
            evt = AlertEvent(
                alert_id=alert_id,
                symbol=symbol,
                triggered_value=triggered_val,
                threshold_value=threshold_val,
                message=message
            )
            session.add(evt)

    @staticmethod
    def get_alert_events(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            evts = session.query(AlertEvent).join(SavedAlert).filter(
                SavedAlert.user_id == user_id
            ).order_by(desc(AlertEvent.triggered_at)).limit(limit).all()
            return [
                {
                    "id": e.id,
                    "symbol": e.symbol,
                    "triggered_value": e.triggered_value,
                    "threshold_value": e.threshold_value,
                    "message": e.message,
                    "triggered_at": e.triggered_at
                }
                for e in evts
            ]

    # Predictions
    @staticmethod
    def record_prediction(symbol: str, market: str, task: str, model_name: str,
                          horizon: int, as_of_price: float, return_pred: Optional[float] = None,
                          direction_pred: Optional[str] = None, prob: Optional[float] = None,
                          version: str = "v1.0", features: Optional[dict] = None):
        with get_db_session() as session:
            rec = PredictionRecord(
                symbol=symbol,
                market=market,
                task_type=task,
                model_name=model_name,
                horizon_days=horizon,
                predicted_return=return_pred,
                predicted_direction=direction_pred,
                prediction_probability=prob,
                as_of_price=as_of_price,
                model_version=version,
                features_used=features
            )
            session.add(rec)

    @staticmethod
    def get_recent_predictions(symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            q = session.query(PredictionRecord)
            if symbol:
                q = q.filter(PredictionRecord.symbol == symbol)
            records = q.order_by(desc(PredictionRecord.created_at)).limit(limit).all()
            return [
                {
                    "symbol": r.symbol,
                    "market": r.market,
                    "task": r.task_type,
                    "model": r.model_name,
                    "horizon": r.horizon_days,
                    "predicted_return": r.predicted_return,
                    "predicted_direction": r.predicted_direction,
                    "probability": r.prediction_probability,
                    "as_of_price": r.as_of_price,
                    "version": r.model_version,
                    "created_at": r.created_at
                }
                for r in records
            ]

    # Portfolio Scenarios
    @staticmethod
    def save_portfolio_scenario(user_id: int, name: str, strategy: str, scenario_type: str,
                                market: str, currency: str, budget: float, exp_return: float,
                                exp_vol: float, sharpe: float, sortino: float,
                                assets: List[Dict[str, Any]]) -> int:
        with get_db_session() as session:
            sc = PortfolioScenario(
                user_id=user_id,
                name=name,
                strategy_type=strategy,
                scenario_type=scenario_type,
                market=market,
                currency=currency,
                budget=budget,
                expected_return=exp_return,
                expected_volatility=exp_vol,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino
            )
            session.add(sc)
            session.flush()

            for a in assets:
                asset_obj = PortfolioAsset(
                    scenario_id=sc.id,
                    symbol=a["symbol"],
                    weight=a["weight"],
                    allocated_amount=a.get("allocated_amount", budget * a["weight"]),
                    shares=a.get("shares", 0.0)
                )
                session.add(asset_obj)
            return sc.id

    @staticmethod
    def get_saved_scenarios(user_id: int) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            scenarios = session.query(PortfolioScenario).filter(
                PortfolioScenario.user_id == user_id
            ).order_by(desc(PortfolioScenario.created_at)).all()
            res = []
            for s in scenarios:
                res.append({
                    "id": s.id,
                    "name": s.name,
                    "strategy": s.strategy_type,
                    "scenario_type": s.scenario_type,
                    "budget": s.budget,
                    "expected_return": s.expected_return,
                    "expected_volatility": s.expected_volatility,
                    "sharpe_ratio": s.sharpe_ratio,
                    "created_at": s.created_at,
                    "assets": [{"symbol": a.symbol, "weight": a.weight, "allocated_amount": a.allocated_amount} for a in s.assets]
                })
            return res

    # ML Experiments & Registry
    @staticmethod
    def record_ml_experiment(experiment_name: str, run_id: str, model_name: str,
                              task_type: str, market: str, symbol: Optional[str],
                              parameters: Dict[str, Any], metrics: Dict[str, float],
                              artifact_uri: Optional[str] = None):
        with get_db_session() as session:
            exp = MLExperimentMetadata(
                experiment_name=experiment_name,
                run_id=run_id,
                model_name=model_name,
                task_type=task_type,
                market=market,
                symbol=symbol,
                parameters=parameters,
                metrics=metrics,
                artifact_uri=artifact_uri
            )
            session.add(exp)

    @staticmethod
    def get_ml_experiments(limit: int = 50) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            exps = session.query(MLExperimentMetadata).order_by(
                desc(MLExperimentMetadata.created_at)
            ).limit(limit).all()
            return [
                {
                    "id": e.id,
                    "experiment": e.experiment_name,
                    "run_id": e.run_id,
                    "model_name": e.model_name,
                    "task_type": e.task_type,
                    "market": e.market,
                    "symbol": e.symbol,
                    "parameters": e.parameters or {},
                    "metrics": e.metrics or {},
                    "created_at": e.created_at
                }
                for e in exps
            ]

    @staticmethod
    def save_model_version(model_name: str, version: str, task_type: str, score: float, metric_name: str, filepath: str):
        with get_db_session() as session:
            mv = session.query(ModelVersion).filter(
                ModelVersion.model_name == model_name,
                ModelVersion.version == version
            ).first()
            if not mv:
                mv = ModelVersion(
                    model_name=model_name,
                    version=version,
                    task_type=task_type,
                    evaluation_score=score,
                    metric_name=metric_name,
                    filepath=filepath,
                    is_active=True
                )
                session.add(mv)
            else:
                mv.evaluation_score = score
                mv.metric_name = metric_name
                mv.filepath = filepath

    @staticmethod
    def get_model_versions() -> List[Dict[str, Any]]:
        with get_db_session() as session:
            mvs = session.query(ModelVersion).order_by(desc(ModelVersion.created_at)).all()
            return [
                {
                    "model_name": m.model_name,
                    "version": m.version,
                    "task_type": m.task_type,
                    "score": m.evaluation_score,
                    "metric_name": m.metric_name,
                    "is_active": m.is_active,
                    "filepath": m.filepath,
                    "created_at": m.created_at
                }
                for m in mvs
            ]

    @staticmethod
    def seed_stock_symbols():
        from app.core.constants import DEFAULT_SYMBOLS
        with get_db_session() as session:
            for market, syms in DEFAULT_SYMBOLS.items():
                for s in syms:
                    existing = session.query(StockSymbol).filter(StockSymbol.symbol == s["symbol"]).first()
                    if not existing:
                        curr = "INR" if market == "IN" else "USD"
                        stock = StockSymbol(
                            symbol=s["symbol"],
                            name=s["name"],
                            market=market,
                            exchange=s["exchange"],
                            sector=s.get("sector", "General"),
                            currency=curr,
                            is_active=True
                        )
                        session.add(stock)


