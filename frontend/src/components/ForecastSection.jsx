import { useMemo } from 'react'
import { Badge, CountUp, KV, Panel, Section, useGrow } from './common'
import { CURRENCY_CODE, fmtRate, trendGlyph, trendTone } from '../lib/format'

// Viewbox aspect is kept close to the rendered panel so the chart can scale
// uniformly — stretching it non-uniformly would distort labels and markers.
const W = 1200
const H = 340
const PAD = { top: 18, right: 20, bottom: 30, left: 56 }

/**
 * Freight outlook chart.
 *
 * Renders exactly what /api/forecast returns: the historical observations used
 * to fit the model, the projected point(s), and the 95% prediction interval.
 * Nothing is interpolated or invented — if the API returns a single forecast
 * period (the prototype series is monthly), one period is drawn.
 */
function ForecastChart({ historical, forecastPts }) {
  const geom = useMemo(() => {
    const all = [...historical, ...forecastPts]
    if (all.length < 2) return null

    const values = [
      ...all.map((p) => p.value),
      ...forecastPts.flatMap((p) => [p.lower, p.upper].filter((v) => v != null)),
    ]
    const min = Math.min(...values)
    const max = Math.max(...values)
    const pad = (max - min) * 0.15 || 1
    const yMin = Math.max(0, min - pad)
    const yMax = max + pad

    const innerW = W - PAD.left - PAD.right
    const innerH = H - PAD.top - PAD.bottom
    const x = (i) => PAD.left + (i / (all.length - 1)) * innerW
    const y = (v) => PAD.top + innerH - ((v - yMin) / (yMax - yMin)) * innerH

    const histPath = historical.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)} ${y(p.value)}`).join(' ')

    // The projection starts at the last observed point so the line is continuous.
    const lastHist = historical[historical.length - 1]
    const lastIdx = historical.length - 1
    const fcPath = [
      `M${x(lastIdx)} ${y(lastHist.value)}`,
      ...forecastPts.map((p, i) => `L${x(historical.length + i)} ${y(p.value)}`),
    ].join(' ')

    // Uncertainty cone: fans out from the last observation to each bound.
    const hasBand = forecastPts.some((p) => p.lower != null && p.upper != null)
    let bandPath = null
    if (hasBand) {
      const upper = forecastPts.map(
        (p, i) => `L${x(historical.length + i)} ${y(p.upper ?? p.value)}`,
      )
      const lower = [...forecastPts]
        .map((p, i) => ({ p, i }))
        .reverse()
        .map(({ p, i }) => `L${x(historical.length + i)} ${y(p.lower ?? p.value)}`)
      bandPath = [
        `M${x(lastIdx)} ${y(lastHist.value)}`,
        ...upper,
        ...lower,
        'Z',
      ].join(' ')
    }

    const ticks = 4
    const yTicks = Array.from({ length: ticks + 1 }, (_, i) => {
      const v = yMin + ((yMax - yMin) * i) / ticks
      return { v, y: y(v) }
    })

    const labelEvery = Math.max(1, Math.ceil(all.length / 8))
    const xTicks = all
      .map((p, i) => ({ i, date: p.date }))
      .filter(({ i }) => i % labelEvery === 0 || i === all.length - 1)
      .map(({ i, date }) => ({
        x: x(i),
        label: String(date).slice(0, 7),
        // Keep the first/last labels inside the plot instead of half-clipped.
        anchor: i === 0 ? 'start' : i === all.length - 1 ? 'end' : 'middle',
      }))

    return {
      histPath,
      fcPath,
      bandPath,
      yTicks,
      xTicks,
      forecastMarkers: forecastPts.map((p, i) => ({
        cx: x(historical.length + i),
        cy: y(p.value),
        value: p.value,
      })),
      splitX: x(lastIdx),
      splitNearEdge: x(lastIdx) > W - PAD.right - 130,
    }
  }, [historical, forecastPts])

  if (!geom) {
    return (
      <p className="placeholder__text">
        The forecast response did not contain enough series points to plot a chart.
      </p>
    )
  }

  return (
    <div className="chartwrap">
      <svg
        className="chart-svg"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Freight rate history and forecast"
      >
        <defs>
          <linearGradient id="histFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
        </defs>

        <g className="chart-grid">
          {geom.yTicks.map((t) => (
            <line key={t.v} x1={PAD.left} x2={W - PAD.right} y1={t.y} y2={t.y} />
          ))}
        </g>

        <g className="chart-axis">
          {geom.yTicks.map((t) => (
            <text key={t.v} x={PAD.left - 9} y={t.y + 3} textAnchor="end">
              {t.v.toFixed(0)}
            </text>
          ))}
          {geom.xTicks.map((t) => (
            <text key={t.label + t.x} x={t.x} y={H - 9} textAnchor={t.anchor}>
              {t.label}
            </text>
          ))}
        </g>

        {/* Filled area under the observed history */}
        <path
          className="chart-fade"
          d={`${geom.histPath} L${geom.splitX} ${H - PAD.bottom} L${PAD.left} ${H - PAD.bottom} Z`}
          fill="url(#histFill)"
        />

        {/* 95% prediction interval */}
        {geom.bandPath && (
          <path
            className="chart-fade"
            d={geom.bandPath}
            fill="rgba(34,211,238,0.16)"
            stroke="rgba(34,211,238,0.32)"
            strokeWidth="1"
          />
        )}

        {/* Forecast boundary */}
        <line
          x1={geom.splitX}
          x2={geom.splitX}
          y1={PAD.top}
          y2={H - PAD.bottom}
          stroke="rgba(255,255,255,0.22)"
          strokeWidth="1"
          strokeDasharray="3 4"
        />
        {/* With a short horizon the split sits near the right edge, so the
            label flips inside the history rather than overflowing the panel. */}
        <text
          x={geom.splitNearEdge ? geom.splitX - 7 : geom.splitX + 7}
          y={PAD.top + 11}
          textAnchor={geom.splitNearEdge ? 'end' : 'start'}
          fill="#6b7c96"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          {geom.splitNearEdge ? '← OBSERVED | FORECAST →' : 'FORECAST →'}
        </text>

        <path
          className="chart-draw"
          pathLength="1"
          d={geom.histPath}
          fill="none"
          stroke="#60a5fa"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />

        <path
          className="chart-fade"
          d={geom.fcPath}
          fill="none"
          stroke="#22d3ee"
          strokeWidth="2.2"
          strokeDasharray="6 4"
          strokeLinecap="round"
        />

        {geom.forecastMarkers.map((m) => (
          <g key={m.cx} className="chart-fade">
            <circle cx={m.cx} cy={m.cy} r="4.5" fill="#22d3ee" />
            <circle cx={m.cx} cy={m.cy} r="8.5" fill="rgba(34,211,238,0.2)" />
          </g>
        ))}
      </svg>

      <div className="chart-legend">
        <span className="chart-legend__item">
          <span className="chart-legend__swatch" style={{ background: '#60a5fa' }} />
          Observed freight rate ({CURRENCY_CODE}/tonne, prototype proxy series)
        </span>
        <span className="chart-legend__item">
          <span
            className="chart-legend__swatch"
            style={{ background: 'repeating-linear-gradient(90deg,#22d3ee 0 5px,transparent 5px 8px)' }}
          />
          Model forecast
        </span>
        <span className="chart-legend__item">
          <span
            className="chart-legend__swatch"
            style={{ background: 'rgba(34,211,238,0.35)', height: 10 }}
          />
          95% prediction interval
        </span>
      </div>
    </div>
  )
}

export function ForecastSection({ forecast, recommendedVessel, delay = 0 }) {
  // The optimizer and risk engine both price the programme off the Panamax
  // benchmark lane regardless of which hull is finally selected, so we say so
  // rather than let the mismatch read as an inconsistency.
  const benchmarkDiffers =
    recommendedVessel && forecast.vessel_type && recommendedVessel !== forecast.vessel_type

  const confidencePct = Math.round((forecast.confidence ?? 0) * 100)
  const confW = useGrow(confidencePct, 320)

  const spread =
    forecast.upper_bound != null && forecast.lower_bound != null && forecast.forecast
      ? ((forecast.upper_bound - forecast.lower_bound) / forecast.forecast) * 100
      : null

  const uncertaintyNote = {
    LOW: 'Recent observations are tightly clustered.',
    MEDIUM: 'Moderate dispersion in recent observations.',
    HIGH: 'Wide dispersion — rate protection carries more value.',
  }[forecast.volatility]

  return (
    <Section
      id="forecast"
      num="03"
      title="Freight Outlook"
      sub="What will the market do? Point forecast with prediction interval for the benchmark lane."
      delay={delay}
    >
      <div className="forecast-layout">
        <Panel
          title={`${forecast.origin} → ${forecast.destination} · ${forecast.vessel_type} benchmark`}
          right={
            <span style={{ display: 'flex', gap: 8 }}>
              <Badge tone={forecast.model_wins ? 'positive' : 'warning'}>
                {forecast.model_wins ? 'Beats naive baseline' : 'Baseline competitive'}
              </Badge>
              <Badge>Prototype / Proxy Data</Badge>
            </span>
          }
        >
          <ForecastChart
            historical={forecast.historical_series ?? []}
            forecastPts={forecast.forecast_series ?? []}
          />
          {(forecast.forecast_series?.length ?? 0) === 1 && (
            <div className="callout callout--info">
              <span>ⓘ</span>
              <span>
                The prototype freight series is <strong>monthly</strong>, so a{' '}
                {forecast.horizon_days}-day horizon resolves to a single projected period. A higher
                frequency feed through the same adapter would produce a denser forecast path.
              </span>
            </div>
          )}
          {benchmarkDiffers && (
            <div className="callout callout--info">
              <span>ⓘ</span>
              <span>
                The charter optimizer and risk engine price this programme off the{' '}
                <strong>{forecast.vessel_type} benchmark rate</strong> for the lane, while the
                feasibility engine selected a <strong>{recommendedVessel}</strong> because{' '}
                {forecast.vessel_type} cannot physically call at {forecast.destination}. The
                benchmark sets the market level; the feasible hull sets the operational cost.
              </span>
            </div>
          )}
          {forecast.warnings?.length > 0 && (
            <div className="callout">
              <span>⚠</span>
              <span>{forecast.warnings.join(' ')}</span>
            </div>
          )}
        </Panel>

        <div className="signalstack">
          <div className="signalcard">
            <div className="signalcard__label">Forecast Signal</div>
            <div className={`signalcard__value tone-${trendTone(forecast.trend)}`}>
              {trendGlyph(forecast.trend)} {forecast.trend}
            </div>
            <div className="signalcard__note">
              {forecast.horizon_days}-day outlook ·{' '}
              <CountUp value={forecast.forecast} format={(v) => fmtRate(v)} />/tonne
            </div>
          </div>

          <div className="signalcard">
            <div className="signalcard__label">Uncertainty</div>
            <div
              className={`signalcard__value tone-${
                forecast.volatility === 'LOW'
                  ? 'positive'
                  : forecast.volatility === 'HIGH'
                    ? 'danger'
                    : 'warning'
              }`}
            >
              {forecast.volatility}
            </div>
            <div className="signalcard__note">{uncertaintyNote}</div>
          </div>

          <div className="signalcard">
            <div className="signalcard__label">Model Confidence</div>
            <div className="signalcard__value">
              <CountUp value={confidencePct} format={(v) => `${v.toFixed(0)}%`} />
            </div>
            <div className="meter">
              <span style={{ width: `${confW}%` }} />
            </div>
            <div className="signalcard__note">
              Composite heuristic (validation, data volume, horizon, volatility) — not a calibrated
              probability.
            </div>
          </div>

          <Panel title="Model Validation" bodyStyle={{ padding: '10px 15px' }}>
            <KV k="Selected model" v={forecast.model_name} />
            <KV
              k="95% interval"
              v={`${fmtRate(forecast.lower_bound)} – ${fmtRate(forecast.upper_bound)}`}
            />
            {spread != null && <KV k="Interval width" v={`±${(spread / 2).toFixed(1)}%`} />}
            <KV k="Model MAE" v={forecast.model_error?.mae?.toFixed(2) ?? '—'} />
            <KV k="Naive baseline MAE" v={forecast.baseline_error?.mae?.toFixed(2) ?? '—'} />
            <KV
              k="Model MAPE"
              v={forecast.model_error?.mape != null ? `${forecast.model_error.mape}%` : '—'}
            />
            <KV k="Observations" v={forecast.historical_series?.length ?? 0} />
          </Panel>
        </div>
      </div>
    </Section>
  )
}
