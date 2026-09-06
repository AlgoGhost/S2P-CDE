import { Badge, CountUp, KV, Panel, Section, useGrow } from './common'
import { fmtMoney, fmtRate, fmtTonnes, prettyStrategy } from '../lib/format'

/** Rate exposure is a direct read of lock_percentage — not a separate model. */
function exposureLabel(lockPct) {
  if (lockPct >= 100) return { text: 'None — fully covered', tone: 'positive' }
  if (lockPct <= 0) return { text: 'Full — every tonne at spot', tone: 'danger' }
  return { text: `Partial — ${100 - lockPct}% at spot`, tone: 'warning' }
}

function StrategyCard({ item, spotCost, isBest, cargoQuantity }) {
  const delta = spotCost != null ? spotCost - item.cost : null
  const deltaPct = delta != null && spotCost ? (delta / spotCost) * 100 : null
  const isSpot = item.strategy === 'SPOT'
  const exposure = exposureLabel(item.lock_percentage)
  const lockW = useGrow(item.lock_percentage, 280)

  let deltaCls = 'strat__delta--base'
  let deltaText = 'Reference case'
  if (!isSpot && delta != null) {
    if (delta > 0) {
      deltaCls = 'strat__delta--save'
      deltaText = `▼ ${fmtMoney(delta, { compact: true })} modelled saving vs spot (${deltaPct.toFixed(1)}%)`
    } else if (delta < 0) {
      deltaCls = 'strat__delta--cost'
      deltaText = `▲ ${fmtMoney(Math.abs(delta), { compact: true })} above spot (${Math.abs(deltaPct).toFixed(1)}%)`
    } else {
      deltaText = 'Level with spot'
    }
  }

  return (
    <div className={`strat ${isBest ? 'strat--best' : ''}`}>
      {isBest && <span className="strat__flag">RECOMMENDED</span>}
      <div className="strat__name">{prettyStrategy(item.strategy)}</div>

      <div className="strat__cpt">
        <CountUp value={item.cost_per_tonne} format={(v) => fmtRate(v)} />
        <span className="strat__cpt-unit"> /t</span>
      </div>
      <div className="strat__total">{fmtMoney(item.cost)} expected total</div>

      <div className={`strat__delta ${deltaCls}`}>{deltaText}</div>

      <div className="strat__rows">
        <KV k="Tonnage locked" v={`${item.lock_percentage}%`} />
        <KV k="Locked" v={fmtTonnes(item.locked_tonnage, { compact: true })} />
        <KV k="Flexible" v={fmtTonnes(item.flexible_tonnage, { compact: true })} />
        <KV k="Rate exposure" v={<span className={`tone-${exposure.tone}`}>{exposure.text}</span>} />
      </div>

      <div className="strat__split" title={`${item.lock_percentage}% locked`}>
        <div className="strat__split-lock" style={{ width: `${lockW}%` }} />
        <div className="strat__split-flex" style={{ width: `${100 - lockW}%` }} />
      </div>
    </div>
  )
}

/**
 * Cost bars are zero-baselined — the honest encoding — which means the four
 * structures look similar because they genuinely differ by only a few percent.
 * The saving chart below carries the discriminating signal.
 */
function CostBar({ item, maxCpt, isBest }) {
  const w = useGrow((item.cost_per_tonne / maxCpt) * 100, 320)
  return (
    <div className="costbar">
      <span className="costbar__name">{prettyStrategy(item.strategy)}</span>
      <span className="costbar__track">
        <span
          className={`costbar__fill ${isBest ? 'costbar__fill--best' : ''}`}
          style={{ width: `${w}%` }}
        />
      </span>
      <span className="costbar__val" style={{ color: isBest ? 'var(--cyan)' : 'var(--text)' }}>
        {fmtRate(item.cost_per_tonne)} /t {isBest && '←'}
      </span>
    </div>
  )
}

function SavingBar({ item, saving, maxSaving, isBest }) {
  const pct = maxSaving > 0 ? (Math.max(0, saving) / maxSaving) * 100 : 0
  const w = useGrow(pct, 380)
  const isSpot = item.strategy === 'SPOT'
  return (
    <div className="costbar">
      <span className="costbar__name">{prettyStrategy(item.strategy)}</span>
      <span className="costbar__track">
        <span
          className="costbar__fill"
          style={{
            width: `${w}%`,
            background: isBest
              ? 'linear-gradient(90deg, var(--green), #4ade80)'
              : 'linear-gradient(90deg, rgba(34,197,94,0.3), rgba(34,197,94,0.55))',
          }}
        />
      </span>
      <span
        className="costbar__val"
        style={{ color: isBest ? '#6ee7a0' : isSpot ? 'var(--text-dim)' : 'var(--text)' }}
      >
        {isSpot ? 'baseline' : fmtMoney(saving, { compact: true })} {isBest && '←'}
      </span>
    </div>
  )
}

