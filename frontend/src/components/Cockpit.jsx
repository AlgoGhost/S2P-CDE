import { Badge } from './common'
import { fmtTonnes } from '../lib/format'

export const DEMO_CASE = {
  origin: 'Australia',
  destination: 'Paradip',
  cargoQuantity: 300000,
  parcelSize: 75000,
  deliveryStart: '2026-10-01',
  deliveryEnd: '2026-12-31',
}

export const STAGES = [
  { id: 'forecast', no: '01', label: 'Market Forecast' },
  { id: 'feasibility', no: '02', label: 'Vessel–Port Check' },
  { id: 'risk', no: '03', label: 'Risk Assessment' },
  { id: 'optimize', no: '04', label: 'Charter Optimization' },
  { id: 'decision', no: '05', label: 'Decision Ready' },
]

const CHAIN = ['Input', 'Forecast', 'Vessel × Port', 'Risk', 'Optimizer', 'Decision']

export function Hero() {
  return (
    <div className="hero__copy">
      <div className="hero__kicker">
        <Badge tone="info">PS26006 · Ministry of Steel · SAIL</Badge>
        <Badge>Prototype / Proxy Data</Badge>
      </div>
      <h1 className="hero__title">Charter Decision Cockpit</h1>
      <p className="hero__lede">
        Move from reactive, single-voyage spot procurement to predictive, constraint-aware
        multi-voyage charter planning for bulk cargo imports into India’s East Coast.
      </p>
      <div className="hero__pitch">
        VARUNEETI does not stop at forecasting freight rates. It converts market uncertainty into
        an <strong>auditable charter decision</strong> that respects real vessel and port
        constraints — then shows its reasoning.
      </div>
      <div className="hero__chain">
        {CHAIN.map((step, i) => (
          <span key={step} style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
            {i > 0 && <span className="hero__chain-sep">→</span>}
            <span className="hero__chain-item">{step}</span>
          </span>
        ))}
      </div>
    </div>
  )
}

export function StageTracker({ currentStage, running, done }) {
  const activeIdx = STAGES.findIndex((s) => s.id === currentStage)
  return (
    <div className="stages" aria-live="polite">
      {STAGES.map((stage, i) => {
        let cls = ''
        if (done) cls = 'is-done'
        else if (running && i < activeIdx) cls = 'is-done'
        else if (running && i === activeIdx) cls = 'is-active'
        return (
          <div key={stage.id} className={`stage ${cls}`}>
            <div className="stage__no">{stage.no}</div>
            <div className="stage__label">{stage.label}</div>
            <div className="stage__bar">
              <span />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function InputPanel({
  form,
  onChange,
  onAnalyze,
  onLoadDemo,
  running,
  currentStage,
  hasResult,
  origins,
  destinations,
}) {
  const set = (key) => (e) => onChange({ ...form, [key]: e.target.value })
  const setNum = (key) => (e) => onChange({ ...form, [key]: e.target.value.replace(/[^\d]/g, '') })

  const cargo = Number(form.cargoQuantity)
  const parcel = Number(form.parcelSize)
  const invalid =
    !form.origin ||
    !form.destination ||
    !(cargo > 0) ||
    !(parcel > 0) ||
    !form.deliveryStart ||
    !form.deliveryEnd ||
    new Date(form.deliveryEnd) < new Date(form.deliveryStart)

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__title">Procurement Requirement</span>
        <span style={{ marginLeft: 'auto' }}>
          <Badge tone="info">Live Engine Call</Badge>
        </span>
      </div>
      <div className="panel__body">
        <div className="inputgrid">
          <div className="field">
            <label className="field__label" htmlFor="origin">
              Origin
            </label>
            <select
              id="origin"
              className="field__control"
              value={form.origin}
              onChange={set('origin')}
              disabled={running}
            >
              {origins.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="destination">
              Destination Port
            </label>
            <select
              id="destination"
              className="field__control"
              value={form.destination}
              onChange={set('destination')}
              disabled={running}
            >
              {destinations.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <span className="field__hint">
              {destinations.length} lane{destinations.length === 1 ? '' : 's'} covered from{' '}
              {form.origin} in the prototype dataset
            </span>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="cargo">
              Cargo Quantity (tonnes)
            </label>
            <input
              id="cargo"
              className="field__control"
              inputMode="numeric"
              value={form.cargoQuantity}
              onChange={setNum('cargoQuantity')}
              disabled={running}
            />
            <span className="field__hint">{fmtTonnes(cargo)} total requirement</span>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="parcel">
              Parcel Size (tonnes)
            </label>
            <input
              id="parcel"
              className="field__control"
              inputMode="numeric"
              value={form.parcelSize}
              onChange={setNum('parcelSize')}
              disabled={running}
            />
            <span className="field__hint">
              {cargo > 0 && parcel > 0
                ? `≈ ${Math.ceil(cargo / parcel)} parcels before vessel constraints`
                : 'Per-voyage lot size'}
            </span>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="dstart">
              Delivery Window Start
            </label>
            <input
              id="dstart"
              type="date"
              className="field__control"
              value={form.deliveryStart}
              onChange={set('deliveryStart')}
              disabled={running}
            />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="dend">
              Delivery Window End
            </label>
            <input
              id="dend"
              type="date"
              className="field__control"
              value={form.deliveryEnd}
              onChange={set('deliveryEnd')}
              disabled={running}
            />
          </div>
        </div>

        <div className="actionrow">
          <button
            type="button"
            className="btn btn--primary"
            onClick={onAnalyze}
            disabled={running || invalid}
          >
            {running ? <span className="spinner" /> : null}
            {running ? 'Analyzing…' : hasResult ? 'Re-run Analysis' : 'Analyze Charter'}
          </button>
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={onLoadDemo}
            disabled={running}
          >
            Load SIH Demo Case
          </button>
        </div>

        {invalid && !running && (
          <p className="field__hint" style={{ marginTop: 10, color: 'var(--amber)' }}>
            Complete every field and ensure the delivery window ends after it starts.
          </p>
        )}

        {(running || hasResult) && (
          <StageTracker currentStage={currentStage} running={running} done={!running && hasResult} />
        )}
      </div>
    </div>
  )
}
