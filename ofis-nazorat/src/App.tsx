import { useEffect, useRef, useState } from 'react'
import {
  captureThumb,
  detectAll,
  detectDescriptor,
  isFaceReady,
  loadFaceModels,
  matchPerson,
} from './face'
import {
  exportLogsCsv,
  loadLogs,
  loadPeople,
  saveLogs,
  savePeople,
  todayKey,
  uid,
} from './storage'
import type { LogEvent, Person } from './types'
import './styles.css'

const LEAVE_FRAME_MS = 2500

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString('uz-UZ', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      day: '2-digit',
      month: '2-digit',
    })
  } catch {
    return iso
  }
}

export default function App() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const peopleRef = useRef<Person[]>([])
  const inFrameRef = useRef<Record<string, boolean>>({})
  const lastSeenRef = useRef<Record<string, number>>({})
  const loopRef = useRef(0)

  const [people, setPeople] = useState<Person[]>(() => loadPeople())
  const [logs, setLogs] = useState<LogEvent[]>(() => loadLogs())
  const [name, setName] = useState('')
  const [status, setStatus] = useState('Kamerani yoqing…')
  const [camOn, setCamOn] = useState(false)
  const [modelsOk, setModelsOk] = useState(false)
  const [busy, setBusy] = useState(false)
  const [liveLabel, setLiveLabel] = useState('Kutilyapti')
  const [error, setError] = useState('')

  useEffect(() => {
    peopleRef.current = people
    savePeople(people)
  }, [people])

  useEffect(() => {
    saveLogs(logs)
  }, [logs])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        setStatus('Yuz modellari yuklanmoqda…')
        await loadFaceModels('/models')
        if (!cancelled) {
          setModelsOk(true)
          setStatus('Modellari tayyor. Kamerani yoqing.')
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Model yuklanmadi')
          setStatus('Model xato')
        }
      }
    })()
    return () => {
      cancelled = true
      stopCamera()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function recordEvent(person: Person, type: 'kirish' | 'chiqish', thumb?: string) {
    const updated: Person = {
      ...person,
      status: type === 'kirish' ? 'inside' : 'outside',
    }
    peopleRef.current = peopleRef.current.map((p) =>
      p.id === person.id ? updated : p,
    )
    setPeople([...peopleRef.current])
    const event: LogEvent = {
      id: uid(),
      personId: person.id,
      name: person.name,
      type,
      at: new Date().toISOString(),
      thumb,
    }
    setLogs((prev) => [event, ...prev])
    setLiveLabel(
      type === 'kirish'
        ? `✅ ${person.name} kirdi`
        : `🚪 ${person.name} chiqdi`,
    )
  }

  async function startCamera() {
    setError('')
    if (!isFaceReady() && !modelsOk) {
      setError('Avval modellar yuklansin')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      })
      streamRef.current = stream
      const video = videoRef.current
      if (video) {
        video.srcObject = stream
        await video.play()
      }
      setCamOn(true)
      setStatus('Kamera doimiy ishlayapti')
      startLoop()
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : 'Kameraga ruxsat berilmadi (HTTPS yoki localhost kerak)',
      )
      setStatus('Kamera ochilmadi')
    }
  }

  function stopCamera() {
    cancelAnimationFrame(loopRef.current)
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setCamOn(false)
    setStatus('Kamera o‘chirildi')
  }

  function startLoop() {
    cancelAnimationFrame(loopRef.current)
    let lastRun = 0
    let scanning = false

    const tick = async (ts: number) => {
      loopRef.current = requestAnimationFrame(tick)
      if (scanning || ts - lastRun < 500) return
      lastRun = ts
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState < 2) return

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      scanning = true
      try {
        const detections = await detectAll(video)
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.lineWidth = 3
        ctx.font = '20px "Segoe UI", sans-serif'

        const now = Date.now()
        const seenNow = new Set<string>()

        for (const det of detections) {
          const box = det.detection.box
          const match = matchPerson(det.descriptor, peopleRef.current)
          const label = match
            ? `${match.name} (${match.distance.toFixed(2)})`
            : 'Noma’lum'
          ctx.strokeStyle = match ? '#22c55e' : '#f59e0b'
          ctx.fillStyle = match ? '#22c55e' : '#f59e0b'
          ctx.strokeRect(box.x, box.y, box.width, box.height)
          ctx.fillText(label, box.x, Math.max(24, box.y - 8))

          if (!match) continue
          seenNow.add(match.id)
          lastSeenRef.current[match.id] = now

          // Kameraga yangi kirganda bitta hodisa
          if (!inFrameRef.current[match.id]) {
            inFrameRef.current[match.id] = true
            const person = peopleRef.current.find((p) => p.id === match.id)
            if (person) {
              const type = person.status === 'inside' ? 'chiqish' : 'kirish'
              recordEvent(person, type, captureThumb(video))
            }
          }
        }

        for (const id of Object.keys(inFrameRef.current)) {
          if (seenNow.has(id)) continue
          const last = lastSeenRef.current[id] || 0
          if (now - last > LEAVE_FRAME_MS) {
            inFrameRef.current[id] = false
          }
        }

        if (!detections.length) {
          setLiveLabel((s) =>
            s.startsWith('✅') || s.startsWith('🚪') ? s : 'Yuz yo‘q',
          )
        }
      } catch {
        // loop continue
      } finally {
        scanning = false
      }
    }

    loopRef.current = requestAnimationFrame(tick)
  }

  async function registerPerson() {
    const video = videoRef.current
    const trimmed = name.trim()
    if (!video || !camOn) {
      setError('Avval kamerani yoqing')
      return
    }
    if (!trimmed) {
      setError('Ism yozing')
      return
    }
    setBusy(true)
    setError('')
    try {
      const descriptor = await detectDescriptor(video)
      if (!descriptor) {
        setError('Yuz topilmadi — yuzni kameraga tuting')
        return
      }
      const person: Person = {
        id: uid(),
        name: trimmed,
        descriptor: Array.from(descriptor),
        thumb: captureThumb(video),
        status: 'outside',
        createdAt: new Date().toISOString(),
      }
      peopleRef.current = [...peopleRef.current, person]
      setPeople([...peopleRef.current])
      setName('')
      setLiveLabel(`➕ ${person.name} ro‘yxatga olindi`)
    } finally {
      setBusy(false)
    }
  }

  function removePerson(id: string) {
    peopleRef.current = peopleRef.current.filter((p) => p.id !== id)
    setPeople([...peopleRef.current])
  }

  function manual(id: string, type: 'kirish' | 'chiqish') {
    const person = peopleRef.current.find((p) => p.id === id)
    if (!person) return
    recordEvent(person, type)
  }

  function clearTodayLogs() {
    const today = todayKey()
    setLogs((prev) => prev.filter((l) => todayKey(l.at) !== today))
  }

  function downloadCsv() {
    const blob = new Blob([exportLogsCsv(logs)], {
      type: 'text/csv;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ofis-log-${todayKey()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const inside = people.filter((p) => p.status === 'inside')
  const todayLogs = logs.filter((l) => todayKey(l.at) === todayKey())

  return (
    <div className="page">
      <header className="top">
        <div>
          <p className="eyebrow">PC kamera · lokal</p>
          <h1>Ofis nazorat</h1>
          <p className="sub">Kim kirdi / kim chiqdi — botga aloqasi yo‘q</p>
        </div>
        <div className="top-actions">
          {!camOn ? (
            <button
              type="button"
              className="btn primary"
              onClick={() => void startCamera()}
            >
              Kamerani yoqish
            </button>
          ) : (
            <button type="button" className="btn danger" onClick={stopCamera}>
              Kamerani o‘chirish
            </button>
          )}
        </div>
      </header>

      <div className="grid">
        <section className="panel cam-panel">
          <div className="cam-wrap">
            <video ref={videoRef} playsInline muted autoPlay />
            <canvas ref={canvasRef} />
            <div className={`pill ${camOn ? 'on' : ''}`}>
              {camOn ? 'LIVE' : 'OFF'}
            </div>
          </div>
          <div className="cam-meta">
            <strong>{liveLabel}</strong>
            <span>{status}</span>
            {error ? <span className="err">{error}</span> : null}
          </div>

          <div className="register">
            <h2>Yangi odam</h2>
            <div className="row">
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ism familiya"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void registerPerson()
                }}
              />
              <button
                type="button"
                className="btn primary"
                disabled={busy || !camOn}
                onClick={() => void registerPerson()}
              >
                Yuzni saqlash
              </button>
            </div>
            <p className="hint">
              Kameraga qarang → «Yuzni saqlash». Eshik oldidan o‘tganda avtomatik
              kirish/chiqish yoziladi. Qayta yozish uchun avval kadrdan chiqish kerak.
            </p>
          </div>
        </section>

        <aside className="side">
          <section className="panel">
            <div className="panel-head">
              <h2>Ichkarida · {inside.length}</h2>
            </div>
            {inside.length === 0 ? (
              <p className="empty">Hozir hech kim yo‘q</p>
            ) : (
              <ul className="people">
                {inside.map((p) => (
                  <li key={p.id}>
                    {p.thumb ? (
                      <img src={p.thumb} alt="" />
                    ) : (
                      <span className="avatar" />
                    )}
                    <div>
                      <strong>{p.name}</strong>
                      <span>ichkarida</span>
                    </div>
                    <button
                      type="button"
                      className="btn ghost"
                      onClick={() => manual(p.id, 'chiqish')}
                    >
                      Chiqish
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Ro‘yxat · {people.length}</h2>
            </div>
            {people.length === 0 ? (
              <p className="empty">Avval odamlarni qo‘shing</p>
            ) : (
              <ul className="people">
                {people.map((p) => (
                  <li key={p.id}>
                    {p.thumb ? (
                      <img src={p.thumb} alt="" />
                    ) : (
                      <span className="avatar" />
                    )}
                    <div>
                      <strong>{p.name}</strong>
                      <span>
                        {p.status === 'inside' ? 'ichkarida' : 'tashqarida'}
                      </span>
                    </div>
                    <div className="mini-actions">
                      <button
                        type="button"
                        className="btn ghost"
                        onClick={() => manual(p.id, 'kirish')}
                      >
                        Kirish
                      </button>
                      <button
                        type="button"
                        className="btn ghost"
                        onClick={() => removePerson(p.id)}
                      >
                        O‘chirish
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Bugungi jurnal · {todayLogs.length}</h2>
              <div className="mini-actions">
                <button type="button" className="btn ghost" onClick={downloadCsv}>
                  CSV
                </button>
                <button
                  type="button"
                  className="btn ghost"
                  onClick={clearTodayLogs}
                >
                  Tozalash
                </button>
              </div>
            </div>
            {todayLogs.length === 0 ? (
              <p className="empty">Hali yozuv yo‘q</p>
            ) : (
              <ul className="logs">
                {todayLogs.slice(0, 80).map((l) => (
                  <li key={l.id} className={l.type}>
                    {l.thumb ? <img src={l.thumb} alt="" /> : null}
                    <div>
                      <strong>{l.name}</strong>
                      <span>{formatTime(l.at)}</span>
                    </div>
                    <em>{l.type === 'kirish' ? 'KIRISH' : 'CHIQISH'}</em>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>
    </div>
  )
}
