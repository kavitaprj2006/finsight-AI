# FinSight AI - Relational Database Schema Documentation

FinSight AI employs a normalized relational database design compatible with **PostgreSQL** and local **SQLite**.

---

## Entity Relationship Overview

| Table Name | Primary Key | Foreign Keys | Purpose |
|------------|-------------|--------------|---------|
| `users` | `id` | - | Platform user accounts & identification |
| `user_preferences` | `id` | `user_id` -> `users.id` | User default market, currency, risk tolerance |
| `stock_symbols` | `id` | - | Active market universe directory (NSE, BSE, NYSE, NASDAQ) |
| `market_data_metadata` | `id` | - | Data provenance, caching state, staleness & provider tracking |
| `stock_fundamentals` | `id` | - | Valuation metrics, balance sheets & income statements |
| `news_articles` | `id` | - | Financial headlines and publication metadata |
| `sentiment_results` | `id` | `article_id` -> `news_articles.id` | NLP sentiment score & confidence breakdown |
| `prediction_records` | `id` | - | Logged regression and classification inferences |
| `portfolio_scenarios` | `id` | `user_id` -> `users.id` | User-saved educational allocation scenarios |
| `portfolio_assets` | `id` | `scenario_id` -> `portfolio_scenarios.id` | Individual asset weights and capital allocations |
| `paper_portfolios` | `id` | `user_id` -> `users.id` | Persistent simulated investment portfolios |
| `paper_transactions` | `id` | `portfolio_id` -> `paper_portfolios.id` | Simulated buy/sell execution ledger with P&L |
| `portfolio_snapshots` | `id` | `portfolio_id` -> `paper_portfolios.id` | Historical daily NAV and P&L snapshots |
| `saved_alerts` | `id` | `user_id` -> `users.id` | User-configured price, vol, and drawdown triggers |
| `alert_events` | `id` | `alert_id` -> `saved_alerts.id` | Historical trigger events and breach records |
| `watchlists` | `id` | `user_id` -> `users.id` | Custom user-created ticker watchlists |
| `watchlist_items` | `id` | `watchlist_id` -> `watchlists.id` | Tickers belonging to specific watchlists |
| `ml_experiments_metadata`| `id` | - | MLflow-synced run hyperparameters & metrics |
| `model_versions` | `id` | - | Active registered production model versions |

---

## Constraints and Indexes
- **Cascade Deletes**: Child tables (`watchlist_items`, `paper_transactions`, `portfolio_assets`, `alert_events`) cascade delete upon parent record deletion.
- **Unique Constraints**:
  - `(user_id, name)` on `watchlists`
  - `(watchlist_id, symbol)` on `watchlist_items`
  - `(user_id, name)` on `paper_portfolios`
  - `(symbol, fiscal_date, period)` on `stock_fundamentals`
- **Indexes**:
  - `symbol` and `market` indexed across price, fundamentals, predictions, and alerts.
  - `published_at` indexed on news articles for timeline retrieval.
  - `executed_at` indexed on paper transactions for portfolio accounting.
