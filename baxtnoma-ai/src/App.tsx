import { useEffect, useRef, useState } from 'react'
import { drawBaxt, H, W } from './draw'
import {
  defaultBaxt,
  KINDS,
  kindById,
  THEMES,
  type BaxtData,
  type KindId,
  type ThemeId,
} from './templates'
import './styles.css'

type Step = 'home' | 'studio'

const STORAGE_KEY = 'baxtnoma-v1'

function loadDraft(): BaxtData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultBaxt()
    return { ...defaultBaxt(), ...JSON.parse(raw) }
  } catch {
    return defaultBaxt()
  }
}

export default function App() {
  const [step, setStep] = useState<Step>('home')
  const [data, setData] = useState<BaxtData>(() => loadDraft())
  const [status, setStatus] = useState('')
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef(0)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }, [data])

  useEffect(() => {
    if (step !== 'studio' || !canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const tick = (now: number) => {
      drawBaxt(ctx, data, now / 1000)
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [data, step])

  function patch<K extends keyof BaxtData>(key: K, value: BaxtData[K]) {
    setData((d) => ({ ...d, [key]: value }))
  }

  function startKind(id: KindId) {
    const kind = kindById(id)
    setData((d) => ({
      ...d,
      kindId: id,
      title: kind.defaultTitle,
      blessing: kind.defaultBlessing,
    }))
    setStep('studio')
  }

  function changeKind(id: KindId) {
    const kind = kindById(id)
    setData((d) => ({
      ...d,
      kindId: id,
      title:
        d.title === kindById(d.kindId).defaultTitle ? kind.defaultTitle : d.title,
      blessing:
        d.blessing === kindById(d.kindId).defaultBlessing
          ? kind.defaultBlessing
          : d.blessing,
    }))
  }

  async function exportPng() {
    const canvas = canvasRef.current
    if (!canvas) return
    setStatus('Rasm tayyorlanmoqda…')
    const ctx = canvas.getContext('2d')
    if (ctx) drawBaxt(ctx, data, 0)
    await wait(40)
    const url = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = url
    a.download = `baxtnoma-${data.kindId}.png`
    a.click()
    setStatus('PNG yuklandi — Telegramga yuboring')
  }

  async function shareNative() {
    const canvas = canvasRef.current
    if (!canvas || !navigator.share) {
      await exportPng()
      return
    }
    const ctx = canvas.getContext('2d')
    if (ctx) drawBaxt(ctx, data, 0)
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/png'),
    )
    if (!blob) {
      await exportPng()
      return
    }
    const file = new File([blob], `baxtnoma-${data.kindId}.png`, {
      type: 'image/png',
    })
    try {
      await navigator.share({
        files: [file],
        title: data.title,
        text: `${data.title} — ${data.recipients}`,
      })
      setStatus('Ulashildi')
    } catch {
      await exportPng()
    }
  }

  if (step === 'home') {
    return (
      <div className="shell home">
        <div className="atmosphere" aria-hidden="true" />
        <header className="hero">
          <p className="brand">Baxtnoma</p>
          <h1>Baxtli kunlarga chiroyli tabrik</h1>
          <p className="lead">
            Turini tanlang — matnni to‘ldiring va tayyor baxtnomani yuklab oling.
          </p>
          <div className="hero-cta">
            <button type="button" className="primary" onClick={() => setStep('studio')}>
              Studiyani ochish
            </button>
          </div>
        </header>
        <section className="kinds" aria-label="Baxtnoma turlari">
          <h2>Tur</h2>
          <div className="kind-grid">
            {KINDS.map((kind) => (
              <button
                key={kind.id}
                type="button"
                className="kind-btn"
                onClick={() => startKind(kind.id)}
              >
                <strong>{kind.label}</strong>
                <span>{kind.hint}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="shell studio">
      <header className="studio-bar">
        <button type="button" className="ghost" onClick={() => setStep('home')}>
          ← Orqaga
        </button>
        <strong className="brand-mini">Baxtnoma</strong>
        <span className="spacer" />
      </header>

      <div className="studio-layout">
        <div className="preview-wrap">
          <canvas
            ref={canvasRef}
            className="preview"
            width={W}
            height={H}
            aria-label="Baxtnoma ko‘rinishi"
          />
        </div>

        <form
          className="form"
          onSubmit={(e) => {
            e.preventDefault()
            void exportPng()
          }}
        >
          <label className="field">
            <span>Tur</span>
            <select
              value={data.kindId}
              onChange={(e) => changeKind(e.target.value as KindId)}
            >
              {KINDS.map((kind) => (
                <option key={kind.id} value={kind.id}>
                  {kind.label}
                </option>
              ))}
            </select>
          </label>

          <fieldset className="themes">
            <legend>Usul</legend>
            <div className="theme-row">
              {THEMES.map((th) => (
                <button
                  key={th.id}
                  type="button"
                  className={`theme-swatch ${data.themeId === th.id ? 'on' : ''}`}
                  style={{ background: `linear-gradient(145deg, ${th.bg0}, ${th.bg1})` }}
                  aria-label={th.label}
                  onClick={() => patch('themeId', th.id as ThemeId)}
                />
              ))}
            </div>
          </fieldset>

          <label className="field">
            <span>Sarlavha</span>
            <input
              value={data.title}
              onChange={(e) => patch('title', e.target.value)}
              maxLength={60}
            />
          </label>

          <label className="field">
            <span>Kimga</span>
            <input
              value={data.recipients}
              onChange={(e) => patch('recipients', e.target.value)}
              placeholder="Masalan: Aziza & Jasur"
              maxLength={80}
            />
          </label>

          <label className="field">
            <span>Duo / tabrik</span>
            <textarea
              value={data.blessing}
              onChange={(e) => patch('blessing', e.target.value)}
              rows={2}
              maxLength={140}
            />
          </label>

          <div className="row2">
            <label className="field">
              <span>Sana</span>
              <input
                value={data.date}
                onChange={(e) => patch('date', e.target.value)}
                maxLength={40}
              />
            </label>
            <label className="field">
              <span>Joy</span>
              <input
                value={data.place}
                onChange={(e) => patch('place', e.target.value)}
                maxLength={60}
              />
            </label>
          </div>

          <label className="field">
            <span>Tabrik etuvchi</span>
            <input
              value={data.from}
              onChange={(e) => patch('from', e.target.value)}
              placeholder="Masalan: Alievlar oilasi"
              maxLength={80}
            />
          </label>

          <label className="field">
            <span>Imzo satri</span>
            <input
              value={data.seal}
              onChange={(e) => patch('seal', e.target.value)}
              placeholder="Hurmat bilan"
              maxLength={40}
            />
          </label>

          <div className="actions">
            <button type="button" className="primary" onClick={() => void shareNative()}>
              Ulashish / yuklash
            </button>
            <button type="submit" className="secondary">
              PNG yuklab olish
            </button>
          </div>
          {status ? <p className="status">{status}</p> : null}
        </form>
      </div>
    </div>
  )
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}
