# Data Sources

**IMPORTANT DISCLAIMER**: The current data utilized in this repository is purely synthetic prototype/proxy data generated for demonstration and testing purposes. **IT IS NOT PROPRIETARY SAIL DATA**, nor is it official Baltic Exchange market data.

## 1. Current Source (Prototype)
- **Generation Method**: A programmatic python script (`backend/data/generate_data.py`).
- **Features included**: Date, Origin, Destination, Vessel Type, Freight Rate, Bunker Price, Commodity Index, Congestion Index, Seasonal Index.
- **Characteristics**: Contains simulated trends, seasonality, volatility, and artificial shocks to validate forecasting model robustness.

## 2. Future Sources (Production)
Upon deployment, the system is designed to integrate with:
- **Licensed Baltic Exchange APIs**: For actual daily/weekly market rates.
- **SAIL Procurement Data**: For historical internal freight cost analysis.

## 3. Data Adapter Interface
- A standardized Data Adapter Interface is implemented.
- Switching from `PrototypeFreightDataAdapter` to an `OfficialMarketDataAdapter` requires zero changes to the core forecasting logic.
