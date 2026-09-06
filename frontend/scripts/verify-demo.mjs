/**
 * Demo verification harness.
 *
 * Drives the real cockpit in a real browser against the real backend:
 *   load -> Load SIH Demo Case -> Analyze Charter -> assert every section rendered.
 *
 * Run with the backend on :8000 and `npm run dev` on :5173:
 *   node scripts/verify-demo.mjs
 */
import puppeteer from 'puppeteer-core'
import { existsSync, mkdirSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

// Chrome first: puppeteer-core tracks Chrome's CDP surface most closely, and
// an Edge major-version bump has broken headless launch here before.
const CANDIDATES = [
  process.env.BROWSER_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
].filter(Boolean)
const executablePath = CANDIDATES.find((p) => existsSync(p))
if (!executablePath) {
  console.error('No Chrome/Edge binary found. Set BROWSER_PATH to override.')
  process.exit(1)
}

const URL = process.env.COCKPIT_URL || 'http://localhost:5173'
const OUT = 'screenshots'
mkdirSync(OUT, { recursive: true })

const consoleErrors = []
const pageErrors = []
const failedRequests = []
const abortedRequests = []
// Requests still in flight when we close the browser abort by definition —
// that is harness teardown, not a product defect.
let tearingDown = false

// Use a throwaway profile: launching against the user's real Edge profile
// fails if that profile is already open or locked.
const profileDir = mkdtempSync(join(tmpdir(), 'varuneeti-verify-'))

const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  args: [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    `--user-data-dir=${profileDir}`,
  ],
})

