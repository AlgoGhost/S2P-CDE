import { Badge, KV, Panel, Section, useGrow } from './common'
import {
  feasibilityLabel,
  feasibilityTone,
  fmtMoney,
  fmtTonnes,
  prettyConstraint,
} from '../lib/format'

const TONE_COLOR = {
  positive: 'var(--green)',
  warning: 'var(--amber)',
  danger: 'var(--red)',
  neutral: 'var(--text-dim)',
}

function FitBar({ score, tone }) {
  const w = useGrow(score, 260)
  return (
    <div className="fitbar">
      <span className="fitbar__track">
        <span
          className="fitbar__fill"
          style={{ width: `${w}%`, background: TONE_COLOR[tone] ?? 'var(--blue)' }}
        />
      </span>
      <span className="fitbar__val">{Math.round(score)}</span>
    </div>
  )
}

export function FeasibilitySection({ feasibility, recommendedVessel, delay = 0 }) {
  const port = feasibility.port ?? {}
  const vessels = feasibility.vessels ?? []
  const usable = vessels.filter((v) => v.status !== 'INFEASIBLE')
  const blocked = vessels.filter((v) => v.status === 'INFEASIBLE')

  // The cheapest hull by daily cost is not necessarily one the port can accept —
  // this is the core constraint story, derived from the feasibility response.
  const largestBlocked = blocked.reduce(
    (best, v) => (best == null || v.capacity > best.capacity ? v : best),
    null,
  )

  return (
    <Section
      id="feasibility"
      num="04"
      title="Vessel–Port Feasibility"
      sub="Which vessel classes can physically serve this port? Capacity alone does not decide."
      delay={delay}
    >
      <div className="forecast-layout">
        <Panel
          title={`Feasibility Matrix · ${feasibility.destination}`}
          right={
            <span style={{ display: 'flex', gap: 8 }}>
              <Badge tone="positive">{usable.length} usable</Badge>
              {blocked.length > 0 && <Badge tone="danger">{blocked.length} blocked</Badge>}
            </span>
          }
          bodyStyle={{ padding: 0 }}
        >
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Vessel Class</th>
                  <th className="num">Capacity</th>
                  <th className="num">Draft</th>
                  <th className="num">LOA / Beam</th>
                  <th className="num">Voyages</th>
                  <th>Port Fit</th>
                  <th>Constraints</th>
                  <th className="num">Ops Cost</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {vessels.map((v) => {
                  const tone = feasibilityTone(v.status)
                  const isSelected = recommendedVessel?.vessel_type === v.vessel_type
                  const infeasible = v.status === 'INFEASIBLE'
                  return (
                    <tr
                      key={v.vessel_type}
                      className={`${isSelected ? 'row--selected' : ''} ${
                        infeasible ? 'row--infeasible' : ''
                      }`}
                    >
                      <td className="no-dim">
                        <span className="vesselname">
                          {v.vessel_type}
                          {isSelected && <span className="vesselname__tag">SELECTED</span>}
                        </span>
                      </td>
                      <td className="num">{fmtTonnes(v.capacity, { compact: true })}</td>
                      <td className="num" style={{ color: TONE_COLOR[tone] }}>
                        {v.draft} m
                      </td>
                      <td className="num" style={{ color: 'var(--text-dim)' }}>
                        {v.loa} / {v.beam}
                      </td>
                      <td className="num">{infeasible ? '—' : v.voyages_required}</td>
                      <td>
                        <FitBar score={v.fit_score} tone={tone} />
                      </td>
                      <td>
                        <div className="chiprow">
                          {v.failed_constraints?.length > 0 ? (
                            v.failed_constraints.map((c) => (
                              <span key={c} className="chip chip--fail">
                                ✕ {prettyConstraint(c)}
                              </span>
                            ))
                          ) : (
                            <span className="chip chip--pass">✓ All clear</span>
                          )}
                          {v.lightering?.required && (
                            <span className="chip" style={{ color: 'var(--amber)' }}>
                              Lightering {fmtTonnes(v.lightering.lightering_quantity, { compact: true })}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="num">
                        {infeasible ? '—' : fmtMoney(v.total_operational_cost, { compact: true })}
                      </td>
                      <td className="no-dim">
                        <Badge tone={tone}>{feasibilityLabel(v.status)}</Badge>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {largestBlocked && (
            <div style={{ padding: '0 16px 16px' }}>
              <div className="callout">
                <span>⚠</span>
                <span>
                  <strong>Cheaper per tonne ≠ usable.</strong> {largestBlocked.vessel_type} offers
                  the largest parcel at {fmtTonnes(largestBlocked.capacity, { compact: true })}, but
                  fails{' '}
                  <strong>
                    {largestBlocked.failed_constraints.map(prettyConstraint).join(', ')}
                  </strong>{' '}
                  at {port.port} (max draft {port.max_draft} m, max LOA {port.max_loa} m, max beam{' '}
                  {port.max_beam} m). A hull that violates a hard port constraint is never
                  recommended, regardless of freight economics.
                </span>
              </div>
            </div>
          )}

          {recommendedVessel?.lightering?.required && (
            <div style={{ padding: '0 16px 16px' }}>
              <div className="callout">
                <span>⚓</span>
                <span>
                  <strong>Lightering required.</strong> The selected{' '}
                  {recommendedVessel.vessel_type} discharges{' '}
                  {fmtTonnes(recommendedVessel.lightering.lightering_quantity)} at anchorage,
                  adding {fmtMoney(recommendedVessel.lightering.incremental_cost)} and{' '}
                  {recommendedVessel.lightering.incremental_days} days per voyage · operational
                  risk {recommendedVessel.lightering.operational_risk}.
                </span>
              </div>
            </div>
          )}
        </Panel>

        <div className="signalstack">
          <Panel title={`Port Specification · ${port.port ?? '—'}`} bodyStyle={{ padding: '10px 15px' }}>
            <KV k="Max draft" v={`${port.max_draft} m`} />
            <KV k="Max LOA" v={`${port.max_loa} m`} />
            <KV k="Max beam" v={`${port.max_beam} m`} />
            <KV k="Handling rate" v={`${Number(port.cargo_handling_rate).toLocaleString()} t/day`} />
            <KV k="Berths" v={port.berth_capacity} />
            <KV k="Congestion index" v={port.congestion_index} />
            <KV k="Lightering" v={port.lightering_available ? 'Available' : 'Not available'} />
            {port.lightering_available && (
              <KV
                k="Lightering capacity"
                v={fmtTonnes(port.lightering_capacity, { compact: true })}
              />
            )}
          </Panel>

          {recommendedVessel && (
            <Panel title="Selected Vessel — Port Time" bodyStyle={{ padding: '10px 15px' }}>
              <KV k="Parcel per voyage" v={fmtTonnes(recommendedVessel.parcel_capacity)} />
              <KV k="Voyages required" v={recommendedVessel.voyages_required} />
              <KV k="Handling days (total)" v={recommendedVessel.handling_days} />
              <KV k="Waiting days (total)" v={recommendedVessel.waiting_days} />
              <KV k="Port time (total)" v={`${recommendedVessel.port_time_days} days`} />
              <KV k="Fit score" v={`${recommendedVessel.fit_score} / 100`} />
            </Panel>
          )}

          {recommendedVessel?.fit_reasons?.length > 0 && (
            <Panel title="Why This Hull" bodyStyle={{ padding: '12px 15px' }}>
              <ul className="assumption-list" style={{ marginTop: 0 }}>
                {recommendedVessel.fit_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </Panel>
          )}
        </div>
      </div>
    </Section>
  )
}
