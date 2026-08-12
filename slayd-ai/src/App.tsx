import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import {
  applyChat,
  generateDeck,
  THEME_CSS,
  type ChatMsg,
  type Deck,
} from './engine'
import './styles.css'

const STARTERS = [
  'Maktabda tabiatni asrash haqida 5 slayd',
  'Startap pitch: yetkazib berish boti',
  'Bolalar uchun ranglar darsi, candy tema',
  'Qorong‘u minimal: shaxsiy brend',
]

export default function App() {
  const [deck, setDeck] = useState<Deck | null>(null)
  const [idx, setIdx] = useState(0)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [msgs, setMsgs] = useState<ChatMsg[]>([
    {
      id: 'm0',
      role: 'assistant',
      text: 'Salom! Men Slayd Studio. Lovable kabi yozing — taqdimot chiqadi. Masalan: «Marketing asoslari haqida 5 slayd».',
    },
  ])
  const listRef = useRef<HTMLDivElement>(null)
  const theme = deck ? THEME_CSS[deck.theme] : THEME_CSS.ocean
  const slide = deck?.slides[idx]

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [msgs, busy])

  const thumbs = useMemo(() => deck?.slides ?? [], [deck])

  async function send(text?: string) {
    const prompt = (text ?? input).trim()
    if (!prompt || busy) return
    setInput('')
    setMsgs((m) => [...m, { id: `u${Date.now()}`, role: 'user', text: prompt }])
    setBusy(true)
    await wait(280)

    const result = deck ? applyChat(deck, prompt) : generateDeck(prompt)
    setDeck(result.deck)
    setIdx(0)
    setMsgs((m) => [
      ...m,
      { id: `a${Date.now()}`, role: 'assistant', text: result.reply },
    ])
    setBusy(false)
  }

  function exportJson() {
    if (!deck) return
    const blob = new Blob([JSON.stringify(deck, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${deck.title.slice(0, 24)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function exportPng() {
    if (!deck || !slide) return
    const canvas = document.createElement('canvas')
    canvas.width = 1920
    canvas.height = 1080
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    // approximate theme fill
    ctx.fillStyle = '#0b3d5c'
    if (deck.theme === 'sunset') ctx.fillStyle = '#c43c2e'
    if (deck.theme === 'forest') ctx.fillStyle = '#1f6a45'
    if (deck.theme === 'mono') ctx.fillStyle = '#111827'
    if (deck.theme === 'candy') ctx.fillStyle = '#ff7eb6'
    ctx.fillRect(0, 0, 1920, 1080)
    ctx.fillStyle = '#fff'
    ctx.font = 'bold 72px Outfit, sans-serif'
    ctx.fillText(slide.title, 120, 220)
    ctx.font = '36px Outfit, sans-serif'
    ctx.fillStyle = 'rgba(255,255,255,0.85)'
    if (slide.subtitle) ctx.fillText(slide.subtitle, 120, 300)
    if (slide.quote) ctx.fillText(`“${slide.quote}”`, 120, 400)
    let y = 380
    for (const b of slide.bullets || []) {
      ctx.fillText(`• ${b}`, 120, y)
      y += 64
    }
    const url = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = url
    a.download = `slayd-${idx + 1}.png`
    a.click()
  }

  return (
    <div className="shell">
      <aside className="chat">
        <div className="chat-head">
          <div className="logo">S</div>
          <div>
            <strong>Slayd Studio</strong>
            <span>Lovable-style · chat → deck</span>
          </div>
        </div>

        <div className="msgs" ref={listRef}>
          {msgs.map((m) => (
            <div key={m.id} className={`bubble ${m.role}`}>
              {m.text}
            </div>
          ))}
          {busy ? <div className="bubble assistant typing">Yaratilmoqda…</div> : null}
        </div>

        {!deck ? (
          <div className="starters">
            {STARTERS.map((s) => (
              <button key={s} type="button" onClick={() => void send(s)}>
                {s}
              </button>
            ))}
          </div>
        ) : null}

        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault()
            void send()
          }}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Nima qilaylik? Masalan: yana slayd qo‘sh…"
            rows={2}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void send()
              }
            }}
          />
          <button type="submit" className="send" disabled={busy || !input.trim()}>
            ↑
          </button>
        </form>
      </aside>

      <main className="preview">
        <header className="preview-bar">
          <div className="tabs">
            <span className="on">Preview</span>
            <span className="mute">{deck ? `${deck.slides.length} slayd` : 'Bo‘sh'}</span>
          </div>
          <div className="bar-actions">
            <button type="button" disabled={!deck} onClick={() => void exportPng()}>
              PNG
            </button>
            <button type="button" disabled={!deck} onClick={exportJson}>
              JSON
            </button>
          </div>
        </header>

        <div className="stage-wrap">
          {slide && deck ? (
            <article
              className="stage"
              style={
                {
                  background: theme.bg,
                  color: theme.text,
                  ['--accent' as string]: theme.accent,
                  ['--muted' as string]: theme.muted,
                  ['--card' as string]: theme.card,
                } as CSSProperties
              }
            >
              <div className="stage-inner">
                {slide.kind === 'title' || slide.kind === 'outro' ? (
                  <>
                    <p className="eyebrow">Slayd Studio</p>
                    <h1>{slide.title}</h1>
                    {slide.subtitle ? <p className="sub">{slide.subtitle}</p> : null}
                  </>
                ) : null}
                {slide.kind === 'bullets' ? (
                  <>
                    <h2>{slide.title}</h2>
                    <ul>
                      {(slide.bullets || []).map((b) => (
                        <li key={b}>{b}</li>
                      ))}
                    </ul>
                  </>
                ) : null}
                {slide.kind === 'quote' ? (
                  <>
                    <h2>{slide.title}</h2>
                    <blockquote>“{slide.quote}”</blockquote>
                  </>
                ) : null}
              </div>
              <div className="stage-foot">
                {idx + 1} / {deck.slides.length} · {deck.theme}
              </div>
            </article>
          ) : (
            <div className="empty-stage">
              <h2>Preview shu yerda</h2>
              <p>Chapdagi chatga yozing — slaydlar shu yerda paydo bo‘ladi.</p>
            </div>
          )}
        </div>

        {thumbs.length ? (
          <div className="thumbs">
            {thumbs.map((s, i) => (
              <button
                key={s.id}
                type="button"
                className={i === idx ? 'on' : ''}
                onClick={() => setIdx(i)}
              >
                <em>{i + 1}</em>
                <span>{s.title}</span>
              </button>
            ))}
          </div>
        ) : null}

        {deck ? (
          <div className="nav-row">
            <button
              type="button"
              disabled={idx <= 0}
              onClick={() => setIdx((v) => Math.max(0, v - 1))}
            >
              ← Oldingi
            </button>
            <button
              type="button"
              disabled={idx >= deck.slides.length - 1}
              onClick={() => setIdx((v) => Math.min(deck.slides.length - 1, v + 1))}
            >
              Keyingi →
            </button>
          </div>
        ) : null}
      </main>
    </div>
  )
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}
