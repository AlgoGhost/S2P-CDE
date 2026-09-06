import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE_URL, getHealth, getLanes, runDecisionLoop } from './api'
import { DEMO_SNAPSHOT, SNAPSHOT_CAPTURED_AT } from './demoSnapshot'
import { Header, NAV_ITEMS, Sidebar } from './components/Shell'
import { DEMO_CASE, Hero, InputPanel } from './components/Cockpit'
import { DecisionPipeline, RecommendationCard } from './components/Recommendation'
import { ForecastSection } from './components/ForecastSection'
import { FeasibilitySection } from './components/FeasibilitySection'
import { RiskSection } from './components/RiskSection'
import { StrategySection } from './components/StrategySection'
import { RationaleSection, VoyageSection } from './components/RationaleSection'
import { ArchitectureSection, CostSection, Transparency } from './components/CostSection'
import { Section } from './components/common'
import { buildVoyagePlan } from './lib/format'

/**
 * Lane coverage fallback, used only if /api/lanes is unreachable.
 *
 * The prototype dataset covers a specific set of origin→destination pairs, not
 * the full cross-product. Offering an unsupported pair would send the judge
 * straight into a 400 from the forecast engine, so destinations are always
 * constrained to the selected origin.
 */
const FALLBACK_LANES = {
  Australia: ['Paradip', 'Visakhapatnam'],
  Indonesia: ['Dhamra', 'Paradip'],
  Mozambique: ['Gangavaram'],
  Russia: ['Paradip'],
  USA: ['Haldia'],
}

