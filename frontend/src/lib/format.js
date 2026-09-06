/**
 * Formatting + derivation helpers.
 *
 * Anything derived (rather than returned verbatim by the API) is computed here
 * from backend values only, and every consumer labels it as modelled/derived.
 */

/**
 * Currency note: backend/data/freight.csv carries freight_rate in USD/tonne and
 * every cost in the optimizer inherits that unit. We render USD, never INR.
 */
export const CURRENCY_SYMBOL = '$'
export const CURRENCY_CODE = 'USD'

export function fmtMoney(value, { compact = false } = {}) {
  if (value == null || Number.isNaN(value)) return '—'
  if (compact) {
    const abs = Math.abs(value)
    if (abs >= 1e9) return `${CURRENCY_SYMBOL}${(value / 1e9).toFixed(2)}B`
    if (abs >= 1e6) return `${CURRENCY_SYMBOL}${(value / 1e6).toFixed(2)}M`
    if (abs >= 1e3) return `${CURRENCY_SYMBOL}${(value / 1e3).toFixed(1)}K`
  }
  return (
    CURRENCY_SYMBOL +
    value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
  )
}

export function fmtRate(value, digits = 2) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${CURRENCY_SYMBOL}${value.toFixed(digits)}`
}

export function fmtTonnes(value, { compact = false } = {}) {
  if (value == null || Number.isNaN(value)) return '—'
  if (compact && Math.abs(value) >= 1000) return `${Math.round(value / 1000)}K t`
  return `${Math.round(value).toLocaleString('en-US')} t`
}

export function fmtPct(value, digits = 0) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${value.toFixed(digits)}%`
}

/** SPOT | SHORT_TERM -> Spot | Short-Term */
export function prettyStrategy(strategy) {
  if (!strategy) return '—'
  return strategy
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join('-')
}

