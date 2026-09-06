import { Badge, Panel, Section } from './common'
import { cleanDriver, fmtTonnes, formatDate } from '../lib/format'

/**
 * Classify a decision driver by which engine emitted it.
 * OptimizeService prefixes risk drivers with "Risk Driver:" and writes the
 * others as sentences; we key off those actual shapes rather than inventing
 * explanations. Text is always the backend's own, only enum reprs are cleaned.
 */
function classify(raw) {
  const s = raw.toLowerCase()
  if (s.startsWith('risk driver:'))
    return { src: 'Risk Engine', icon: '●', tone: 'warning' }
  if (s.includes('risk score evaluated'))
    return { src: 'Risk Engine', icon: '◆', tone: 'warning' }
  if (s.startsWith('forecast trend'))
    return { src: 'Forecast Engine', icon: '↗', tone: 'info' }
  if (s.startsWith('vessel selected'))
    return { src: 'Feasibility Engine', icon: '✓', tone: 'positive' }
  if (s.includes('selected because') || s.includes('selected to') || s.includes('selected as'))
    return { src: 'Charter Optimizer', icon: '★', tone: 'info' }
  if (s.includes('no feasible')) return { src: 'Feasibility Engine', icon: '✕', tone: 'danger' }
  return { src: 'Decision Engine', icon: '•', tone: 'info' }
}

export function RationaleSection({ optimize, delay = 0 }) {
  const drivers = (optimize.decision_drivers ?? []).map((d) => ({
    text: cleanDriver(d),
    ...classify(d),
  }))

  return (
    <Section
      id="rationale"
      num="08"
      title="Why VARUNEETI Chose This Strategy"
      sub="Every line below is emitted by the decision engines — the recommendation is auditable, not a black box."
      delay={delay}
    >
      <Panel
        title="Decision Drivers"
        right={<Badge tone="info">{drivers.length} traced signals</Badge>}
      >
        <div className="rationale">
          {drivers.map((d, i) => (
            <div className="reason" key={i}>
              <span className={`reason__icon reason__icon--${d.tone}`}>{d.icon}</span>
              <div>
                <div className="reason__src">{d.src}</div>
                <div className="reason__text">{d.text}</div>
              </div>
            </div>
          ))}
        </div>

        {optimize.assumptions?.length > 0 && (
          <>
            <div className="eyebrow" style={{ marginTop: 16 }}>
              Optimizer Assumptions (stated by the engine)
            </div>
            <ul className="assumption-list">
              {optimize.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </>
        )}
      </Panel>
    </Section>
  )
}

export function VoyageSection({ optimize, vessel, request, plan, delay = 0 }) {
  const totalPlanned = plan.reduce((s, v) => s + v.tonnes, 0)

  return (
    <Section
      id="voyage"
      num="07"
      title="Multi-Voyage Procurement Plan"
      sub="How the programme breaks into parcels the selected vessel and port can actually handle."
      delay={delay}
    >
      <div className="voyage-layout">
        <div className="voyagestats">
          <div className="bigstat">
            <div className="bigstat__label">Total Requirement</div>
            <div className="bigstat__value">
              {(request.cargo_quantity / 1000).toLocaleString()}K t
            </div>
            <div className="bigstat__note">
              {request.origin} → {request.destination} ·{' '}
              {formatDate(request.delivery_start, { day: 'numeric', month: 'short' })} –{' '}
              {formatDate(request.delivery_end)}
            </div>
          </div>
          <div className="forecast-layout" style={{ gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div className="signalcard">
              <div className="signalcard__label">Parcel Size</div>
              <div className="signalcard__value">
                {vessel ? `${(vessel.parcel_capacity / 1000).toFixed(0)}K` : '—'}
                <span style={{ fontSize: 13, color: 'var(--text-dim)' }}> t</span>
              </div>
              <div className="signalcard__note">Capped by {vessel?.vessel_type} capacity</div>
            </div>
            <div className="signalcard">
              <div className="signalcard__label">Voyages</div>
              <div className="signalcard__value tone-info">{optimize.voyages}</div>
              <div className="signalcard__note">From the feasibility engine</div>
            </div>
          </div>
        </div>

        <Panel
          title="Indicative Parcelisation"
          right={<Badge>Schedule is indicative</Badge>}
        >
          <div className="voyagerail">
            {plan.map((v) => (
              <div
                className="voyage reveal"
                key={v.index}
                style={{ animationDelay: `${v.index * 70}ms` }}
              >
                <div className="voyage__no">VOYAGE {String(v.index).padStart(2, '0')}</div>
                <div className="voyage__tonnes">
                  {v.tonnes >= 1000 ? `${(v.tonnes / 1000).toFixed(0)}K` : Math.round(v.tonnes)}
                  <span style={{ fontSize: 12, color: 'var(--text-dim)' }}> t</span>
                </div>
                {v.window && (
                  <div className="voyage__win">
                    {formatDate(v.window.from, { day: '2-digit', month: 'short' })} →{' '}
                    {formatDate(v.window.to, { day: '2-digit', month: 'short' })}
                  </div>
                )}
                <div className="voyage__meter" />
              </div>
            ))}
          </div>

          <div className="callout callout--info">
            <span>ⓘ</span>
            <span>
              The <strong>voyage count and parcel size come from the feasibility and optimizer
              responses</strong> ({fmtTonnes(totalPlanned)} across {plan.length} voyages). The dates
              shown are an even distribution across the requested delivery window — voyage-level
              scheduling and laycan negotiation are not modelled in this prototype.
            </span>
          </div>
        </Panel>
      </div>
    </Section>
  )
}