export default function App() {
  const [form, setForm] = useState(DEMO_CASE)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)
  const [stage, setStage] = useState(null)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [activeNav, setActiveNav] = useState('cockpit')
  const [laneMap, setLaneMap] = useState(FALLBACK_LANES)

  const resultRef = useRef(null)

  // ── Health + lane discovery ──────────────────────────────────────────────
  useEffect(() => {
    const ac = new AbortController()
    let lanesLoaded = false
    const probe = async () => {
      try {
        await getHealth(ac.signal)
        if (ac.signal.aborted) return
        setBackendStatus('online')
        if (lanesLoaded) return
        try {
          const { lanes } = await getLanes(ac.signal)
          if (ac.signal.aborted || !Array.isArray(lanes) || lanes.length === 0) return
          const map = {}
          for (const l of lanes) {
            if (!map[l.origin]) map[l.origin] = new Set()
            map[l.origin].add(l.destination)
          }
          setLaneMap(
            Object.fromEntries(
              Object.entries(map)
                .map(([o, set]) => [o, [...set].sort()])
                .sort(([a], [b]) => a.localeCompare(b)),
            ),
          )
          lanesLoaded = true
        } catch {
          /* keep the config-mirrored fallbacks */
        }
      } catch {
        if (!ac.signal.aborted) setBackendStatus('offline')
      }
    }
    probe()
    const id = window.setInterval(probe, 20000)
    return () => {
      ac.abort()
      window.clearInterval(id)
    }
  }, [])

  // ── Scroll-spy for the sidebar ───────────────────────────────────────────
  useEffect(() => {
    const ids = ['cockpit', 'decision', 'forecast', 'feasibility', 'risk', 'strategy']
    const onScroll = () => {
      let current = 'cockpit'
      for (const id of ids) {
        const el = document.getElementById(id)
        if (el && el.getBoundingClientRect().top <= 160) current = id
      }
      setActiveNav(current)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [result])

  const origins = Object.keys(laneMap)
  const destinations = laneMap[form.origin] ?? []

  /** Keep origin/destination on a lane the dataset actually covers. */
  const updateForm = useCallback(
    (next) => {
      const valid = laneMap[next.origin] ?? []
      if (valid.length > 0 && !valid.includes(next.destination)) {
        setForm({ ...next, destination: valid[0] })
        return
      }
      setForm(next)
    },
    [laneMap],
  )

  // If lane discovery lands after first paint and invalidates the current pair,
  // snap the destination to a covered one rather than letting Analyze 400.
  useEffect(() => {
    const valid = laneMap[form.origin]
    if (valid?.length && !valid.includes(form.destination)) {
      setForm((f) => ({ ...f, destination: valid[0] }))
    }
  }, [laneMap, form.origin, form.destination])

  const navigate = useCallback((id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    else document.getElementById('cockpit')?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const analyze = useCallback(
    async (payload = form) => {
      setRunning(true)
      setError(null)
      setStage('forecast')
      try {
        const data = await runDecisionLoop(payload, setStage)
        setResult(data)
        setBackendStatus('online')
        window.setTimeout(
          () => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
          120,
        )
      } catch (err) {
        setError(err.message || 'The decision engine could not complete the analysis.')
        if (err.status === 0) setBackendStatus('offline')
      } finally {
        setRunning(false)
      }
    },
    [form],
  )

  const loadDemoCase = useCallback(() => {
    setForm(DEMO_CASE)
    setError(null)
  }, [])

  /** Clearly-labelled offline fallback built from a recorded live engine run. */
  const loadSnapshot = useCallback(() => {
    setForm(DEMO_CASE)
    setResult({ ...DEMO_SNAPSHOT, completedAt: new Date(), live: false })
    setError(null)
    window.setTimeout(
      () => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
      120,
    )
  }, [])

  const vessel = result?.feasibility?.recommended_vessel
  const plan = result
    ? buildVoyagePlan({
        voyages: result.optimize.voyages,
        cargoQuantity: result.request.cargo_quantity,
        parcelCapacity: vessel?.parcel_capacity ?? result.request.parcel_quantity,
        start: result.request.delivery_start,
        end: result.request.delivery_end,
      })
    : []

  return (
    <div className="app">
      <Sidebar active={activeNav} onNavigate={navigate} hasResult={Boolean(result)} />

      <div className="main">
        <Header backendStatus={backendStatus} lastRun={result?.completedAt} live={result?.live} />

        <div className="content">
          {/* ── Cockpit / input ───────────────────────────────────────── */}
          <div id="cockpit" className="hero reveal">
            <Hero />
            <InputPanel
              form={form}
              onChange={updateForm}
              onAnalyze={() => analyze()}
              onLoadDemo={loadDemoCase}
              running={running}
              currentStage={stage}
              hasResult={Boolean(result)}
              origins={origins}
              destinations={destinations}
            />
          </div>

          {/* ── Error ─────────────────────────────────────────────────── */}
          {error && (
            <div className="errorpanel reveal" role="alert">
              <div className="errorpanel__title">Decision engine unavailable</div>
              <p className="errorpanel__msg">{error}</p>
              <p className="errorpanel__msg" style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>
                Engine endpoint: <span className="mono">{API_BASE_URL}</span> · start it with{' '}
                <span className="mono">python -m uvicorn backend.main:app --port 8000</span> from
                the repository root.
              </p>
              <div className="errorpanel__actions">
                <button
                  type="button"
                  className="btn btn--primary"
                  style={{ flex: '0 0 auto' }}
                  onClick={() => analyze()}
                  disabled={running}
                >
                  Retry Analysis
                </button>
                <button type="button" className="btn btn--ghost btn--sm" onClick={loadSnapshot}>
                  Load Demo Snapshot
                </button>
              </div>
            </div>
          )}

          {/* ── Empty state ───────────────────────────────────────────── */}
          {!result && !error && !running && (
            <div className="placeholder reveal">
              <div className="placeholder__title">Awaiting a procurement requirement</div>
              <p className="placeholder__text">
                Load the SIH demo case — 300,000 tonnes from Australia into Paradip in 75,000 tonne
                parcels across October–December 2026 — then run{' '}
                <strong>Analyze Charter</strong>. VARUNEETI will forecast the lane, test every
                vessel class against Paradip’s physical limits, score the decision risk and compare
                four chartering structures.
              </p>
            </div>
          )}

          {/* ── Results ───────────────────────────────────────────────── */}
          {result && (
            <div ref={resultRef}>
              {!result.live && (
                <div className="snapshot-banner reveal">
                  <strong>DEMO SNAPSHOT</strong>
                  <span>
                    The backend is unreachable. Showing recorded engine output from a live run on{' '}
                    {SNAPSHOT_CAPTURED_AT} — this is not a live calculation.
                  </span>
                </div>
              )}

              <Section
                id="decision"
                num="01"
                title="Charter Recommendation"
                sub="How much tonnage should we lock, on which vessel, at what expected cost?"
              >
                <RecommendationCard
                  optimize={result.optimize}
                  feasibility={result.feasibility}
                  risk={result.risk}
                  request={result.request}
                />
              </Section>

              <Section
                id="pipeline"
                num="02"
                title="The Decision Pipeline"
                sub="Market data becomes a forecast, a feasible fleet, a risk score, then a charter decision."
                delay={60}
              >
                <DecisionPipeline
                  forecast={result.forecast}
                  feasibility={result.feasibility}
                  risk={result.risk}
                  optimize={result.optimize}
                />
              </Section>

              <ForecastSection
                forecast={result.forecast}
                recommendedVessel={vessel?.vessel_type}
                delay={80}
              />

              <FeasibilitySection
                feasibility={result.feasibility}
                recommendedVessel={vessel}
                delay={100}
              />

              <RiskSection risk={result.risk} delay={120} />

              <StrategySection
                optimize={result.optimize}
                riskScore={result.risk?.overall_score}
                cargoQuantity={result.request.cargo_quantity}
                delay={140}
              />

              <VoyageSection
                optimize={result.optimize}
                vessel={vessel}
                request={result.request}
                plan={plan}
                delay={160}
              />

              <RationaleSection optimize={result.optimize} delay={180} />

              <CostSection
                forecast={result.forecast}
                feasibility={result.feasibility}
                optimize={result.optimize}
                request={result.request}
                delay={200}
              />

              <ArchitectureSection delay={220} />

              <Transparency
                dataStatus={result.optimize?.data_status}
                forecastSource={result.forecast?.data_source}
                observations={result.forecast?.historical_series?.length}
              />
            </div>
          )}

          <div className="footnote">
            <span>
              VARUNEETI · Maritime Charter Decision Intelligence Engine · SIH 2026 · PS26006 ·
              Ministry of Steel / SAIL
            </span>
            <span className="mono">
              Forecast the market. Respect the port. Quantify the risk. Optimize the charter.
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
