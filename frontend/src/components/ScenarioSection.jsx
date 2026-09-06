import { Badge, Panel, Section, useGrow } from './common'
import { fmtMoney, fmtRate, prettyStrategy } from '../lib/format'

function DeltaBar({ pct, maxAbs }) {
  // Diverging bar centred on the base case: cost increases run right (red),
  // decreases run left (green). Zero-baselined, so length is proportional.
  const magnitude = maxAbs > 0 ? (Math.abs(pct) / maxAbs) * 50 : 0
  const w = useGrow(magnitude, 300)
  const positive = pct > 0
  return (
    <div style={{ position: 'relative', height: 16, width: '100%' }}>
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: 0,
          bottom: 0,
          width: 1,
          background: 'var(--line-strong)',
        }}
      />
      {Math.abs(pct) > 0.01 && (
        <div
          style={{
            position: 'absolute',
            top: 3,
            height: 10,
            borderRadius: 2,
            left: positive ? '50%' : `${50 - w}%`,
            width: `${w}%`,
            background: positive
              ? 'linear-gradient(90deg, rgba(239,68,68,0.45), rgba(239,68,68,0.75))'
              : 'linear-gradient(90deg, rgba(34,197,94,0.75), rgba(34,197,94,0.45))',
            transition: 'width 0.9s cubic-bezier(0.2,0.8,0.2,1), left 0.9s cubic-bezier(0.2,0.8,0.2,1)',
          }}
        />
      )}
    </div>
  )
}

export function ScenarioSection({ scenarios, delay = 0 }) {
  if (!scenarios) {
    return (
      <Section
        id="scenarios"
        num="07"
        title="Scenario Stress Test"
        sub="Does the recommendation survive if the forecast is wrong?"
        delay={delay}
      >
        <div className="placeholder">
          <div className="placeholder__title">Stress test unavailable</div>
          <p className="placeholder__text">
            The scenario engine did not return a result for this run. The base recommendation
            above is unaffected.
          </p>
        </div>
      </Section>
    )
  }

  const outcomes = scenarios.outcomes ?? []
  const base = outcomes.find((o) => o.scenario_id === scenarios.base_scenario_id)
  const maxAbs = Math.max(1, ...outcomes.map((o) => Math.abs(o.cost_pct_delta_vs_base)))
  const flipped = outcomes.filter((o) => o.strategy_changed)
  const robust = scenarios.recommendation_is_robust

  return (
    <Section
      id="scenarios"
      num="07"
      title="Scenario Stress Test"
      sub="Does the recommendation survive if the forecast is wrong? Each case re-solves the full decision."
      delay={delay}
    >
      <div className={`robust-banner robust-banner--${robust ? 'robust' : 'fragile'}`}>
        <span className="robust-banner__glyph">{robust ? '✓' : '⚠'}</span>
        <span>
          <strong>{robust ? 'RECOMMENDATION IS ROBUST' : 'RECOMMENDATION IS CONDITIONAL'}</strong>
          <br />
          {scenarios.robustness_summary}
        </span>
      </div>

      <Panel
        title="Stress Cases"
        right={
          <span style={{ display: 'flex', gap: 8 }}>
            <Badge tone={robust ? 'positive' : 'warning'}>
              {flipped.length} of {Math.max(0, outcomes.length - 1)} flip the structure
            </Badge>
            <Badge>Shocks are prototype assumptions</Badge>
          </span>
        }
        bodyStyle={{ padding: 0 }}
      >
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Strategy</th>
                <th>Vessel</th>
                <th className="num">Voyages</th>
                <th className="num">Cost / t</th>
                <th className="num">Risk</th>
                <th style={{ minWidth: 130 }}>vs Base</th>
                <th className="num">Δ Cost</th>
                <th>Impact</th>
              </tr>
            </thead>
            <tbody>
              {outcomes.map((o) => {
                const isBase = o.scenario_id === scenarios.base_scenario_id
                const deltaCls =
                  o.cost_pct_delta_vs_base > 0.01
                    ? 'delta-pos'
                    : o.cost_pct_delta_vs_base < -0.01
                      ? 'delta-neg'
                      : 'delta-zero'
                return (
                  <tr
                    key={o.scenario_id}
                    className={
                      isBase
                        ? 'scenario-row--base'
                        : o.strategy_changed
                          ? 'scenario-row--flip'
                          : ''
                    }
                  >
                    <td>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{o.label}</div>
                      <div style={{ fontSize: 10.5, color: 'var(--text-dim)', maxWidth: '34ch' }}>
                        {o.notes}
                      </div>
                    </td>
                    <td>
                      <span
                        className={o.strategy_changed ? 'tone-warning' : ''}
                        style={{ fontWeight: o.strategy_changed ? 700 : 500 }}
                      >
                        {prettyStrategy(o.strategy)}
                      </span>
                    </td>
                    <td className={o.vessel_changed ? 'tone-warning' : ''}>{o.vessel_class}</td>
                    <td className="num">{o.voyages}</td>
                    <td className="num">{fmtRate(o.cost_per_tonne)}</td>
                    <td className="num">{o.risk_score.toFixed(1)}</td>
                    <td>
                      <DeltaBar pct={o.cost_pct_delta_vs_base} maxAbs={maxAbs} />
                    </td>
                    <td className={`num ${deltaCls}`}>
                      {isBase
                        ? '—'
                        : `${o.cost_pct_delta_vs_base > 0 ? '+' : ''}${o.cost_pct_delta_vs_base.toFixed(1)}%`}
                    </td>
                    <td>
                      {isBase ? (
                        <Badge tone="info">BASE</Badge>
                      ) : o.strategy_changed ? (
                        <Badge tone="warning">STRATEGY FLIPS</Badge>
                      ) : o.vessel_changed ? (
                        <Badge tone="warning">VESSEL CHANGES</Badge>
                      ) : (
                        <Badge tone="positive">HOLDS</Badge>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div style={{ padding: '0 16px 16px' }}>
          <div className="callout callout--info">
            <span>ⓘ</span>
            <span>
              Every row re-runs the <strong>complete</strong> forecast → feasibility → risk →
              strategy path with the shock applied; no costs are re-derived in the scenario
              engine. Shock magnitudes are stated prototype assumptions, and the cases are{' '}
              <strong>not probability-weighted</strong> — they are independent stress tests, so
              their costs must not be averaged into an expected value.
            </span>
          </div>
        </div>
      </Panel>
    </Section>
  )
}
