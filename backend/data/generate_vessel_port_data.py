"""
Generate prototype vessel and port data for VARUNEETI.

Creates `vessels.csv` and `ports.csv` with assumed constraints, handling rates,
and costs to serve as a proxy for real data.

All values are marked with source_type = "prototype_assumption".
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent

def generate_vessels():
    """Generate proxy vessel data."""
    vessels = [
        {
            "vessel_type": "Handysize",
            "cargo_capacity": 35000,
            "draft": 10.0,
            "loa": 180,
            "beam": 28,
            "speed": 13.5,
            "daily_cost": 12000,
            "availability_factor": 0.9,
            "source_type": "prototype_assumption"
        },
        {
            "vessel_type": "Supramax",
            "cargo_capacity": 55000,
            "draft": 11.5,
            "loa": 195,
            "beam": 32,
            "speed": 14.0,
            "daily_cost": 15000,
            "availability_factor": 0.85,
            "source_type": "prototype_assumption"
        },
        {
            "vessel_type": "Panamax",
            "cargo_capacity": 75000,
            "draft": 13.5,
            "loa": 225,
            "beam": 32.2,
            "speed": 14.5,
            "daily_cost": 18000,
            "availability_factor": 0.8,
            "source_type": "prototype_assumption"
        },
        {
            "vessel_type": "Capesize",
            "cargo_capacity": 150000,
            "draft": 18.0,
            "loa": 290,
            "beam": 45,
            "speed": 15.0,
            "daily_cost": 25000,
            "availability_factor": 0.7,
            "source_type": "prototype_assumption"
        },
    ]
    df = pd.DataFrame(vessels)
    out_path = DATA_DIR / "vessels.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {out_path} ({len(df)} rows)")

def generate_ports():
    """Generate proxy port data for East Coast India."""
    ports = [
        {
            "port": "Paradip",
            "max_draft": 14.5,
            "max_loa": 260,
            "max_beam": 40,
            "cargo_handling_rate": 25000,
            "berth_capacity": 4,
            "congestion_index": 1.1,
            "lightering_available": True,
            "lightering_capacity": 20000,
            "lightering_cost_per_tonne": 4.5,
            "waiting_cost_per_day": 10000,
            "source_type": "prototype_assumption"
        },
        {
            "port": "Visakhapatnam",
            "max_draft": 14.0,
            "max_loa": 250,
            "max_beam": 38,
            "cargo_handling_rate": 20000,
            "berth_capacity": 5,
            "congestion_index": 1.2,
            "lightering_available": False,
            "lightering_capacity": 0,
            "lightering_cost_per_tonne": 0.0,
            "waiting_cost_per_day": 12000,
            "source_type": "prototype_assumption"
        },
        {
            "port": "Gangavaram",
            "max_draft": 18.5, # Deep draft port
            "max_loa": 300,
            "max_beam": 50,
            "cargo_handling_rate": 35000,
            "berth_capacity": 3,
            "congestion_index": 1.05,
            "lightering_available": False,
            "lightering_capacity": 0,
            "lightering_cost_per_tonne": 0.0,
            "waiting_cost_per_day": 9000,
            "source_type": "prototype_assumption"
        },
        {
            "port": "Gopalpur",
            "max_draft": 12.5,
            "max_loa": 225,
            "max_beam": 32,
            "cargo_handling_rate": 15000,
            "berth_capacity": 2,
            "congestion_index": 1.0,
            "lightering_available": False,
            "lightering_capacity": 0,
            "lightering_cost_per_tonne": 0.0,
            "waiting_cost_per_day": 8000,
            "source_type": "prototype_assumption"
        },
        {
            "port": "Dhamra",
            "max_draft": 18.0,
            "max_loa": 300,
            "max_beam": 45,
            "cargo_handling_rate": 30000,
            "berth_capacity": 3,
            "congestion_index": 1.15,
            "lightering_available": False,
            "lightering_capacity": 0,
            "lightering_cost_per_tonne": 0.0,
            "waiting_cost_per_day": 11000,
            "source_type": "prototype_assumption"
        },
        {
            "port": "Haldia",
            "max_draft": 7.5, # River port, very draft restricted
            "max_loa": 210,
            "max_beam": 32,
            "cargo_handling_rate": 12000,
            "berth_capacity": 6,
            "congestion_index": 1.3,
            "lightering_available": True, # Lightering via Sandheads is common
            "lightering_capacity": 15000,
            "lightering_cost_per_tonne": 6.0,
            "waiting_cost_per_day": 15000,
            "source_type": "prototype_assumption"
        },
        {
            "port": "Sagar-Sandheads",
            "max_draft": 10.5, # Anchorage, draft restricted
            "max_loa": 230,
            "max_beam": 35,
            "cargo_handling_rate": 10000,
            "berth_capacity": 0,
            "congestion_index": 1.4,
            "lightering_available": True,
            "lightering_capacity": 15000,
            "lightering_cost_per_tonne": 5.0,
            "waiting_cost_per_day": 14000,
            "source_type": "prototype_assumption"
        }
    ]
    df = pd.DataFrame(ports)
    out_path = DATA_DIR / "ports.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {out_path} ({len(df)} rows)")

if __name__ == "__main__":
    generate_vessels()
    generate_ports()
