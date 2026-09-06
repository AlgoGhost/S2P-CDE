import { useEffect, useRef, useState } from 'react'

/** Section wrapper with a numbered heading — drives the sidebar anchors. */
export function Section({ id, num, title, sub, children, delay = 0 }) {
  return (
    <section id={id} className="section reveal" style={{ animationDelay: `${delay}ms` }}>
      <div className="section__head">
        {num && <span className="section__num">{num}</span>}
        <h2 className="section__title">{title}</h2>
        {sub && <p className="section__sub">{sub}</p>}
      </div>
      {children}
    </section>
  )
}

export function Panel({ title, right, children, bodyStyle, className = '' }) {
  return (
    <div className={`panel ${className}`}>
      {(title || right) && (
        <div className="panel__head">
          {title && <span className="panel__title">{title}</span>}
          {right && <span style={{ marginLeft: 'auto' }}>{right}</span>}
        </div>
      )}
      <div className="panel__body" style={bodyStyle}>
        {children}
      </div>
    </div>
  )
}

export function Badge({ tone = 'proto', children }) {
  return <span className={`badge badge--${tone}`}>{children}</span>
}

export function KV({ k, v }) {
  return (
    <div className="kv">
      <span className="kv__k">{k}</span>
      <span className="kv__v">{v}</span>
    </div>
  )
}

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

/**
 * Count a number up from zero on mount. `format` receives the interpolated
 * value; the final frame always uses the exact target so the displayed figure
 * is byte-identical to the API value.
 */
export function CountUp({ value, format = (v) => v.toFixed(0), duration = 950, delay = 0 }) {
  const [display, setDisplay] = useState(() =>
    typeof value === 'number' && Number.isFinite(value) ? 0 : value,
  )
  const frame = useRef(0)
  const timer = useRef(0)

  useEffect(() => {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      setDisplay(value)
      return undefined
    }
    if (prefersReducedMotion()) {
      setDisplay(value)
      return undefined
    }

    setDisplay(0)
    const start = () => {
      const t0 = performance.now()
      const tick = (now) => {
        const p = Math.min(1, (now - t0) / duration)
        // easeOutExpo — fast settle, no overshoot
        const eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p)
        setDisplay(p === 1 ? value : value * eased)
        if (p < 1) frame.current = requestAnimationFrame(tick)
      }
      frame.current = requestAnimationFrame(tick)
    }

    timer.current = window.setTimeout(start, delay)
    return () => {
      window.clearTimeout(timer.current)
      cancelAnimationFrame(frame.current)
    }
  }, [value, duration, delay])

  if (typeof value !== 'number' || !Number.isFinite(value)) return <>{value ?? '—'}</>
  return <>{format(display)}</>
}

/** Animate a bar/meter width in after mount so the fill transition can run. */
export function useGrow(target, delay = 120) {
  const [w, setW] = useState(0)
  useEffect(() => {
    if (prefersReducedMotion()) {
      setW(target)
      return undefined
    }
    setW(0)
    const t = window.setTimeout(() => setW(target), delay)
    return () => window.clearTimeout(t)
  }, [target, delay])
  return w
}