export function StrategySection({ optimize, riskScore, cargoQuantity, delay = 0 }) {
  const items = optimize.strategy_comparison ?? []
  if (items.length === 0) {
    return (
      <Section id="strategy" num="06" title="Charter Strategy Comparison" delay={delay}>
        <div className="placeholder">
          <div className="placeholder__title">No strategies to compare</div>
          <p className="placeholder__text">
            The optimizer could not construct a feasible charter programme for this requirement.
          </p>
        </div>
      </Section>
    )
  }

  const best = optimize.recommendation?.strategy
  const spot = items.find((i) => i.strategy === 'SPOT')
  const maxCpt = Math.max(...items.map((i) => i.cost_per_tonne))
  const bestItem = items.find((i) => i.strategy === best)
  const saving = spot && bestItem ? spot.cost - bestItem.cost : null
  const savingPct = saving != null && spot?.cost ? (saving / spot.cost) * 100 : null
  const maxSaving = spot ? Math.max(0, ...items.map((i) => spot.cost - i.cost)) : 0

  return (
    <Section
      id="strategy"
      num="06"
      title="Charter Strategy Comparison"
      sub="Four chartering structures, costed on the same forecast and the same feasible vessel."
      delay={delay}
    >
      <div className="stratgrid">
        {items.map((item) => (
          <StrategyCard
            key={item.strategy}
            item={item}
            spotCost={spot?.cost}
            isBest={item.strategy === best}
            cargoQuantity={cargoQuantity}
          />
        ))}
      </div>

      <div style={{ marginTop: 14 }} className="cost-layout">
        <Panel title="Expected Cost per Tonne" right={<Badge>Modelled · Prototype</Badge>}>
          <div className="costbars">
            {items.map((item) => (
              <CostBar
                key={item.strategy}
                item={item}
                maxCpt={maxCpt}
                isBest={item.strategy === best}
              />
            ))}
          </div>

          {maxSaving > 0 && (
            <>
              <div
                className="eyebrow"
                style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--line)' }}
              >
                Modelled saving vs all-spot baseline
              </div>
              <div className="costbars">
                {items.map((item) => (
                  <SavingBar
                    key={item.strategy}
                    item={item}
                    saving={spot ? spot.cost - item.cost : 0}
                    maxSaving={maxSaving}
                    isBest={item.strategy === best}
                  />
                ))}
              </div>
            </>
          )}

          <div className="callout callout--info">
            <span>ⓘ</span>
            <span>
              Charter-structure cost multipliers and the risk penalty applied to longer locks are{' '}
              <strong>prototype assumptions</strong> stated by the optimizer, not observed market
              spreads. Figures are modelled expected costs — not quotes, and not guaranteed
              savings.
            </span>
          </div>
        </Panel>

        <div className="signalstack">
          {saving != null && saving > 0 && (
            <div className="bigstat">
              <div className="bigstat__label">Modelled Saving vs Spot</div>
              <div className="bigstat__value">
                <CountUp value={saving} format={(v) => fmtMoney(v, { compact: true })} />
              </div>
              <div className="bigstat__note">
                {savingPct.toFixed(1)}% below the all-spot reference case for the same{' '}
                {fmtTonnes(cargoQuantity)} programme. Modelled under stated prototype assumptions —
                not a realised or guaranteed saving.
              </div>
            </div>
          )}

          <Panel title="Programme Decision Risk" bodyStyle={{ padding: '12px 15px' }}>
            <KV k="Composite risk score" v={`${riskScore ?? '—'} / 100`} />
            <KV k="Recommended structure" v={prettyStrategy(best)} />
            <KV
              k="Tonnage committed"
              v={fmtTonnes(optimize.recommendation?.locked_tonnage, { compact: true })}
            />
            <KV
              k="Tonnage left open"
              v={fmtTonnes(optimize.recommendation?.flexible_tonnage, { compact: true })}
            />
            <p className="signalcard__note" style={{ marginTop: 10 }}>
              The risk engine scores the <strong>procurement programme</strong>, not each structure
              separately. Risk influences the comparison through the penalty the optimizer applies
              to longer commitments, and through the rate exposure each structure leaves open.
            </p>
          </Panel>
        </div>
      </div>
    </Section>
  )
}
