import pandas as pd
import numpy as np
from datetime import datetime
import os

# Prototype/proxy data for demonstration. Not proprietary SAIL data.

def generate_synthetic_freight_data():
    np.random.seed(42)

    # Define realistic lanes
    lanes = [
        ("Australia", "Paradip", ["Handysize", "Supramax", "Panamax", "Capesize"]),
        ("Australia", "Visakhapatnam", ["Handysize", "Supramax", "Panamax", "Capesize"]),
        ("Indonesia", "Dhamra", ["Handysize", "Supramax", "Panamax"]),
        ("Indonesia", "Paradip", ["Handysize", "Supramax", "Panamax", "Capesize"]),
        ("USA", "Haldia", ["Supramax", "Panamax", "Capesize"]),
        ("Mozambique", "Gangavaram", ["Handysize", "Supramax", "Panamax"]),
        ("Russia", "Paradip", ["Supramax", "Panamax", "Capesize"])
    ]

    dates = pd.date_range(start='2022-01-01', end='2026-08-01', freq='MS')
    
    base_rates = {"Handysize": 17.5, "Supramax": 21.5, "Panamax": 27.0, "Capesize": 15.0}
    vessel_volatility = {"Handysize": 0.05, "Supramax": 0.08, "Panamax": 0.12, "Capesize": 0.18}
    origin_premiums = {"Australia": 0.0, "Indonesia": -2.0, "USA": 3.0, "Mozambique": 1.0, "Russia": 2.0}

    data = []

    for date in dates:
        # t is months since Jan 2022
        t = (date.year - 2022) * 12 + date.month - 1
        
        # Trend: upward 22-24, dip mid-24, recovery 25-26
        if t < 30: # Jan 2022 to Jun 2024
            trend = t * 0.15
        elif t < 36: # Jul 2024 to Dec 2024 dip
            trend = 30 * 0.15 - (t - 30) * 0.5
        else: # 2025 onwards
            trend = 30 * 0.15 - 6 * 0.5 + (t - 36) * 0.2

        # Seasonality: higher Q4 & Q1, lower Q2-Q3. Using a simple shifted cosine
        month = date.month
        # Peak around Dec/Jan, trough around Jun/Jul
        seasonality = np.cos(2 * np.pi * (month - 1) / 12) * 2.5
        
        # Shocks
        shock = 0
        if date.year == 2023 and date.month in [7, 8, 9]:
            shock = 4.5
        elif date.year == 2024 and date.month in [1, 2]:
            shock = -3.5

        # Global base components
        bunker = 600 + trend * 10 + np.random.normal(0, 15)
        commodity = 110 + trend * 1.5 + np.random.normal(0, 3)
        
        # Monsoon congestion (higher in Jul-Sep for India)
        monsoon = 1.0 if month in [7, 8, 9] else 0.0
        congestion = 1.0 + monsoon * 0.4 + np.random.normal(0, 0.05)

        for origin, destination, vessel_types in lanes:
            for vessel in vessel_types:
                base = base_rates[vessel]
                premium = origin_premiums[origin]
                volatility = vessel_volatility[vessel]
                
                noise = np.random.normal(0, base * volatility)
                
                freight_rate = base + premium + trend + seasonality + shock + noise
                
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "origin": origin,
                    "destination": destination,
                    "vessel_type": vessel,
                    "freight_rate": round(max(5.0, freight_rate), 2),
                    "bunker_price": round(bunker, 2),
                    "commodity_index": round(commodity, 2),
                    "congestion_index": round(congestion, 2),
                    "seasonal_index": round(seasonality, 2)
                })

    df = pd.DataFrame(data)
    
    output_path = r"N:\VARUNEETI\backend\data\freight.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Generated prototype freight data at {output_path}")
    print(f"Shape: {df.shape}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nSummary Statistics:")
    print(df.describe())

if __name__ == "__main__":
    generate_synthetic_freight_data()
