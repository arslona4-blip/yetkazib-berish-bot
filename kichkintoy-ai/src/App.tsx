import { useEffect, useRef, useState } from 'react'
import { drawScene, H, W } from './draw'
import { buildStory, THEMES, type Scene, type ThemeId } from './stories'
import { speak, stopSpeak } from './tts'
import './styles.css'

type Step = 'home' | 'studio' | 'player'

export default function App() {
  const [step, setStep] = useState<Step>('home')
  const [name, setName] = useState('Oybola')
  const [theme, setTheme] = useState<ThemeId>('yulduz')
  const [scenes, setScenes] = useState<Scene[]>([])
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [status, setStatus] = useState('')
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef(0)
  const t0Ref = useRef(0)

  function create() {
    const s = buildStory(name, theme)
    setScenes(s)
    setIdx(0)
    setStep('studio')
    setStatus('')
  }

  useEffect(() => {
    if (!scenes.length || !canvasRef.current) return
    const ctx = canvasRef.current.getContext('2d')
    if (!ctx) return
    const tick = (now: number) => {
      if (!t0Ref.current) t0Ref.current = now
      const t = (now - t0Ref.current) / 1000
      drawScene(ctx, scenes[idx], t, name.trim() || 'Oybola')
      rafRef.current = requestAnimationFrame(tick)
    }
    t0Ref.current = 0
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [scenes, idx, name, step])

  async function playAll() {
    if (!scenes.length) return
    setPlaying(true)
    setStep('player')
    setStatus('Ijro…')
    for (let i = 0; i < scenes.length; i++) {
      setIdx(i)
      await speak(scenes[i].narrate)
      await wait(600)
    }
    setPlaying(false)
    setStatus('Tayyor')
  }

  async function exportVideo() {
    const canvas = canvasRef.current
    if (!canvas || !scenes.length) return
    setExporting(true)
    setStatus('Video yozilmoqda…')
    stopSpeak()

    const stream = canvas.captureStream(30)
    const mime = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
      ? 'video/webm;codecs=vp9'
      : 'video/webm'
    const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 4_000_000 })
    const chunks: BlobPart[] = []
    rec.ondataavailable = (e) => {
      if (e.data.size) chunks.push(e.data)
    }

    const done = new Promise<Blob>((resolve) => {
      rec.onstop = () => resolve(new Blob(chunks, { type: 'video/webm' }))
    })

    rec.start(200)

    for (let i = 0; i < scenes.length; i++) {
      setIdx(i)
      setStatus(`Sahna ${i + 1}/${scenes.length}`)
      // speak while recording (may not mix into video on all browsers)
      void speak(scenes[i].narrate)
      await wait(5200)
    }

    rec.stop()
    stopSpeak()
    const blob = await done
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `kichkintoy-${theme}.webm`
    a.click()
    URL.revokeObjectURL(url)
    setExporting(false)
    setStatus('Video yuklandi (.webm)')
  }

  return (
    <div className="app">
      {step === 'home' ? (
        <section className="hero">
          <div className="badge">Kichkintoy AI</div>
          <h1>Ertakdan video</h1>
          <p>
            Ism va mavzu tanlang — slideshow + ovoz + video fayl. Kling emas:
            yengil, bepul, brauzerda.
          </p>

          <label className="field">
            <span>Bolaning ismi</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Oybola"
              maxLength={24}
            />
          </label>

          <div className="themes">
            {THEMES.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`theme${theme === t.id ? ' on' : ''}`}
                onClick={() => setTheme(t.id)}
              >
                <span className="te">{t.emoji}</span>
                <strong>{t.title}</strong>
                <em>{t.desc}</em>
              </button>
            ))}
          </div>

          <button type="button" className="btn primary" onClick={create}>
            Ertak yaratish
          </button>
        </section>
      ) : null}

      {(step === 'studio' || step === 'player') && scenes.length ? (
        <section className="studio">
          <header className="top">
            <button type="button" className="ghost" onClick={() => setStep('home')}>
              ← Orqaga
            </button>
            <div>
              <strong>{name || 'Oybola'}</strong>
              <span>
                {idx + 1}/{scenes.length} · {scenes[idx]?.title}
              </span>
            </div>
          </header>

          <div className="stage">
            <canvas ref={canvasRef} width={W} height={H} />
          </div>

          <div className="scene-list">
            {scenes.map((s, i) => (
              <button
                key={s.id}
                type="button"
                className={`chip${i === idx ? ' on' : ''}`}
                onClick={() => setIdx(i)}
              >
                {s.emoji} {s.title}
              </button>
            ))}
          </div>

          <p className="narrate">{scenes[idx]?.narrate}</p>

          <div className="actions">
            <button
              type="button"
              className="btn"
              disabled={playing || exporting}
              onClick={() => void speak(scenes[idx].narrate)}
            >
              Ovoz
            </button>
            <button
              type="button"
              className="btn primary"
              disabled={playing || exporting}
              onClick={() => void playAll()}
            >
              Hammasi
            </button>
            <button
              type="button"
              className="btn accent"
              disabled={playing || exporting}
              onClick={() => void exportVideo()}
            >
              Video (.webm)
            </button>
          </div>
          {status ? <p className="status">{status}</p> : null}
          <p className="hint">
            Video — animatsiyali slideshow. Ovoz ba’zi telefonlarda videoga
            tushmasligi mumkin; CapCut da alohida qo‘shing.
          </p>
        </section>
      ) : null}
    </div>
  )
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}
