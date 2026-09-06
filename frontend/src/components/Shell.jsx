import { useEffect, useState } from 'react'
import { formatTime } from '../lib/format'

export const NAV_ITEMS = [
  { id: 'cockpit', label: 'Overview' },
  { id: 'decision', label: 'Charter Decision' },
  { id: 'forecast', label: 'Freight Forecast' },
  { id: 'feasibility', label: 'Vessel & Port' },
  { id: 'risk', label: 'Risk Radar' },
  { id: 'strategy', label: 'Strategy' },
  { id: 'scenarios', label: 'Scenarios' },
]

function Anchor() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="5" r="2.4" stroke="#fff" strokeWidth="1.7" />
      <path
        d="M12 7.6V20M6.5 11H17.5M4 15.2A8.2 8.2 0 0 0 12 20a8.2 8.2 0 0 0 8-4.8"
        stroke="#fff"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function Sidebar({ active, onNavigate, hasResult }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__mark">
          <span className="sidebar__glyph">
            <Anchor />
          </span>
          <span>
            <div className="sidebar__wordmark">VARUNEETI</div>
            <div className="sidebar__tag">Decision Intelligence</div>
          </span>
        </div>
      </div>

      <nav className="sidebar__nav">
        <div className="sidebar__section-label eyebrow">Decision Loop</div>
        {NAV_ITEMS.map((item, i) => (
          <button
            key={item.id}
            type="button"
            className={`navitem ${active === item.id ? 'is-active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="navitem__idx">{String(i + 1).padStart(2, '0')}</span>
            <span>{item.label}</span>
            {hasResult && item.id !== 'cockpit' && <span className="navitem__dot" />}
          </button>
        ))}
      </nav>

      <div className="sidebar__foot">
        <div className="sidebar__foot-title">SAIL • SIH 2026</div>
        <div className="sidebar__foot-sub">Prototype Decision Support</div>
        <div className="sidebar__foot-sub" style={{ marginTop: 6 }}>
          PS26006 · Ministry of Steel
        </div>
      </div>
    </aside>
  )
}

export function Header({ backendStatus, lastRun, live }) {
  const [, setTick] = useState(0)
  // Re-render once a minute so "last calculation" stays honest during a demo.
  useEffect(() => {
    const t = window.setInterval(() => setTick((n) => n + 1), 60000)
    return () => window.clearInterval(t)
  }, [])

  const statusMap = {
    online: { cls: 'online', text: 'System Online' },
    offline: { cls: 'offline', text: 'Engine Unreachable' },
    checking: { cls: 'checking', text: 'Connecting' },
  }
  const status = statusMap[backendStatus] ?? statusMap.checking

  return (
    <header className="header">
      <div>
        <div className="header__title">VARUNEETI</div>
        <div className="header__sub">Maritime Charter Decision Intelligence</div>
      </div>
      <div className="header__tagline">“From freight prediction to charter decision.”</div>

      <div className="header__right">
        <div className="header__meta">
          <div className="header__meta-label">Data</div>
          <div className="header__meta-value">PROTOTYPE / PROXY</div>
        </div>
        <div className="header__meta">
          <div className="header__meta-label">Last Calculation</div>
          <div className="header__meta-value">
            {lastRun ? `${formatTime(lastRun)}${live ? '' : ' · SNAPSHOT'}` : '—'}
          </div>
        </div>
        <span className={`status-pill status-pill--${status.cls}`}>
          <span className="status-dot" />
          {status.text}
        </span>
      </div>
    </header>
  )
}
