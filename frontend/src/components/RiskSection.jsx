import { Badge, CountUp, Panel, Section, useGrow } from './common'
import { prettyFactor, riskTone } from '../lib/format'

/**
 * Canonical factor order (RiskService.WEIGHTS). Used only to keep the display
 * order stable and to name dimensions the response did not quantify — never to
 * supply a score.
 */
const FACTOR_ORDER = [
  'freight_volatility',
  'port_congestion',
  'vessel_availability',
  'weather',
  'delivery_pressure',
  'operational',
]

const SEVERITY_COLOR = {
  HIGH: 'var(--red)',
  MEDIUM: 'var(--amber)',
  LOW: 'var(--green)',
}

function scoreColor(score) {
  if (score > 60) return 'var(--red)'
  if (score > 30) return 'var(--amber)'
  return 'var(--green)'
}

function Gauge({ score, level }) {
  const R = 78
  const CX = 100
  const CY = 96
  const circumference = Math.PI * R
  const pct = Math.max(0, Math.min(100, score)) / 100
  const dash = useGrow(circumference * pct, 300)

  const arc = `M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`
  const color = scoreColor(score)

  return (
    <div className="gauge">
      <svg className="gauge__svg" viewBox="0 0 200 132" role="img" aria-label={`Risk ${score}/100`}>
        <path
          d={arc}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d={arc}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
          style={{ transition: 'stroke-dasharray 1.1s cubic-bezier(0.2,0.8,0.2,1)' }}
        />
        <text className="gauge__score" x={CX} y={CY - 6} textAnchor="middle">
          <CountUp value={score} format={(v) => v.toFixed(0)} />
        </text>
        <text className="gauge__of" x={CX} y={CY + 14} textAnchor="middle">
          / 100
        </text>
      </svg>
      <div className={`gauge__level tone-${riskTone(level)}`}>{level}</div>
      <div className="gauge__note">
        Weighted composite of six modelled decision-risk dimensions.
      </div>
    </div>
  )
}

function RiskRow({ factor, driver }) {
  const score = driver?.score ?? 0
  const w = useGrow(driver ? score : 0, 320)

  if (!driver) {
    return (
      <div className="riskrow riskrow--unknown">
        <div>
          <div className="riskrow__name">{prettyFactor(factor)}</div>
          <div className="riskrow__weight">in model</div>
        </div>
        <div className="riskrow__track" />
        <div className="riskrow__na">not in response</div>
      </div>
    )
  }

  return (
    <div className="riskrow">
      <div>
        <div className="riskrow__name">{prettyFactor(factor)}</div>
        <div className="riskrow__weight">
          weight {(driver.weight * 100).toFixed(0)}% · contrib {driver.contribution}
        </div>
      </div>
      <div className="riskrow__track">
        <span
          className="riskrow__fill"
          style={{ width: `${w}%`, background: SEVERITY_COLOR[driver.severity] ?? 'var(--blue)' }}
        />
      </div>
      <div className="riskrow__score" style={{ color: SEVERITY_COLOR[driver.severity] }}>
        {score.toFixed(0)}
        <span style={{ fontSize: 9, color: 'var(--text-dim)', marginLeft: 4 }}>
          {driver.severity}
        </span>
      </div>
    </div>
  )
}

export function RiskSection({ risk, delay = 0 }) {
  // Prefer the full factor set; fall back to top drivers if the engine only
  // exposes those. Dimensions that are absent are labelled, never estimated.
  const drivers = risk.all_drivers?.length ? risk.all_drivers : (risk.top_drivers ?? [])
  const byFactor = Object.fromEntries(drivers.map((d) => [d.factor, d]))
  const knownFactors = FACTOR_ORDER.filter((f) => f in byFactor)
  const extraFactors = drivers.map((d) => d.factor).filter((f) => !FACTOR_ORDER.includes(f))
  const ordered = [...FACTOR_ORDER, ...extraFactors]
  const partial = knownFactors.length < FACTOR_ORDER.length

  return (
    <Section
      id="risk"
      num="05"
      title="Decision Risk Radar"
      sub="What can go wrong? Composite exposure across market, port, fleet and schedule dimensions."
      delay={delay}
    >
      <div className="risk-layout">
        <Panel title="Overall Decision Risk" bodyStyle={{ padding: 0 }}>
          <Gauge score={risk.overall_score} level={risk.risk_level} />
        </Panel>

        <Panel
          title="Risk Dimensions"
          right={<Badge>{drivers.length} of {FACTOR_ORDER.length} scored</Badge>}
        >
          {ordered.map((f) => (
            <RiskRow key={f} factor={f} driver={byFactor[f]} />
          ))}
          {partial && (
            <div className="callout callout--info" style={{ marginTop: 12 }}>
              <span>ⓘ</span>
              <span>
                Dimensions marked <em>not in response</em> are scored inside the risk engine and
                feed the composite, but are not itemised by this endpoint. No placeholder values
                are shown for them.
              </span>
            </div>
          )}
        </Panel>

        <Panel title="Top Risk Drivers" right={<Badge tone={riskTone(risk.risk_level)}>{risk.risk_level}</Badge>}>
          <div className="driverlist">
            {(risk.top_drivers ?? []).map((d, i) => (
              <div className="driver" key={d.factor}>
                <span className="driver__no">{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <div className="driver__name" style={{ color: SEVERITY_COLOR[d.severity] }}>
                    {prettyFactor(d.factor)}
                  </div>
                  <div className="driver__text">{d.explanation}</div>
                  <div className="driver__text" style={{ fontFamily: 'var(--font-mono)' }}>
                    score {d.score} × weight {d.weight} = {d.contribution} pts
                  </div>
                </div>
              </div>
            ))}
          </div>
          {risk.assumptions?.length > 0 && (
            <>
              <div className="eyebrow" style={{ marginTop: 14 }}>
                Stated Assumptions
              </div>
              <ul className="assumption-list">
                {risk.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </>
          )}
        </Panel>
      </div>
    </Section>
  )
}
