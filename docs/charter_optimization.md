# VARUNEETI — Charter Optimization Engine (Emergency MVP)

## Business Objective
The Charter Optimization Engine transforms the outputs from the Forecasting, Feasibility, and Risk modules into an actionable commercial decision. It evaluates four distinct chartering strategies (SPOT, SHORT-TERM, MEDIUM-TERM, HYBRID) and recommends the strategy with the lowest risk-adjusted expected total landed cost.

## Strategy Definitions
1. **SPOT**: Procurement of individual voyages near loading date. Maximum flexibility but maximum exposure to future freight volatility.
2. **SHORT-TERM**: Period contract covering a limited duration/tonnage. 100% lock allocation.
3. **MEDIUM-TERM**: Longer period commitment. 100% lock allocation, exposing the charterer to utilization risk if demand drops, but protecting against rising freight.
4. **HYBRID**: A mix of locked tonnage and flexible tonnage (e.g. 60% locked, 40% spot), balancing cost security with operational flexibility.

## Decision Variables
- `strategy`: The selected strategy string.
- `vessel_class`: The directly feasible vessel with the lowest operational turnaround cost.
- `locked_tonnage`: Tonnage committed to period contracts.
- `flexible_tonnage`: Tonnage procured on the spot market.
- `lock_percentage`: Ratio of locked tonnage to total required tonnage.

## Cost Components
- **Freight Cost**: Sourced from the SARIMAX forecasting engine output.
- **Port Cost**: Derived from cargo handling rate and port congestion index (synthetic baseline).
- **Demurrage Exposure**: Modeled penalty when waiting days exceed a reasonable threshold (1.5x handling time).
- **Lightering Cost**: Calculated if direct discharge fails but lightering is operationally feasible (e.g. Haldia/Sandheads).
- **Risk Penalty**: Dynamic multipliers applied to period contracts when volatility/uncertainty is high.

## Hard Constraints
- **Vessel Feasibility**: If a vessel violates physical port limits (draft, LOA, beam) and cannot be lightered, it is skipped entirely.
- **Parcel Capacity**: Maximum cargo handled per voyage cannot exceed vessel capacity.

## Limitations and Assumptions
> [!IMPORTANT]
> The optimizer is a prototype decision-support system. Its recommendations are subject to data quality, commercial validation, operational constraints and human approval.

- Cost multipliers (e.g., Short-term=0.98x, Medium=0.95x) are illustrative prototypes to demonstrate the optimization logic, not real SAIL financial data.
- The Risk Score is a synthesized proxy calculated dynamically from forecast volatility and lightering status.
