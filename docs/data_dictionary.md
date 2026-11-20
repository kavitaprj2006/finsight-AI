# FinSight AI - Data Dictionary

This document details all financial data fields, types, units, and derivation methodologies utilized across FinSight AI.

---

## 1. Market Data Fields

| Field Name | Type | Unit | Description |
|------------|------|------|-------------|
| `Open` | Float | Currency (INR/USD) | Opening price at market session start |
| `High` | Float | Currency (INR/USD) | Highest price traded during session |
| `Low` | Float | Currency (INR/USD) | Lowest price traded during session |
| `Close` | Float | Currency (INR/USD) | Final official closing transaction price |
| `Adj Close`| Float | Currency (INR/USD) | Close adjusted for stock splits and dividends |
| `Volume` | Integer | Share Count | Total number of contracts/shares traded |
| `Daily_Return` | Float | Percentage Ratio | $\frac{\text{Close}_t - \text{Close}_{t-1}}{\text{Close}_{t-1}}$ |
| `Rolling_Vol_21` | Float | Annualized % | $\text{std}(\text{Daily\_Return}_{21}) \times \sqrt{252}$ |

---

## 2. Technical Indicators

| Field Name | Window/Span | Formula / Definition |
|------------|-------------|----------------------|
| `SMA_20` | 20 sessions | Arithmetic moving average of closing price over 20 days |
| `SMA_50` | 50 sessions | Medium-term trend benchmark |
| `SMA_200` | 200 sessions | Long-term institutional bull/bear line |
| `EMA_12` | 12 sessions | Exponential smoothing: $\alpha = \frac{2}{N+1}$ |
| `EMA_26` | 26 sessions | Slow exponential baseline for MACD |
| `RSI_14` | 14 sessions | Wilder's RSI: $100 - \frac{100}{1 + RS}$ |
| `MACD` | 12 / 26 sessions | $\text{EMA}_{12} - \text{EMA}_{26}$ |
| `MACD_Signal`| 9 sessions | 9-period EMA of MACD Line |
| `MACD_Hist` | - | $\text{MACD} - \text{MACD\_Signal}$ |
| `BB_Upper` | 20 sessions | $\text{SMA}_{20} + 2 \times \sigma_{20}$ |
| `BB_Lower` | 20 sessions | $\text{SMA}_{20} - 2 \times \sigma_{20}$ |
| `ATR_14` | 14 sessions | Average True Range across daily highs, lows, and gaps |

---

## 3. Financial Risk Metrics

| Metric | Typical Range | Derivation & Interpretation |
|--------|---------------|-----------------------------|
| `Sharpe Ratio` | 0.0 to 3.0+ | $\frac{R_p - R_f}{\sigma_p}$. Risk-free rate default: 5.0% (0.05). |
| `Sortino Ratio`| 0.0 to 4.0+ | $\frac{R_p - R_f}{\sigma_{\text{downside}}}$. Penalizes only negative deviations below $R_f$. |
| `Max Drawdown` | -100% to 0% | Maximum peak-to-trough equity drop: $\min_t \frac{P_t - \max_{\tau \le t} P_\tau}{\max_{\tau \le t} P_\tau}$. |
| `VaR (95%)` | 0.5% to 5.0% | Historical 95% 1-day Value at Risk (5th percentile negative return). |
| `CVaR (95%)` | 1.0% to 8.0% | Conditional Value at Risk: Average loss in the worst 5% tail. |
| `Beta` | 0.5 to 2.0 | $\frac{\text{Cov}(R_{\text{asset}}, R_{\text{bench}})}{\text{Var}(R_{\text{bench}})}$. Relative market sensitivity. |
