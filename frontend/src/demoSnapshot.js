/**
 * DEMO SNAPSHOT - captured verbatim from a live VARUNEETI engine run.
 *
 * Real API responses (Australia -> Paradip, 300,000 t, 75,000 t parcels,
 * Oct-Dec 2026) recorded on 2026-09-06, NOT hand-written figures. The cockpit
 * falls back to this payload only when the backend is unreachable, and always
 * labels the screen as a snapshot so it is never mistaken for a live result.
 */

export const DEMO_SNAPSHOT = {
  "forecast": {
    "origin": "Australia",
    "destination": "Paradip",
    "vessel_type": "Panamax",
    "horizon_days": 30,
    "forecast": 30.24,
    "lower_bound": 22.68,
    "upper_bound": 37.81,
    "trend": "STABLE",
    "volatility": "MEDIUM",
    "confidence": 0.766,
    "model_name": "SARIMAX",
    "baseline_error": {
      "mae": 4.688,
      "rmse": 6.141,
      "mape": 15.02
    },
    "model_error": {
      "mae": 3.899,
      "rmse": 4.825,
      "mape": 12.64
    },
    "model_wins": true,
    "historical_series": [
      {
        "date": "2022-01-01",
        "value": 28.74,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-02-01",
        "value": 29.27,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-03-01",
        "value": 31.71,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-04-01",
        "value": 30.42,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-05-01",
        "value": 34.33,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-06-01",
        "value": 26.32,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-07-01",
        "value": 31.55,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-08-01",
        "value": 26.45,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-09-01",
        "value": 20.9,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-10-01",
        "value": 34.07,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-11-01",
        "value": 31.25,
        "lower": null,
        "upper": null
      },
      {
        "date": "2022-12-01",
        "value": 33.24,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-01-01",
        "value": 33.34,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-02-01",
        "value": 31.06,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-03-01",
        "value": 28.65,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-04-01",
        "value": 31.56,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-05-01",
        "value": 23.68,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-06-01",
        "value": 27.02,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-07-01",
        "value": 36.5,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-08-01",
        "value": 32.51,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-09-01",
        "value": 30.67,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-10-01",
        "value": 31.21,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-11-01",
        "value": 32.77,
        "lower": null,
        "upper": null
      },
      {
        "date": "2023-12-01",
        "value": 29.41,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-01-01",
        "value": 26.01,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-02-01",
        "value": 31.75,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-03-01",
        "value": 37.84,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-04-01",
        "value": 34.38,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-05-01",
        "value": 30.35,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-06-01",
        "value": 28.96,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-07-01",
        "value": 24.19,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-08-01",
        "value": 25.2,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-09-01",
        "value": 35.76,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-10-01",
        "value": 29.46,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-11-01",
        "value": 28.48,
        "lower": null,
        "upper": null
      },
      {
        "date": "2024-12-01",
        "value": 30.38,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-01-01",
        "value": 23.15,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-02-01",
        "value": 33.13,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-03-01",
        "value": 24.74,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-04-01",
        "value": 30.86,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-05-01",
        "value": 29.44,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-06-01",
        "value": 30.15,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-07-01",
        "value": 29.47,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-08-01",
        "value": 32.22,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-09-01",
        "value": 29.89,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-10-01",
        "value": 26.45,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-11-01",
        "value": 29.26,
        "lower": null,
        "upper": null
      },
      {
        "date": "2025-12-01",
        "value": 36.8,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-01-01",
        "value": 36.61,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-02-01",
        "value": 29.35,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-03-01",
        "value": 24.16,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-04-01",
        "value": 38.49,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-05-01",
        "value": 29.64,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-06-01",
        "value": 28.93,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-07-01",
        "value": 26.84,
        "lower": null,
        "upper": null
      },
      {
        "date": "2026-08-01",
        "value": 28.35,
        "lower": null,
        "upper": null
      }
    ],
    "forecast_series": [
      {
        "date": "2026-09-01",
        "value": 30.24,
        "lower": 22.68,
        "upper": 37.81
      }
    ],
    "data_source": "prototype_proxy",
    "warnings": []
  },
  "feasibility": {
    "origin": "Australia",
    "destination": "Paradip",
    "cargo_quantity": 300000.0,
    "parcel_quantity": 75000.0,
    "loading_port": null,
    "port": {
      "port": "Paradip",
      "max_draft": 14.5,
      "max_loa": 260,
      "max_beam": 40,
      "cargo_handling_rate": 25000,
      "berth_capacity": 4,
      "congestion_index": 1.1,
      "lightering_available": true,
      "lightering_capacity": 20000,
      "lightering_cost_per_tonne": 4.5,
      "waiting_cost_per_day": 10000,
      "source_type": "prototype_assumption"
    },
    "vessels": [
      {
        "vessel_type": "Panamax",
        "capacity": 75000.0,
        "draft": 13.5,
        "loa": 225.0,
        "beam": 32.2,
        "parcel_capacity": 75000.0,
        "voyages_required": 4,
        "direct_feasible": true,
        "conditional_feasible": false,
        "status": "DIRECT_FEASIBLE",
        "fit_score": 100.0,
        "fit_reasons": [
          "Good capacity utilization (100%)",
          "Capable of serving in 4 voyages"
        ],
        "passed_constraints": [
          "capacity",
          "draft",
          "loa",
          "beam"
        ],
        "failed_constraints": [],
        "handling_days": 12.0,
        "waiting_days": 1.2,
        "port_time_days": 13.2,
        "port_cost": 132000.0,
        "demurrage_exposure": 0.0,
        "lightering_cost": 0.0,
        "total_operational_cost": 132000.0,
        "lightering": null
      },
      {
        "vessel_type": "Supramax",
        "capacity": 55000.0,
        "draft": 11.5,
        "loa": 195.0,
        "beam": 32.0,
        "parcel_capacity": 55000.0,
        "voyages_required": 6,
        "direct_feasible": true,
        "conditional_feasible": false,
        "status": "DIRECT_FEASIBLE",
        "fit_score": 84.0,
        "fit_reasons": [
          "Good capacity utilization (100%)",
          "Below requested parcel: 55,000 t capacity vs 75,000 t requested - cargo split across more voyages",
          "Capable of serving in 6 voyages"
        ],
        "passed_constraints": [
          "draft",
          "loa",
          "beam"
        ],
        "failed_constraints": [],
        "handling_days": 13.2,
        "waiting_days": 1.32,
        "port_time_days": 14.52,
        "port_cost": 145200.0,
        "demurrage_exposure": 0.0,
        "lightering_cost": 0.0,
        "total_operational_cost": 145200.0,
        "lightering": null
      },
      {
        "vessel_type": "Handysize",
        "capacity": 35000.0,
        "draft": 10.0,
        "loa": 180.0,
        "beam": 28.0,
        "parcel_capacity": 35000.0,
        "voyages_required": 9,
        "direct_feasible": true,
        "conditional_feasible": false,
        "status": "DIRECT_FEASIBLE",
        "fit_score": 68.0,
        "fit_reasons": [
          "Good capacity utilization (100%)",
          "Below requested parcel: 35,000 t capacity vs 75,000 t requested - cargo split across more voyages",
          "Capable of serving in 9 voyages"
        ],
        "passed_constraints": [
          "draft",
          "loa",
          "beam"
        ],
        "failed_constraints": [],
        "handling_days": 12.6,
        "waiting_days": 1.26,
        "port_time_days": 13.86,
        "port_cost": 138600.0,
        "demurrage_exposure": 0.0,
        "lightering_cost": 0.0,
        "total_operational_cost": 138600.0,
        "lightering": null
      },
      {
        "vessel_type": "Capesize",
        "capacity": 150000.0,
        "draft": 18.0,
        "loa": 290.0,
        "beam": 45.0,
        "parcel_capacity": 75000.0,
        "voyages_required": 4,
        "direct_feasible": false,
        "conditional_feasible": false,
        "status": "INFEASIBLE",
        "fit_score": 0.0,
        "fit_reasons": [
          "Infeasible due to draft, loa, beam"
        ],
        "passed_constraints": [
          "capacity"
        ],
        "failed_constraints": [
          "draft",
          "loa",
          "beam"
        ],
        "handling_days": 12.0,
        "waiting_days": 1.2,
        "port_time_days": 13.2,
        "port_cost": 132000.0,
        "demurrage_exposure": 0.0,
        "lightering_cost": 0.0,
        "total_operational_cost": 132000.0,
        "lightering": null
      }
    ],
    "recommended_vessel": {
      "vessel_type": "Panamax",
      "capacity": 75000.0,
      "draft": 13.5,
      "loa": 225.0,
      "beam": 32.2,
      "parcel_capacity": 75000.0,
      "voyages_required": 4,
      "direct_feasible": true,
      "conditional_feasible": false,
      "status": "DIRECT_FEASIBLE",
      "fit_score": 100.0,
      "fit_reasons": [
        "Good capacity utilization (100%)",
        "Capable of serving in 4 voyages"
      ],
      "passed_constraints": [
        "capacity",
        "draft",
        "loa",
        "beam"
      ],
      "failed_constraints": [],
      "handling_days": 12.0,
      "waiting_days": 1.2,
      "port_time_days": 13.2,
      "port_cost": 132000.0,
      "demurrage_exposure": 0.0,
      "lightering_cost": 0.0,
      "total_operational_cost": 132000.0,
      "lightering": null
    },
    "alternatives": [
      {
        "vessel_type": "Supramax",
        "capacity": 55000.0,
        "draft": 11.5,
        "loa": 195.0,
        "beam": 32.0,
        "parcel_capacity": 55000.0,
        "voyages_required": 6,
        "direct_feasible": true,
        "conditional_feasible": false,
        "status": "DIRECT_FEASIBLE",
        "fit_score": 84.0,
        "fit_reasons": [
          "Good capacity utilization (100%)",
          "Below requested parcel: 55,000 t capacity vs 75,000 t requested - cargo split across more voyages",
          "Capable of serving in 6 voyages"
        ],
        "passed_constraints": [
          "draft",
          "loa",
          "beam"
        ],
        "failed_constraints": [],
        "handling_days": 13.2,
        "waiting_days": 1.32,
        "port_time_days": 14.52,
        "port_cost": 145200.0,
        "demurrage_exposure": 0.0,
        "lightering_cost": 0.0,
        "total_operational_cost": 145200.0,
        "lightering": null
      },
      {
        "vessel_type": "Handysize",
        "capacity": 35000.0,
        "draft": 10.0,
        "loa": 180.0,
        "beam": 28.0,
        "parcel_capacity": 35000.0,
        "voyages_required": 9,
        "direct_feasible": true,
        "conditional_feasible": false,
        "status": "DIRECT_FEASIBLE",
        "fit_score": 68.0,
        "fit_reasons": [
          "Good capacity utilization (100%)",
          "Below requested parcel: 35,000 t capacity vs 75,000 t requested - cargo split across more voyages",
          "Capable of serving in 9 voyages"
        ],
        "passed_constraints": [
          "draft",
          "loa",
          "beam"
        ],
        "failed_constraints": [],
        "handling_days": 12.6,
        "waiting_days": 1.26,
        "port_time_days": 13.86,
        "port_cost": 138600.0,
        "demurrage_exposure": 0.0,
        "lightering_cost": 0.0,
        "total_operational_cost": 138600.0,
        "lightering": null
      }
    ],
    "assumptions": [
      "Data source marked as 'prototype_assumption'",
      "Lightering ratio based on draft exceedance approximation",
      "Port waiting costs and handling rates are synthetic baselines"
    ]
  },
  "risk": {
    "overall_score": 34.2,
    "risk_level": "MEDIUM",
    "top_drivers": [
      {
        "factor": "freight_volatility",
        "score": 50.0,
        "weight": 0.25,
        "contribution": 12.5,
        "severity": "MEDIUM",
        "explanation": "Forecast volatility is moderate."
      },
      {
        "factor": "weather",
        "score": 70.0,
        "weight": 0.15,
        "contribution": 10.5,
        "severity": "HIGH",
        "explanation": "Delivery window spans Bay of Bengal cyclone season (Oct, Nov, Dec); seasonal calendar proxy, not a weather forecast."
      },
      {
        "factor": "port_congestion",
        "score": 20.000000000000018,
        "weight": 0.2,
        "contribution": 4.0,
        "severity": "LOW",
        "explanation": "Port congestion index is 1.1."
      }
    ],
    "all_drivers": [
      {
        "factor": "freight_volatility",
        "score": 50.0,
        "weight": 0.25,
        "contribution": 12.5,
        "severity": "MEDIUM",
        "explanation": "Forecast volatility is moderate."
      },
      {
        "factor": "weather",
        "score": 70.0,
        "weight": 0.15,
        "contribution": 10.5,
        "severity": "HIGH",
        "explanation": "Delivery window spans Bay of Bengal cyclone season (Oct, Nov, Dec); seasonal calendar proxy, not a weather forecast."
      },
      {
        "factor": "port_congestion",
        "score": 20.000000000000018,
        "weight": 0.2,
        "contribution": 4.0,
        "severity": "LOW",
        "explanation": "Port congestion index is 1.1."
      },
      {
        "factor": "vessel_availability",
        "score": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "severity": "LOW",
        "explanation": "Multiple feasible vessel alternatives exist."
      },
      {
        "factor": "delivery_pressure",
        "score": 15.0,
        "weight": 0.15,
        "contribution": 2.25,
        "severity": "LOW",
        "explanation": "91-day window against 13.2 days of modelled port time across 4 voyages (85% slack, sailing time excluded)."
      },
      {
        "factor": "operational",
        "score": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "severity": "LOW",
        "explanation": "Direct discharge feasible."
      }
    ],
    "assumptions": [
      "Factor weights are centralized prototype assumptions, not calibrated values.",
      "Port congestion is a proxy derived from the port master congestion index.",
      "Delivery pressure compares the requested window against the port time the feasibility engine computes for the selected vessel. Voyage sailing time is NOT modelled - the prototype dataset carries no route distances - so this understates true schedule pressure.",
      "Seasonal risk is a calendar proxy for Bay of Bengal cyclone season and the southwest monsoon. It is not a meteorological forecast."
    ]
  },
  "optimize": {
    "status": "optimal",
    "recommendation": {
      "strategy": "MEDIUM_TERM",
      "vessel_class": "Panamax",
      "locked_tonnage": 300000.0,
      "flexible_tonnage": 0.0,
      "lock_percentage": 100.0,
      "expected_cost": 8743800.0,
      "cost_per_tonne": 29.15,
      "risk_score": 34.2
    },
    "strategy_comparison": [
      {
        "strategy": "SPOT",
        "cost": 9204000.0,
        "cost_per_tonne": 30.68,
        "lock_percentage": 0.0,
        "locked_tonnage": 0.0,
        "flexible_tonnage": 300000.0
      },
      {
        "strategy": "SHORT_TERM",
        "cost": 9019920.0,
        "cost_per_tonne": 30.0664,
        "lock_percentage": 100.0,
        "locked_tonnage": 300000.0,
        "flexible_tonnage": 0.0
      },
      {
        "strategy": "MEDIUM_TERM",
        "cost": 8743800.0,
        "cost_per_tonne": 29.146,
        "lock_percentage": 100.0,
        "locked_tonnage": 300000.0,
        "flexible_tonnage": 0.0
      },
      {
        "strategy": "HYBRID",
        "cost": 8927880.0,
        "cost_per_tonne": 29.7596,
        "lock_percentage": 60.0,
        "locked_tonnage": 180000.0,
        "flexible_tonnage": 120000.0
      }
    ],
    "voyages": 4,
    "decision_drivers": [
      "Risk Driver: Forecast volatility is moderate.",
      "Risk Driver: Delivery window spans Bay of Bengal cyclone season (Oct, Nov, Dec); seasonal calendar proxy, not a weather forecast.",
      "Risk Driver: Port congestion index is 1.1.",
      "Forecast trend is STABLE with MEDIUM volatility.",
      "Vessel selected: Panamax (Feasibility: DIRECT_FEASIBLE).",
      "Risk score evaluated at 34.2/100.",
      "Medium-term selected because market risk is low and cost multiplier is favorable."
    ],
    "assumptions": [
      "Cost multipliers (Spot=1.0, Short=0.98, Medium=0.95, Hybrid=0.97) are prototype assumptions.",
      "Risk score is a synthesized proxy for MVP demonstration."
    ],
    "data_status": {
      "prototype": true
    }
  },
  "scenarios": {
    "base_scenario_id": "BASE",
    "outcomes": [
      {
        "scenario_id": "BASE",
        "label": "Base Case",
        "status": "optimal",
        "strategy": "MEDIUM_TERM",
        "vessel_class": "Panamax",
        "voyages": 4,
        "lock_percentage": 100.0,
        "expected_cost": 8743800.0,
        "cost_per_tonne": 29.15,
        "risk_score": 34.2,
        "cost_delta_vs_base": 0.0,
        "cost_pct_delta_vs_base": 0.0,
        "strategy_changed": false,
        "vessel_changed": false,
        "notes": "Unshocked decision using the model's own forecast."
      },
      {
        "scenario_id": "HIGH_FREIGHT",
        "label": "Freight Spike +25%",
        "status": "optimal",
        "strategy": "MEDIUM_TERM",
        "vessel_class": "Panamax",
        "voyages": 4,
        "lock_percentage": 100.0,
        "expected_cost": 10898400.0,
        "cost_per_tonne": 36.33,
        "risk_score": 34.2,
        "cost_delta_vs_base": 2154600.0,
        "cost_pct_delta_vs_base": 24.64,
        "strategy_changed": false,
        "vessel_changed": false,
        "notes": "Freight settles 25% above the point forecast."
      },
      {
        "scenario_id": "LOW_FREIGHT",
        "label": "Freight Fall -20%",
        "status": "optimal",
        "strategy": "MEDIUM_TERM",
        "vessel_class": "Panamax",
        "voyages": 4,
        "lock_percentage": 100.0,
        "expected_cost": 7020120.0,
        "cost_per_tonne": 23.4,
        "risk_score": 34.2,
        "cost_delta_vs_base": -1723680.0,
        "cost_pct_delta_vs_base": -19.71,
        "strategy_changed": false,
        "vessel_changed": false,
        "notes": "Freight settles 20% below the point forecast."
      },
      {
        "scenario_id": "HIGH_CONGESTION",
        "label": "Port Congestion +40%",
        "status": "optimal",
        "strategy": "HYBRID",
        "vessel_class": "Panamax",
        "voyages": 4,
        "lock_percentage": 60.0,
        "expected_cost": 8983286.4,
        "cost_per_tonne": 29.94,
        "risk_score": 50.2,
        "cost_delta_vs_base": 239486.4,
        "cost_pct_delta_vs_base": 2.74,
        "strategy_changed": true,
        "vessel_changed": false,
        "notes": "Discharge port congestion worsens by 40%, extending port time."
      },
      {
        "scenario_id": "LOW_AVAILABILITY",
        "label": "Preferred Vessel Unavailable",
        "status": "optimal",
        "strategy": "MEDIUM_TERM",
        "vessel_class": "Supramax",
        "voyages": 6,
        "lock_percentage": 100.0,
        "expected_cost": 8756340.0,
        "cost_per_tonne": 29.19,
        "risk_score": 38.8,
        "cost_delta_vs_base": 12540.0,
        "cost_pct_delta_vs_base": 0.14,
        "strategy_changed": false,
        "vessel_changed": true,
        "notes": "Panamax cannot be fixed in the delivery window; the fleet is re-evaluated without it."
      }
    ],
    "recommendation_is_robust": false,
    "robustness_summary": "The recommendation is NOT robust: 1 of 4 stress cases change the structure (Port Congestion +40% -> HYBRID). Treat MEDIUM_TERM as conditional on the base forecast holding.",
    "worst_case_scenario_id": "HIGH_FREIGHT",
    "assumptions": [
      "Scenario shock magnitudes are prototype assumptions, not calibrated probabilities or fitted market moves.",
      "Each scenario re-runs the full forecast/feasibility/risk/strategy path; no cost logic is duplicated in the scenario engine.",
      "Scenarios are not probability-weighted - they are independent stress cases, so their costs must not be averaged into an expected value.",
      "Cost multipliers (Spot=1.0, Short=0.98, Medium=0.95, Hybrid=0.97) are prototype assumptions.",
      "Risk score is a synthesized proxy for MVP demonstration."
    ],
    "data_status": {
      "prototype": true
    }
  },
  "request": {
    "origin": "Australia",
    "destination": "Paradip",
    "cargo_quantity": 300000,
    "parcel_quantity": 75000,
    "delivery_start": "2026-10-01",
    "delivery_end": "2026-12-31"
  }
}

export const SNAPSHOT_CAPTURED_AT = '2026-09-06'
