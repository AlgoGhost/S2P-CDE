/**
 * VARUNEETI API client.
 *
 * The backend does NOT nest forecast/feasibility/risk inside the /api/optimize
 * response (verified against backend/schemas.py::OptimizeResponse), so the
 * cockpit calls each engine endpoint directly and assembles the decision view.
 * No calculation is duplicated here — every displayed figure originates from
 * a backend response.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000'

/** Vessel class used for the headline freight signal. */
// OptimizeService and RiskService both run their internal forecast on Panamax
// (backend/services/optimize_service.py). The cockpit uses the same lane so the
// chart and the recommendation can never disagree.
export const FORECAST_BENCHMARK_VESSEL = 'Panamax'
export const FORECAST_HORIZON_DAYS = 30

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** Turn any backend failure into an operator-safe message — never a stack trace. */
function friendlyMessage(status, detail) {
  if (status === 400 && detail) return detail
  if (status === 404) return 'Requested decision endpoint was not found on the engine.'
  if (status >= 500) return 'The decision engine encountered an internal error.'
  return detail || 'The decision engine returned an unexpected response.'
}

async function request(path, { method = 'GET', body, timeoutMs = 45000, signal } = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  // Let callers cancel too (e.g. the health poll on unmount) without leaving
  // an in-flight request to be killed by the browser.
  if (signal) {
    if (signal.aborted) controller.abort()
    else signal.addEventListener('abort', () => controller.abort(), { once: true })
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    if (err.name === 'AbortError') {
      throw new ApiError('The decision engine did not respond in time.', 0)
    }
    throw new ApiError(
      `Cannot reach the decision engine at ${API_BASE_URL}. Confirm the backend is running.`,
      0,
    )
  }
  clearTimeout(timer)

  if (!response.ok) {
    let detail = null
    try {
      const payload = await response.json()
      // FastAPI puts the message in `detail`; it may be a validation array.
      if (typeof payload?.detail === 'string') detail = payload.detail
      else if (Array.isArray(payload?.detail)) detail = payload.detail[0]?.msg ?? null
    } catch {
      /* body was not JSON — fall through to the generic message */
    }
    throw new ApiError(friendlyMessage(response.status, detail), response.status)
  }

  return response.json()
}

export const getHealth = (signal) => request('/api/health', { timeoutMs: 4000, signal })

export const getLanes = (signal) => request('/api/lanes', { timeoutMs: 8000, signal })

export const postForecast = (payload) =>
  request('/api/forecast', { method: 'POST', body: payload })

export const postFeasibility = (payload) =>
  request('/api/feasibility', { method: 'POST', body: payload })

export const postRisk = (payload) => request('/api/risk', { method: 'POST', body: payload })

export const postOptimize = (payload) =>
  request('/api/optimize', { method: 'POST', body: payload })

export const postScenario = (payload) =>
  request('/api/scenario', { method: 'POST', body: payload })

/**
 * Run the full decision loop, reporting progress per stage.
 *
 * Stage order mirrors the engine dependency graph:
 *   forecast + feasibility (independent) -> risk -> optimize
 *
 * @param {object} form      cockpit input values
 * @param {(id: string) => void} onStage called as each stage begins
 */
export async function runDecisionLoop(form, onStage = () => {}) {
  const decisionPayload = {
    origin: form.origin,
    destination: form.destination,
    cargo_quantity: Number(form.cargoQuantity),
    parcel_quantity: Number(form.parcelSize),
    delivery_start: form.deliveryStart,
    delivery_end: form.deliveryEnd,
  }

  onStage('forecast')
  const [forecast, feasibility] = await Promise.all([
    postForecast({
      origin: form.origin,
      destination: form.destination,
      vessel_type: FORECAST_BENCHMARK_VESSEL,
      horizon_days: FORECAST_HORIZON_DAYS,
    }),
    postFeasibility({
      origin: form.origin,
      destination: form.destination,
      cargo_quantity: decisionPayload.cargo_quantity,
      parcel_quantity: decisionPayload.parcel_quantity,
    }),
  ])

  onStage('feasibility')
  onStage('risk')
  const risk = await postRisk(decisionPayload)

  onStage('optimize')
  const optimize = await postOptimize(decisionPayload)

  // Stress cases reuse the memoised forecast, so this is near-instant once the
  // base decision has been solved.
  onStage('scenario')
  let scenarios = null
  try {
    scenarios = await postScenario(decisionPayload)
  } catch (err) {
    // Stress testing is additive - never fail the whole decision over it.
    console.warn('Scenario analysis unavailable:', err.message)
  }

  onStage('decision')
  return {
    forecast,
    feasibility,
    risk,
    optimize,
    scenarios,
    request: decisionPayload,
    completedAt: new Date(),
    live: true,
  }
}