let exitCode = 0
try {
  const page = await browser.newPage()
  await page.setViewport({ width: 1920, height: 1080 })

  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text())
  })
  page.on('pageerror', (e) => pageErrors.push(e.message))
  page.on('requestfailed', (r) => {
    if (tearingDown) return
    const err = r.failure()?.errorText ?? 'unknown'
    // ERR_ABORTED is our own AbortController cancelling a health poll (React
    // StrictMode double-invokes effects in dev). Informational, not a defect.
    if (err.includes('ERR_ABORTED')) {
      abortedRequests.push(`${r.url()} :: ${err}`)
      return
    }
    failedRequests.push(`${r.url()} :: ${err}`)
  })
  page.on('response', (r) => {
    if (r.status() >= 400) failedRequests.push(`HTTP ${r.status()} :: ${r.url()}`)
  })

  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 30000 })

  // Health probe should flip the status pill to online.
  await page.waitForFunction(
    () => document.querySelector('.status-pill')?.textContent?.includes('System Online'),
    { timeout: 15000 },
  )
  console.log('✓ backend health detected — SYSTEM ONLINE')

  const clickByText = async (selector, text) => {
    const handle = await page.evaluateHandle(
      (sel, t) => [...document.querySelectorAll(sel)].find((el) => el.textContent.includes(t)),
      selector,
      text,
    )
    const el = handle.asElement()
    if (!el) throw new Error(`Could not find ${selector} containing "${text}"`)
    await el.click()
  }

  await clickByText('button', 'Load SIH Demo Case')
  const formValues = await page.$$eval('.field__control', (els) => els.map((e) => e.value))
  console.log('✓ demo case loaded:', formValues.join(' | '))

  await page.screenshot({ path: `${OUT}/01-cockpit-1920.png` })

  await clickByText('button', 'Analyze Charter')
  console.log('  running decision loop…')

  await page.waitForSelector('.reco__strategy-name', { timeout: 60000 })

  const checks = {
    'Recommendation card': '.reco',
    'Decision pipeline': '.pipeline .pipe',
    'Forecast chart': '#forecast .chart-svg',
    'Feasibility matrix': '#feasibility .table tbody tr',
    'Risk gauge': '#risk .gauge__svg',
    'Risk dimension bars': '#risk .riskrow',
    'Strategy cards': '#strategy .strat',
    'Strategy bar chart': '#strategy .costbar',
    'Voyage plan': '#voyage .voyage',
    'Decision drivers': '#rationale .reason',
    'Cost breakdown': '#cost .costrow',
    'Architecture rail': '#architecture .arch',
    'Scenario stress test': '#scenarios .table tbody tr',
    'Robustness banner': '.robust-banner',
    'Data transparency': '.transparency',
  }

  const results = {}
  for (const [name, sel] of Object.entries(checks)) {
    results[name] = await page.$$eval(sel, (els) => els.length).catch(() => 0)
  }

  // Count-up animations must finish before the DOM is read, otherwise we
  // capture interpolated values rather than the engine's actual figures.
  await new Promise((r) => setTimeout(r, 2500))

  const snapshot = await page.evaluate(() => ({
    strategy: document.querySelector('.reco__strategy-name')?.textContent?.trim(),
    metrics: [...document.querySelectorAll('.reco__metrics .metric')].map((m) => ({
      label: m.querySelector('.metric__label')?.textContent?.trim(),
      value: m.querySelector('.metric__value')?.textContent?.trim(),
    })),
    pipeline: [...document.querySelectorAll('.pipe')].map((p) => ({
      engine: p.querySelector('.pipe__engine')?.textContent?.trim(),
      headline: p.querySelector('.pipe__headline')?.textContent?.trim(),
    })),
    vessels: [...document.querySelectorAll('#feasibility tbody tr')].map((r) => {
      const cells = [...r.querySelectorAll('td')].map((c) => c.textContent.trim())
      return `${cells[0]} → ${cells[cells.length - 1]}`
    }),
    strategies: [...document.querySelectorAll('.strat')].map(
      (s) =>
        `${s.querySelector('.strat__name')?.textContent} ${s.querySelector('.strat__cpt')?.textContent}` +
        (s.querySelector('.strat__flag') ? '  ← RECOMMENDED' : ''),
    ),
    snapshotBanner: Boolean(document.querySelector('.snapshot-banner')),
  }))

  // ── Cross-check the rendered figures against the engine itself ──────────
  const apiPayload = {
    origin: 'Australia',
    destination: 'Paradip',
    cargo_quantity: 300000,
    parcel_quantity: 75000,
    delivery_start: '2026-10-01',
    delivery_end: '2026-12-31',
  }
  const apiRes = await fetch('http://localhost:8000/api/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(apiPayload),
  })
  const api = await apiRes.json()

  const expectations = [
    ['Strategy', snapshot.strategy, api.recommendation.strategy.replace('_', '-')],
    [
      'Voyages',
      snapshot.metrics.find((m) => m.label === 'Voyages')?.value,
      String(api.voyages),
    ],
    [
      'Cost / tonne',
      snapshot.metrics.find((m) => m.label === 'Expected Cost / Tonne')?.value,
      `$${api.recommendation.cost_per_tonne.toFixed(2)}`,
    ],
    [
      'Vessel',
      snapshot.metrics.find((m) => m.label === 'Recommended Vessel')?.value,
      api.recommendation.vessel_class.toUpperCase(),
    ],
  ]

  console.log('\n── UI vs API PARITY ──────────────────────────────')
  for (const [name, ui, expected] of expectations) {
    const ok = ui === expected
    console.log(`${ok ? '✓' : '✗'} ${name}: UI "${ui}" vs API "${expected}"`)
    if (!ok) exitCode = 1
  }

  await page.screenshot({ path: `${OUT}/02-decision-1920.png` })
  await page.evaluate(() => document.getElementById('forecast')?.scrollIntoView())
  await new Promise((r) => setTimeout(r, 700))
  await page.screenshot({ path: `${OUT}/03-forecast-risk-1920.png` })
  await page.evaluate(() => document.getElementById('strategy')?.scrollIntoView())
  await new Promise((r) => setTimeout(r, 700))
  await page.screenshot({ path: `${OUT}/04-strategy-1920.png` })

  await page.setViewport({ width: 1366, height: 768 })
  await new Promise((r) => setTimeout(r, 600))
  await page.evaluate(() => window.scrollTo(0, 0))
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: `${OUT}/05-cockpit-1366.png` })
  await page.evaluate(() => document.getElementById('decision')?.scrollIntoView())
  await new Promise((r) => setTimeout(r, 500))
  await page.screenshot({ path: `${OUT}/06-decision-1366.png` })

  const overflow = await page.evaluate(() => ({
    scrollW: document.documentElement.scrollWidth,
    clientW: document.documentElement.clientWidth,
  }))

  console.log('\n── RENDERED SECTIONS ─────────────────────────────')
  for (const [name, count] of Object.entries(results)) {
    console.log(`${count > 0 ? '✓' : '✗'} ${name}: ${count} node(s)`)
    if (count === 0) exitCode = 1
  }

  console.log('\n── DECISION OUTPUT ───────────────────────────────')
  console.log('Strategy:', snapshot.strategy)
  snapshot.metrics.forEach((m) => console.log(`  ${m.label}: ${m.value}`))
  console.log('Pipeline:')
  snapshot.pipeline.forEach((p) => console.log(`  ${p.engine} → ${p.headline}`))
  console.log('Vessels:')
  snapshot.vessels.forEach((v) => console.log(`  ${v}`))
  console.log('Strategies:')
  snapshot.strategies.forEach((s) => console.log(`  ${s}`))
  console.log('Snapshot banner shown (should be false for a live run):', snapshot.snapshotBanner)
  if (snapshot.snapshotBanner) exitCode = 1

  console.log('\n── LAYOUT @1366×768 ──────────────────────────────')
  console.log(`scrollWidth ${overflow.scrollW} vs clientWidth ${overflow.clientW}`)
  if (overflow.scrollW > overflow.clientW + 1) {
    console.log('✗ horizontal overflow detected')
    exitCode = 1
  } else {
    console.log('✓ no horizontal overflow')
  }

  console.log('\n── CONSOLE ───────────────────────────────────────')
  console.log('console errors:', consoleErrors.length)
  consoleErrors.forEach((e) => console.log('  ✗', e))
  console.log('uncaught page errors:', pageErrors.length)
  pageErrors.forEach((e) => console.log('  ✗', e))
  console.log('failed requests:', failedRequests.length)
  failedRequests.forEach((e) => console.log('  ✗', e))
  console.log(`deliberate client aborts (informational): ${abortedRequests.length}`)
  abortedRequests.forEach((e) => console.log('  ·', e))
  if (consoleErrors.length || pageErrors.length || failedRequests.length) exitCode = 1
} catch (err) {
  console.error('\n✗ VERIFICATION FAILED:', err.message)
  exitCode = 1
} finally {
  tearingDown = true
  await browser.close()
}

console.log(exitCode === 0 ? '\n✅ DEMO VERIFIED' : '\n❌ ISSUES FOUND')
process.exit(exitCode)
