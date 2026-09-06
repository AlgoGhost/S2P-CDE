import { Badge, CountUp, useGrow } from './common'
import {
  CURRENCY_CODE,
  feasibilityLabel,
  feasibilityTone,
  fmtMoney,
  fmtRate,
  fmtTonnes,
  prettyStrategy,
  riskTone,
  trendGlyph,
  trendTone,
} from '../lib/format'

/** Short, plain-language description of what each charter structure commits to. */
const STRATEGY_BLURB = {
  SPOT: 'All tonnage remains open to the spot market — maximum flexibility, full rate exposure.',
  SHORT_TERM: 'Tonnage committed under a short-term charter, capping near-term rate exposure.',
  MEDIUM_TERM:
    'Tonnage committed under a medium-term charter, trading flexibility for the lowest modelled expected cost.',
  HYBRID: 'Part of the programme is locked under charter, the balance stays open to spot.',
  NONE: 'No feasible charter programme could be constructed for this requirement.',
}

export function RecommendationCard({ optimize, feasibility, risk, request }) {
  const rec = optimize.recommendation
  const vessel = feasibility?.recommended_vessel
  const lockPct = rec.lock_percentage ?? 0
  const flexPct = Math.max(0, 100 - lockPct)

  const lockedW = useGrow(lockPct, 260)
  const flexW = useGrow(flexPct, 260)

  const infeasible = optimize.status !== 'optimal'

  return (
    <div className="reco">
      <div className="reco__top">
        <span className="reco__label">VARUNEETI Recommends</span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <Badge tone={infeasible ? 'danger' : 'info'}>
            {infeasible ? 'No Feasible Plan' : 'Optimizer Status: Optimal'}
          </Badge>
          <Badge>Decision Support · Human-in-the-loop</Badge>
        </span>
      </div>

      <div className="reco__body">
        <div className="reco__strategy">
          <div className="reco__strategy-name">{prettyStrategy(rec.strategy).toUpperCase()}</div>
          <p className="reco__strategy-sub">
            {STRATEGY_BLURB[rec.strategy] ?? 'Recommended charter structure.'}
          </p>

          <div className="locksplit">
            <div className="locksplit__bar">
              <div className="locksplit__locked" style={{ width: `${lockedW}%` }} />
              <div className="locksplit__flex" style={{ width: `${flexW}%` }} />
            </div>
            <div className="locksplit__legend">
              <div className="locksplit__item">
                <div className="locksplit__pct locksplit__pct--locked">
                  <CountUp value={lockPct} format={(v) => `${v.toFixed(0)}%`} />
                </div>
                <div className="locksplit__cap">Tonnage Locked</div>
                <div className="locksplit__tonnes">{fmtTonnes(rec.locked_tonnage)}</div>
              </div>
              <div className="locksplit__item" style={{ textAlign: 'right' }}>
                <div className="locksplit__pct locksplit__pct--flex">
                  <CountUp value={flexPct} format={(v) => `${v.toFixed(0)}%`} />
                </div>
                <div className="locksplit__cap">Flexible</div>
                <div className="locksplit__tonnes">{fmtTonnes(rec.flexible_tonnage)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="reco__metrics">
          <div className="metric">
            <div className="metric__label">Recommended Vessel</div>
            <div className="metric__value metric__value--sm">
              {rec.vessel_class?.toUpperCase() ?? '—'}
            </div>
            <div className={`metric__note tone-${feasibilityTone(vessel?.status)}`}>
              {vessel ? feasibilityLabel(vessel.status) : 'From feasibility engine'}
            </div>
          </div>

          <div className="metric">
            <div className="metric__label">Voyages</div>
            <div className="metric__value">
              <CountUp value={optimize.voyages} />
            </div>
            <div className="metric__note">
              {vessel ? `${fmtTonnes(vessel.parcel_capacity, { compact: true })} per voyage` : '—'}
            </div>
          </div>

          <div className="metric">
            <div className="metric__label">Decision Risk</div>
            <div className={`metric__value metric__value--sm tone-${riskTone(risk?.risk_level)}`}>
              {risk?.risk_level ?? '—'}
            </div>
            <div className="metric__note">
              <CountUp value={rec.risk_score} format={(v) => v.toFixed(1)} /> / 100 composite
            </div>
          </div>

          <div className="metric">
            <div className="metric__label">Expected Cost / Tonne</div>
            <div className="metric__value">
              <CountUp value={rec.cost_per_tonne} format={(v) => fmtRate(v)} />
            </div>
            <div className="metric__note">{CURRENCY_CODE} · modelled, risk-adjusted</div>
          </div>

          <div className="metric">
            <div className="metric__label">Total Expected Cost</div>
            <div className="metric__value">
              <CountUp value={rec.expected_cost} format={(v) => fmtMoney(v, { compact: true })} />
            </div>
            <div className="metric__note">{fmtMoney(rec.expected_cost)}</div>
          </div>

          <div className="metric">
            <div className="metric__label">Lane</div>
            <div className="metric__value metric__value--xs">
              {request.origin} → {request.destination}
            </div>
            <div className="metric__note">{fmtTonnes(request.cargo_quantity)} programme</div>
          </div>

          <div className="metric">
            <div className="metric__label">Delivery Window</div>
            <div className="metric__value metric__value--xs">
              {request.delivery_start?.slice(0, 7)} → {request.delivery_end?.slice(0, 7)}
            </div>
            <div className="metric__note">Requested laycan span</div>
          </div>

          <div className="metric">
            <div className="metric__label">Port Constraint</div>
            <div className="metric__value metric__value--sm">
              {feasibility?.port?.max_draft != null ? `${feasibility.port.max_draft} m` : '—'}
            </div>
            <div className="metric__note">Max draft at {feasibility?.port?.port ?? '—'}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

/** Compact stage cards: one headline output per engine, left to right. */
export function DecisionPipeline({ forecast, feasibility, risk, optimize }) {
  const rec = optimize.recommendation
  const vessel = feasibility?.recommended_vessel

  const nodes = [
    {
      stage: '01',
      engine: 'Forecast',
      headline: `${trendGlyph(forecast?.trend)} ${forecast?.trend ?? '—'}`,
      tone: trendTone(forecast?.trend),
      detail: `${fmtRate(forecast?.forecast)}/t point forecast · ${forecast?.horizon_days ?? '—'}d horizon`,
      foot: `Confidence ${forecast ? Math.round(forecast.confidence * 100) : '—'}% · ${forecast?.model_name ?? '—'}`,
    },
    {
      stage: '02',
      engine: 'Vessel × Port',
      headline: vessel?.vessel_type?.toUpperCase() ?? 'NONE',
      tone: feasibilityTone(vessel?.status),
      detail: vessel
        ? `${feasibilityLabel(vessel.status)} at ${feasibility.port?.port} · fit ${vessel.fit_score}/100`
        : 'No feasible vessel class',
      foot: `${feasibility?.vessels?.filter((v) => v.status !== 'INFEASIBLE').length ?? 0}/${
        feasibility?.vessels?.length ?? 0
      } classes usable`,
    },
    {
      stage: '03',
      engine: 'Risk',
      headline: `${risk?.overall_score ?? '—'} / 100`,
      tone: riskTone(risk?.risk_level),
      detail: `${risk?.risk_level ?? '—'} composite exposure`,
      foot: `Top driver: ${risk?.top_drivers?.[0]?.factor?.replace(/_/g, ' ') ?? '—'}`,
    },
    {
      stage: '04',
      engine: 'Optimizer',
      headline: prettyStrategy(rec.strategy).toUpperCase(),
      tone: 'info',
      detail: `${rec.lock_percentage}% locked · ${fmtRate(rec.cost_per_tonne)}/t expected`,
      foot: `${optimize.strategy_comparison.length} structures compared`,
    },
    {
      stage: '05',
      engine: 'Decision',
      headline:
        rec.lock_percentage === 0
          ? 'STAY OPEN'
          : rec.lock_percentage >= 100
            ? 'FULL LOCK'
            : 'LOCK + FLEX',
      tone: 'info',
      detail: `${fmtTonnes(rec.locked_tonnage, { compact: true })} locked / ${fmtTonnes(
        rec.flexible_tonnage,
        { compact: true },
      )} open`,
      foot: `${optimize.voyages} voyages · ${rec.vessel_class}`,
      isDecision: true,
    },
  ]

  return (
    <div className="pipeline">
      {nodes.map((n, i) => (
        <div
          key={n.stage}
          className={`pipe ${n.isDecision ? 'pipe--decision' : ''} reveal`}
          style={{ animationDelay: `${i * 90}ms` }}
        >
          <div className="pipe__stage">STAGE {n.stage}</div>
          <div className="pipe__engine">{n.engine}</div>
          <div className={`pipe__headline tone-${n.tone}`}>{n.headline}</div>
          <div className="pipe__detail">{n.detail}</div>
          <div className="pipe__foot">{n.foot}</div>
        </div>
      ))}
    </div>
  )
}
