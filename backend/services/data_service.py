"""
VARUNEETI Data Service
=======================

Provides a data abstraction layer with a clean adapter interface.

Current implementation: PrototypeFreightDataAdapter
    Loads from local CSV files (prototype/proxy data).

Future implementations can include:
    SAILFreightDataAdapter — for licensed SAIL procurement data
    LicensedMarketDataAdapter — for Baltic Exchange or similar feeds

The forecasting engine consumes a standard pandas DataFrame regardless
of the underlying data source.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import pandas as pd

from backend.config import DATA_DIR, DATA_DISCLAIMER, DATA_SOURCE_LABEL, FREIGHT_CSV

logger = logging.getLogger(__name__)


# ─── Abstract Data Adapter ──────────────────────────────────────────────────


class FreightDataAdapter(ABC):
    """
    Abstract interface for freight data sources.

    Any adapter must implement get_freight_data() returning a DataFrame
    with the standard schema:
        date, origin, destination, vessel_type, freight_rate,
        bunker_price, commodity_index, congestion_index, seasonal_index
    """

    @abstractmethod
    def get_freight_data(self) -> pd.DataFrame:
        """Return the full freight dataset."""
        ...

    @abstractmethod
    def get_lane_data(
        self, origin: str, destination: str, vessel_type: str
    ) -> pd.DataFrame:
        """Return data filtered for a specific shipping lane + vessel type."""
        ...

    @abstractmethod
    def get_available_lanes(self) -> list[dict]:
        """Return list of available (origin, destination, vessel_type) combinations."""
        ...

    @property
    @abstractmethod
    def source_label(self) -> str:
        """Human-readable label for the data source."""
        ...

    @property
    @abstractmethod
    def disclaimer(self) -> str:
        """Data provenance disclaimer."""
        ...


# ─── Prototype Adapter ──────────────────────────────────────────────────────


class PrototypeFreightDataAdapter(FreightDataAdapter):
    """
    Loads freight data from a local CSV file.

    This adapter uses PROTOTYPE/PROXY data generated for demonstration
    purposes. It is NOT proprietary SAIL data.
    """

    def __init__(self, csv_path: Path | str | None = None) -> None:
        self._csv_path = Path(csv_path) if csv_path else FREIGHT_CSV
        self._data: pd.DataFrame | None = None

    def _load(self) -> pd.DataFrame:
        if self._data is not None:
            return self._data

        if not self._csv_path.exists():
            raise FileNotFoundError(
                f"Freight data file not found: {self._csv_path}. "
                "Run backend/data/generate_data.py to create prototype data."
            )

        logger.info("Loading freight data from %s", self._csv_path)
        df = pd.read_csv(self._csv_path, parse_dates=["date"])
        df = df.sort_values(["origin", "destination", "vessel_type", "date"])
        df = df.reset_index(drop=True)

        logger.info(
            "Loaded %d freight observations, %d lanes",
            len(df),
            df.groupby(["origin", "destination", "vessel_type"]).ngroups,
        )
        self._data = df
        return df

    def get_freight_data(self) -> pd.DataFrame:
        return self._load().copy()

    def get_lane_data(
        self, origin: str, destination: str, vessel_type: str
    ) -> pd.DataFrame:
        df = self._load()
        mask = (
            (df["origin"].str.lower() == origin.lower())
            & (df["destination"].str.lower() == destination.lower())
            & (df["vessel_type"].str.lower() == vessel_type.lower())
        )
        result = df[mask].copy().sort_values("date").reset_index(drop=True)
        logger.info(
            "Lane %s→%s [%s]: %d observations",
            origin, destination, vessel_type, len(result),
        )
        return result

    def get_available_lanes(self) -> list[dict]:
        df = self._load()
        lanes = (
            df.groupby(["origin", "destination", "vessel_type"])
            .size()
            .reset_index(name="n_observations")
        )
        return lanes.to_dict("records")

    @property
    def source_label(self) -> str:
        return DATA_SOURCE_LABEL

    @property
    def disclaimer(self) -> str:
        return DATA_DISCLAIMER


# ─── Module-level singleton ─────────────────────────────────────────────────


_adapter_instance: FreightDataAdapter | None = None


def get_data_adapter() -> FreightDataAdapter:
    """
    Return the singleton data adapter.

    To swap to a different data source (e.g., licensed SAIL data),
    replace this function's return value or use dependency injection.
    """
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = PrototypeFreightDataAdapter()
    return _adapter_instance


def reset_adapter() -> None:
    """Reset the singleton (useful in tests)."""
    global _adapter_instance
    _adapter_instance = None