/** freight_volatility -> Freight Volatility */
export function prettyFactor(factor) {
  if (!factor) return '—'
  const overrides = {
    weather: 'Seasonal / Weather',
    operational: 'Operational Risk',
    port_congestion: 'Port Congestion',
    vessel_availability: 'Vessel Availability',
    freight_volatility: 'Freight Volatility',
    delivery_pressure: 'Delivery Pressure',
  }
  if (overrides[factor]) return overrides[factor]
  return factor
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

/** DIRECT_FEASIBLE -> DIRECT, CONDITIONALLY_FEASIBLE -> LIGHTERING */
export function feasibilityLabel(status) {
  switch (status) {
    case 'DIRECT_FEASIBLE':
      return 'DIRECT'
    case 'CONDITIONALLY_FEASIBLE':
      return 'LIGHTERING'
    case 'INFEASIBLE':
      return 'INFEASIBLE'
    default:
      return status || '—'
  }
}

export function feasibilityTone(status) {
  switch (status) {
    case 'DIRECT_FEASIBLE':
      return 'positive'
    case 'CONDITIONALLY_FEASIBLE':
      return 'warning'
    case 'INFEASIBLE':
      return 'danger'
    default:
      return 'neutral'
  }
}

export function riskTone(level) {
  switch ((level || '').toUpperCase()) {
    case 'LOW':
      return 'positive'
    case 'MEDIUM':
      return 'warning'
    case 'HIGH':
      return 'danger'
    default:
      return 'neutral'
  }
}

export function trendTone(trend) {
  switch ((trend || '').toUpperCase()) {
    case 'RISING':
      return 'warning'
    case 'FALLING':
      return 'positive'
    default:
      return 'info'
  }
}

export function trendGlyph(trend) {
  switch ((trend || '').toUpperCase()) {
    case 'RISING':
      return '▲'
    case 'FALLING':
      return '▼'
    default:
      return '►'
  }
}

/**
 * OptimizeService builds its driver strings with f-strings over raw Enum
 * members, so responses contain "TrendDirection.STABLE" / "VolatilityLevel.MEDIUM".
 * We normalise for display rather than editing the service.
 */
export function cleanDriver(text) {
  if (!text) return ''
  return text
    .replace(/\b(?:TrendDirection|VolatilityLevel|RiskLevel|FeasibilityStatus|CharterStrategy)\./g, '')
    .replace(/^Risk Driver:\s*/i, '')
    .replace(/\s+/g, ' ')
    .trim()
}

/** Constraint keys -> human labels for the failure chips. */
export function prettyConstraint(key) {
  const map = {
    draft: 'Draft',
    loa: 'LOA',
    beam: 'Beam',
    capacity: 'Capacity',
    lightering_draft: 'Draft (via lightering)',
    lightering_capacity_exceeded: 'Lightering capacity exceeded',
  }
  return map[key] || key
}

export function formatDate(value, opts = { day: 'numeric', month: 'short', year: 'numeric' }) {
  if (!value) return '—'
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('en-GB', opts)
}

export function formatTime(date) {
  if (!date) return '—'
  return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

/**
 * Indicative parcelisation schedule.
 *
 * The backend returns a voyage COUNT (OptimizeResponse.voyages) but no
 * voyage-level dates — scheduling is not modelled in the prototype. We spread
 * the voyages evenly across the requested delivery window purely so the plan is
 * legible, and the UI labels it as indicative.
 */
export function buildVoyagePlan({ voyages, cargoQuantity, parcelCapacity, start, end }) {
  if (!voyages || voyages < 1) return []
  const startMs = new Date(start).getTime()
  const endMs = new Date(end).getTime()
  const hasWindow = Number.isFinite(startMs) && Number.isFinite(endMs) && endMs > startMs

  let remaining = cargoQuantity
  const plan = []
  for (let i = 0; i < voyages; i += 1) {
    const tonnes = Math.min(parcelCapacity, remaining)
    remaining -= tonnes
    let window = null
    if (hasWindow) {
      const span = (endMs - startMs) / voyages
      window = { from: new Date(startMs + span * i), to: new Date(startMs + span * (i + 1)) }
    }
    plan.push({ index: i + 1, tonnes, window })
  }
  return plan
}

/**
 * Cost decomposition of the recommended strategy.
 *
 * Reconstructed from published API values only:
 *   freight        = forecast.forecast (USD/t) x cargo_quantity
 *   port/demurrage/lightering = feasibility.recommended_vessel.*
 *   charter adj.   = optimize.recommendation.expected_cost - (freight + operational)
 *
 * That last term is exactly the charter-structure multiplier (and any risk
 * penalty) the optimizer applied, surfaced instead of guessed. Components the
 * prototype does not model are returned as unavailable, never as numbers.
 */
export function buildCostBreakdown({ forecast, vessel, recommendation, cargoQuantity }) {
  const freight = forecast != null && cargoQuantity ? forecast * cargoQuantity : null
  const portCost = vessel?.port_cost ?? null
  const demurrage = vessel?.demurrage_exposure ?? null
  const lightering = vessel?.lightering_cost ?? null
  const operational = vessel?.total_operational_cost ?? null
  const expected = recommendation?.expected_cost ?? null

  const base = freight != null && operational != null ? freight + operational : null
  const charterAdjustment = base != null && expected != null ? expected - base : null

  return {
    rows: [
      {
        label: 'Freight',
        value: freight,
        note: `${fmtRate(forecast)}/t forecast × ${fmtTonnes(cargoQuantity)}`,
      },
      { label: 'Port Charges', value: portCost, note: 'Berth + waiting time, all voyages' },
      { label: 'Demurrage Exposure', value: demurrage, note: 'Modelled excess port time' },
      {
        label: 'Lightering',
        value: lightering,
        note: lightering ? 'Transhipment at anchorage' : 'Not required for this vessel',
      },
      {
        label: 'Idle / Positioning',
        value: null,
        unavailable: true,
        note: 'Ballast & positioning legs are not modelled in the prototype',
      },
      {
        label: 'Charter Structure Adjustment',
        value: charterAdjustment,
        note: 'Modelled premium/discount of the selected charter structure vs. spot',
        signed: true,
      },
      {
        label: 'Explicit Risk Provision',
        value: null,
        unavailable: true,
        note: 'Risk enters via strategy multipliers, not as a separate cost line',
      },
    ],
    total: expected,
    perTonne: recommendation?.cost_per_tonne ?? null,
    operational,
  }
}
