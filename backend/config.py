"""
VARUNEETI Configuration
Maritime Charter Decision Intelligence Engine

All application-wide constants, paths, and domain configuration.
"""

import os
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

FREIGHT_CSV = DATA_DIR / "freight.csv"
VESSELS_CSV = DATA_DIR / "vessels.csv"
PORTS_CSV = DATA_DIR / "ports.csv"
ROUTES_CSV = DATA_DIR / "routes.csv"
MARKET_CSV = DATA_DIR / "market.csv"

# ─── Application ─────────────────────────────────────────────────────────────

APP_NAME = "VARUNEETI"
APP_VERSION = "0.2.0"
APP_DESCRIPTION = "Maritime Charter Decision Intelligence Engine"

# ─── Domain Constants ────────────────────────────────────────────────────────

ORIGINS = ["Australia", "USA", "Mozambique", "Russia", "Indonesia"]

DESTINATIONS = [
    "Paradip",
    "Visakhapatnam",
    "Gangavaram",
    "Gopalpur",
    "Dhamra",
    "Haldia",
    "Sagar-Sandheads",
]

VESSEL_CLASSES = ["Handysize", "Supramax", "Panamax", "Capesize"]

CHARTER_STRATEGIES = ["SPOT", "SHORT_TERM", "MEDIUM_TERM", "HYBRID"]

# ─── Forecasting Configuration ──────────────────────────────────────────────

# Supported forecast horizons (days)
SUPPORTED_HORIZONS = [7, 14, 30, 60, 90]

# Minimum observations required for SARIMAX
SARIMAX_MIN_OBSERVATIONS = 24

# Minimum observations for any forecast
ABSOLUTE_MIN_OBSERVATIONS = 6

# SARIMAX default order (p, d, q)
SARIMAX_ORDER = (1, 1, 1)

# SARIMAX seasonal order (P, D, Q, s) — s=12 for monthly data
SARIMAX_SEASONAL_ORDER = (1, 0, 1, 12)

# Confidence interval (prediction interval) level
FORECAST_CONFIDENCE_LEVEL = 0.95

# ─── Trend Thresholds ────────────────────────────────────────────────────────
# Percentage change in forecast trajectory to classify as RISING/FALLING
# Below this threshold → STABLE
TREND_THRESHOLD_PCT = 2.0  # percent

# ─── Volatility Thresholds ───────────────────────────────────────────────────
# Based on coefficient of variation (CV = std/mean) of recent observations
VOLATILITY_LOW_THRESHOLD = 0.05   # CV < 5% → LOW
VOLATILITY_HIGH_THRESHOLD = 0.15  # CV > 15% → HIGH, else MEDIUM

# ─── Confidence Score Weights ────────────────────────────────────────────────
# Weights for composite confidence score components
CONFIDENCE_WEIGHT_VALIDATION = 0.35
CONFIDENCE_WEIGHT_DATA_AMOUNT = 0.25
CONFIDENCE_WEIGHT_HORIZON = 0.20
CONFIDENCE_WEIGHT_VOLATILITY = 0.20

# ─── CORS Configuration ─────────────────────────────────────────────────────

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# ─── Data Source Metadata ────────────────────────────────────────────────────

DATA_SOURCE_LABEL = "prototype_proxy"
DATA_DISCLAIMER = (
    "Prototype/proxy data for demonstration. "
    "Not proprietary SAIL data."
)
