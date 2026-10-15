import { useEffect, useRef, useState } from 'react'
import { drawInvite, H, W } from './draw'
import {
  defaultInvite,
  EVENTS,
  eventById,
  THEMES,
  type EventId,
  type InviteData,
  type ThemeId,
} from './templates'
import './styles.css'

type Step = 'home' | 'studio'

const STORAGE_KEY = 'taklifnoma-v1'

function loadDraft(): InviteData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultInvite()
    return { ...defaultInvite(), ...JSON.parse(raw) }
  } catch {
    return defaultInvite()
  }
}

export default function App() {
  const [step, setStep] = useState<Step>('home')
  const [data, setData] = useState<InviteData>(() => loadDraft())
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
      drawInvite(ctx, data, now / 1000)
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [data, step])

  function patch<K extends keyof InviteData>(key: K, value: InviteData[K]) {
    setData((d) => ({ ...d, [key]: value }))
  }

  function startEvent(id: EventId) {
    const ev = eventById(id)
    setData((d) => ({
      ...d,
      eventId: id,
      title: ev.defaultTitle,
      note: ev.defaultNote,
    }))
    setStep('studio')
  }

  function changeEvent(id: EventId) {
    const ev = eventById(id)
    setData((d) => ({
      ...d,
      eventId: id,
      title: d.title === eventById(d.eventId).defaultTitle ? ev.defaultTitle : d.title,
      note: d.note === eventById(d.eventId).defaultNote ? ev.defaultNote : d.note,
    }))
  }

  async function exportPng() {
    const canvas = canvasRef.current
    if (!canvas) return
    setStatus('Rasm tayyorlanmoqda…')
    // redraw once without animation wobble
    const ctx = canvas.getContext('2d')
    if (ctx) drawInvite(ctx, data, 0)
    await wait(40)
    const url = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = url
    a.download = `taklifnoma-${data.eventId}.png`
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
    if (ctx) drawInvite(ctx, data, 0)
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/png'),
    )
    if (!blob) {
      await exportPng()
      return
    }
    const file = new File([blob], `taklifnoma-${data.eventId}.png`, {
      type: 'image/png',
    })
    try {
      await navigator.share({
        files: [file],
        title: data.title,
        text: `${data.title} — ${data.date} ${data.time}`,
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
          <p className="brand">Taklifnoma</p>
          <h1>Har bir mehmonga chiroyli taklif</h1>
          <p className="lead">
            Tadbirni tanlang — matnni to‘ldiring va tayyor rasmni yuklab oling.
          </p>
          <div className="hero-cta">
            <button type="button" className="primary" onClick={() => setStep('studio')}>
              Studiyani ochish
            </button>
          </div>
        </header>
        <section className="events" aria-label="Tadbir turlari">
          <h2>Tadbir turi</h2>
          <div className="event-grid">
            {EVENTS.map((ev) => (
              <button
                key={ev.id}
                type="button"
                className="event-btn"
                onClick={() => startEvent(ev.id)}
              >
                <strong>{ev.label}</strong>
                <span>{ev.hint}</span>
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
        <strong className="brand-mini">Taklifnoma</strong>
        <span className="spacer" />
      </header>

      <div className="studio-layout">
        <div className="preview-wrap">
          <canvas
            ref={canvasRef}
            className="preview"
            width={W}
            height={H}
            aria-label="Taklifnoma ko‘rinishi"
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
            <span>Tadbir</span>
            <select
              value={data.eventId}
              onChange={(e) => changeEvent(e.target.value as EventId)}
            >
              {EVENTS.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.label}
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
            <span>Taklif etuvchilar</span>
            <input
              value={data.hosts}
              onChange={(e) => patch('hosts', e.target.value)}
              placeholder="Masalan: Alievlar oilasi"
              maxLength={80}
            />
          </label>

          <label className="field">
            <span>Mehmon (ixtiyoriy)</span>
            <input
              value={data.guest}
              onChange={(e) => patch('guest', e.target.value)}
              placeholder="Hurmatli …"
              maxLength={60}
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
              <span>Vaqt</span>
              <input
                value={data.time}
                onChange={(e) => patch('time', e.target.value)}
                maxLength={20}
              />
            </label>
          </div>

          <label className="field">
            <span>Manzil</span>
            <input
              value={data.place}
              onChange={(e) => patch('place', e.target.value)}
              maxLength={100}
            />
          </label>

          <label className="field">
            <span>Izoh</span>
            <textarea
              value={data.note}
              onChange={(e) => patch('note', e.target.value)}
              rows={2}
              maxLength={120}
            />
          </label>

          <label className="field">
            <span>Telefon</span>
            <input
              value={data.phone}
              onChange={(e) => patch('phone', e.target.value)}
              placeholder="+998 …"
              maxLength={30}
              inputMode="tel"
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
