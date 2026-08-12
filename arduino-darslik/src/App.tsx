import { useMemo, useState } from 'react'
import { LESSONS, LEVEL_LABEL, type Lesson } from './lessons'
import { loadDone, saveDone } from './progress'
import './styles.css'

type View = 'home' | 'lesson'

export default function App() {
  const [view, setView] = useState<View>('home')
  const [lessonId, setLessonId] = useState(LESSONS[0].id)
  const [done, setDone] = useState<string[]>(() => loadDone())
  const [filter, setFilter] = useState<'all' | Lesson['level']>('all')
  const [copied, setCopied] = useState(false)

  const lesson = useMemo(
    () => LESSONS.find((l) => l.id === lessonId) || LESSONS[0],
    [lessonId],
  )

  const filtered = useMemo(() => {
    if (filter === 'all') return LESSONS
    return LESSONS.filter((l) => l.level === filter)
  }, [filter])

  const progress = Math.round((done.length / LESSONS.length) * 100)

  function openLesson(id: string) {
    setLessonId(id)
    setView('lesson')
    setCopied(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function toggleDone(id: string) {
    setDone((prev) => {
      const next = prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id]
      saveDone(next)
      return next
    })
  }

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(lesson.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  function nextLesson() {
    const i = LESSONS.findIndex((l) => l.id === lesson.id)
    const n = LESSONS[(i + 1) % LESSONS.length]
    openLesson(n.id)
  }

  if (view === 'home') {
    return (
      <div className="page">
        <header className="hero">
          <div className="hero-glow" aria-hidden />
          <p className="eyebrow">Telefon · PC · PWA</p>
          <h1>
            Arduino <span>Darslik</span>
          </h1>
          <p className="lead">
            Oddiy bosqichlar bilan elektronika: LED, tugma, sensor, servo va
            mini-loyiha. Kodni nusxalab Arduino IDE ga joylang.
          </p>
          <div className="progress-wrap">
            <div className="progress-meta">
              <span>Progress</span>
              <strong>
                {done.length}/{LESSONS.length} · {progress}%
              </strong>
            </div>
            <div className="bar">
              <i style={{ width: `${progress}%` }} />
            </div>
          </div>
        </header>

        <div className="filters">
          {(
            [
              ['all', 'Hammasi'],
              ['boshlangich', 'Boshlang‘ich'],
              ['ortacha', 'O‘rta'],
              ['loyiha', 'Loyiha'],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              type="button"
              className={`chip${filter === k ? ' on' : ''}`}
              onClick={() => setFilter(k)}
            >
              {label}
            </button>
          ))}
        </div>

        <section className="grid">
          {filtered.map((l, idx) => {
            const isDone = done.includes(l.id)
            return (
              <button
                key={l.id}
                type="button"
                className={`card${isDone ? ' done' : ''}`}
                onClick={() => openLesson(l.id)}
              >
                <div className="card-top">
                  <span className="num">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="tag">{LEVEL_LABEL[l.level]}</span>
                </div>
                <h2>{l.title}</h2>
                <p>{l.summary}</p>
                <div className="card-foot">
                  <span>{l.minutes} daqiqa</span>
                  <span>{isDone ? '✓ Tugadi' : 'Ochish →'}</span>
                </div>
              </button>
            )
          })}
        </section>

        <footer className="foot">
          Offline ishlaydi · Brauzerga “O‘rnatish” mumkin
        </footer>
      </div>
    )
  }

  const idx = LESSONS.findIndex((l) => l.id === lesson.id)
  const isDone = done.includes(lesson.id)

  return (
    <div className="page lesson-page">
      <button type="button" className="back" onClick={() => setView('home')}>
        ← Darslar
      </button>

      <header className="lesson-head">
        <div className="meta-row">
          <span className="tag">{LEVEL_LABEL[lesson.level]}</span>
          <span className="muted">
            {idx + 1}/{LESSONS.length} · {lesson.minutes} daq
          </span>
        </div>
        <h1>{lesson.title}</h1>
        <p className="lead">{lesson.summary}</p>
      </header>

      <section className="block">
        <h3>Maqsad</h3>
        <ul>
          {lesson.goals.map((g) => (
            <li key={g}>{g}</li>
          ))}
        </ul>
      </section>

      <section className="block two">
        <div>
          <h3>Kerakli qismlar</h3>
          <ul>
            {lesson.parts.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Ulanish</h3>
          <ul>
            {lesson.wiring.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="block">
        <div className="code-head">
          <h3>Kod</h3>
          <button type="button" className="btn ghost" onClick={() => void copyCode()}>
            {copied ? 'Nusxalandi' : 'Nusxa olish'}
          </button>
        </div>
        <pre className="code">
          <code>{lesson.code}</code>
        </pre>
        <p className="tip">💡 {lesson.tip}</p>
      </section>

      <div className="actions">
        <button
          type="button"
          className={`btn${isDone ? ' ghost' : ' primary'}`}
          onClick={() => toggleDone(lesson.id)}
        >
          {isDone ? 'Belgina olib tashlash' : 'Tugallandi deb belgilash'}
        </button>
        <button type="button" className="btn primary" onClick={nextLesson}>
          Keyingi dars →
        </button>
      </div>
    </div>
  )
}
