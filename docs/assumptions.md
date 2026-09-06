# Modeling Assumptions & Configuration

> **Note**: This system currently relies on prototype/proxy data for demonstration. Not proprietary SAIL data.

## 1. Prototype Data Limitations
- All freight rates, bunker prices, and indices are synthetically generated for demonstration.
- Simulated shocks and trends are arbitrary and used strictly to validate the forecasting engine's responsiveness.

## 2. Temporal Assumptions
- **Monthly Granularity**: Forecasts are generated at a month-start level.
- **Seasonality**: Shipping demand is assumed to peak in Q1 and Q4, and drop in Q2 and Q3 (simulated using sinusoidal patterns).

## 3. Walk-forward Validation Splits
- Training uses an expanding window approach.
- Ratios typically rely on an 80/20 train/test split of the available 56 months of historical proxy data.

## 4. SARIMAX Parameter Choices
- p, d, q parameters are determined through automated grid search bounded by reasonable limits (max p=3, max q=3).
- Exogenous variables (Bunkers, Commodity Index) are assumed to have a linear relationship with freight rates over the forecast horizon.

## 5. Confidence Score Methodology
- Evaluated based on historical RMSE of the lane.
- Uncertainty intervals are derived from the model's standard error of prediction.
- High volatility lanes (e.g., Capesize vessels) naturally widen the confidence intervals.
