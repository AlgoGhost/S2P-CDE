import { Badge, CountUp, KV, Panel, Section } from './common'
import { CURRENCY_CODE, buildCostBreakdown, fmtMoney, fmtRate, fmtTonnes } from '../lib/format'

export function CostSection({ forecast, feasibility, optimize, request, delay = 0 }) {
  const vessel = feasibility?.recommended_vessel
  const breakdown = buildCostBreakdown({
    forecast: forecast?.forecast,
    vessel,
    recommendation: optimize.recommendation,
    cargoQuantity: request.cargo_quantity,
  })

  return (
    <Section
      id="cost"
      num="10"
      title="Expected Cost Breakdown"
      sub="What drives the number? Components the prototype does not model are declared, not filled in."
      delay={delay}
    >
      <div className="cost-layout">
        <Panel
          title="Recommended Programme — Cost Composition"
          right={<Badge>{CURRENCY_CODE} · Modelled</Badge>}
        >
          {breakdown.rows.map((row) => (
            <div
              className={`costrow ${row.unavailable ? 'costrow--na' : ''}`}
              key={row.label}
            >
              <span className="costrow__label">{row.label}</span>
              <span className="costrow__note">{row.note}</span>
              {row.unavailable || row.value == null ? (
                <span className="costrow__na">Not available in prototype</span>
              ) : (
                <span
                  className="costrow__amount"
                  style={{
                    color:
                      row.signed && row.value < 0
                        ? 'var(--green)'
                        : row.signed && row.value > 0
                          ? 'var(--amber)'
                          : 'var(--text)',
                  }}
                >
                  {row.signed && row.value > 0 ? '+' : row.signed && row.value < 0 ? '−' : ''}
                  {fmtMoney(Math.abs(row.value))}
                </span>
              )}
            </div>
          ))}

          <div className="costtotal">
            <span className="costtotal__label">Total Expected Cost</span>
            <span className="costrow__note">
              As returned by the optimizer for the recommended structure
            </span>
            <span className="costtotal__amount">
              <CountUp value={breakdown.total} format={(v) => fmtMoney(v)} />
            </span>
          </div>

          <div className="callout callout--info">
            <span>ⓘ</span>
            <span>
              Freight is <strong>{fmtRate(forecast?.forecast)}/t × {fmtTonnes(request.cargo_quantity)}</strong>{' '}
              from the forecast engine; port, demurrage and lightering come from the feasibility
              engine for the selected {vessel?.vessel_type}. The charter-structure adjustment is the
              exact difference between the optimizer’s expected cost and those components — the
              engine’s own multiplier, surfaced rather than estimated.
            </span>
          </div>
        </Panel>

        <div className="signalstack">
          <div className="bigstat">
            <div className="bigstat__label">Expected Cost / Tonne</div>
            <div className="bigstat__value">
              <CountUp value={breakdown.perTonne} format={(v) => fmtRate(v)} />
            </div>
            <div className="bigstat__note">
              Risk-adjusted, modelled on prototype/proxy market data. Delivered basis at{' '}
              {feasibility?.port?.port}.
            </div>
          </div>

          <Panel title="Operational Detail" bodyStyle={{ padding: '12px 15px' }}>
            <KV k="Total operational cost" v={fmtMoney(breakdown.operational)} />
            <KV k="Port charges" v={fmtMoney(vessel?.port_cost)} />
            <KV k="Demurrage exposure" v={fmtMoney(vessel?.demurrage_exposure)} />
            <KV
              k="Lightering"
              v={vessel?.lightering_cost ? fmtMoney(vessel.lightering_cost) : 'Not required'}
            />
            <KV k="Total port time" v={`${vessel?.port_time_days ?? '—'} days`} />
            <KV k="Voyages" v={optimize.voyages} />
          </Panel>

          {feasibility?.assumptions?.length > 0 && (
            <Panel title="Feasibility Assumptions" bodyStyle={{ padding: '12px 15px' }}>
              <ul className="assumption-list" style={{ marginTop: 0 }}>
                {feasibility.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </Panel>
          )}
        </div>
      </div>
    </Section>
  )
}

/** Layers reflect what is actually in this repository — no aspirational tech. */
const ARCH_LAYERS = [
  { layer: 'Data Adapter', tech: 'pandas · CSV proxy feeds\nswappable source interface' },
  { layer: 'Forecast Engine', tech: 'statsmodels SARIMAX\n→ moving average → naive\nwalk-forward validation' },
  { layer: 'Feasibility Engine', tech: 'Deterministic constraint\nchecks: draft / LOA / beam\nlightering evaluation' },
  { layer: 'Risk Engine', tech: 'Weighted multi-factor\ncomposite scoring' },
  { layer: 'Optimizer', tech: 'Charter structure\ncost comparison\n+ risk penalties' },
  { layer: 'Scenario Engine', tech: 'Re-solves the decision\nunder freight, congestion\nand availability shocks' },
  { layer: 'Decision API', tech: 'FastAPI · Pydantic v2\nOpenAPI at /docs' },
  { layer: 'Cockpit', tech: 'React 18 · Vite\nhand-built SVG charts' },
]

export function ArchitectureSection({ delay = 0 }) {
  return (
    <Section
      id="architecture"
      num="11"
      title="Decision Architecture"
      sub="Each layer is an independent, testable engine — the data adapter is the only thing production would need to swap."
      delay={delay}
    >
      <div className="archrail">
        {ARCH_LAYERS.map((a, i) => (
          <div className="arch reveal" key={a.layer} style={{ animationDelay: `${i * 60}ms` }}>
            <div className="eyebrow">Layer {String(i + 1).padStart(2, '0')}</div>
            <div className="arch__layer">{a.layer}</div>
            <div className="arch__tech" style={{ whiteSpace: 'pre-line' }}>
              {a.tech}
            </div>
            <div className="arch__bar" />
          </div>
        ))}
      </div>
      <div className="callout callout--info">
        <span>ⓘ</span>
        <span>
          Only technologies present in this repository are listed. The prototype does not use a
          database, OR-Tools, or any live market feed — the freight series is a generated proxy
          dataset committed to <strong>backend/data/</strong>.
        </span>
      </div>
    </Section>
  )
}

export function Transparency({ dataStatus, forecastSource, observations }) {
  return (
    <div className="transparency reveal">
      <div className="transparency__grid">
        <div>
          <div className="transparency__title">Data Status</div>
          <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <Badge>Prototype / Proxy Dataset</Badge>
            {forecastSource && <Badge>{forecastSource}</Badge>}
          </div>
          {observations != null && (
            <div className="signalcard__note" style={{ marginTop: 8 }}>
              {observations} observations on the analysed lane.
            </div>
          )}
        </div>
        <div className="transparency__body">
          <p>
            Every figure in this cockpit is computed by the VARUNEETI engines from a{' '}
            <strong>generated prototype dataset</strong>. It contains no proprietary SAIL data, no
            Baltic Exchange data, and no licensed market feed. Costs shown are{' '}
            <strong>modelled expected values under stated assumptions</strong> — not quotes, not
            realised results, and not guaranteed savings.
          </p>
          <p>
            This prototype demonstrates the complete decision architecture end to end. A production
            deployment would connect representative SAIL and licensed market/operational feeds
            through the existing data adapter layer without changing the forecasting, feasibility,
            risk or optimization engines.
          </p>
          <p style={{ color: 'var(--text-dim)' }}>
            VARUNEETI is a <strong>decision-support</strong> system with a human in the loop. It
            recommends and explains; the chartering desk decides.
          </p>
          {dataStatus && Object.keys(dataStatus).length > 0 && (
            <p className="mono" style={{ fontSize: 10.5, color: 'var(--text-dim)' }}>
              engine data_status: {JSON.stringify(dataStatus)}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
