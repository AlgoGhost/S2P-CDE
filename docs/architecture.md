# VARUNEETI Forecasting Architecture

> **Note**: This system uses prototype/proxy data for demonstration purposes. Not proprietary SAIL data.

## System Components

1. **Data Layer**
   - Implements a Data Adapter Pattern (`PrototypeFreightDataAdapter`).
   - Retrieves historical freight data, bunkers, and commodity indices.
   - Designed to easily swap out synthetic prototype data for actual Baltic Exchange / SAIL licensed data in production.

2. **Forecast Engine**
   - Time Series Processing & Feature Engineering.
   - Model Hierarchy:
     1. **SARIMAX Model**: Primary model using exogenous variables (bunkers, seasonality).
     2. **Simple Statistical**: Secondary fallback for sparse lanes.
     3. **NaiveBaseline (Persistence)**: Ultimate fallback model.
   - Evaluates performance using walk-forward validation.
   - Calculates uncertainty quantification and prediction intervals.

3. **API Service (Clean Service Interface Pattern)**
   - Exposes prediction endpoints.
   - Handles parameter validation and route mapping.
   - Aggregates outputs from the Forecast Engine into JSON responses containing point estimates and confidence intervals.
