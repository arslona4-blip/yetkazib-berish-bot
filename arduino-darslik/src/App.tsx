import { useMemo, useState } from 'react'
import { LESSONS, LEVEL_LABEL, type Lesson } from './lessons'
import { loadDone, saveDone } from './progress'
import { Simulator } from './Simulator'
import './styles.css'

type View = 'home' | 'lesson'
type Tab = 'steps' | 'sim' | 'code' | 'practice'

export default function App() {
  const [view, setView] = useState<View>('home')
  const [lessonId, setLessonId] = useState(LESSONS[0].id)
  const [done, setDone] = useState<string[]>(() => loadDone())
  const [filter, setFilter] = useState<'all' | Lesson['level']>('all')
  const [tab, setTab] = useState<Tab>('steps')
  const [stepIdx, setStepIdx] = useState(0)
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
    setTab('steps')
    setStepIdx(0)
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
    openLesson(LESSONS[(i + 1) % LESSONS.length].id)
  }

  if (view === 'home') {
    return (
      <div className="page">
        <header className="hero">
          <div className="hero-glow" aria-hidden />
          <p className="eyebrow">Telefon · PC · Simulyator</p>
          <h1>
            Arduino <span>Darslik</span>
          </h1>
          <p className="lead">
            Bosqichma-bosqich o‘rganing: IDE o‘rnatish, simulyator, tayyor kod va
            amaliy mashq. Har darsda ko‘rib, kod yozib, sinab chiqing.
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
          {filtered.map((l) => {
            const isDone = done.includes(l.id)
            const globalIdx = LESSONS.findIndex((x) => x.id === l.id)
            return (
              <button
                key={l.id}
                type="button"
                className={`card${isDone ? ' done' : ''}`}
                onClick={() => openLesson(l.id)}
              >
                <div className="card-top">
                  <span className="num">
                    {String(globalIdx + 1).padStart(2, '0')}
                  </span>
                  <span className="tag">{LEVEL_LABEL[l.level]}</span>
                </div>
                <h2>{l.title}</h2>
                <p>{l.summary}</p>
                <div className="card-foot">
                  <span>{l.minutes} daq · simulyator</span>
                  <span>{isDone ? '✓ Tugadi' : 'Boshlash →'}</span>
                </div>
              </button>
            )
          })}
        </section>

        <footer className="foot">
          1-darsdan boshlang: Arduino IDE ni xatosiz o‘rnatish
        </footer>
      </div>
    )
  }

  const idx = LESSONS.findIndex((l) => l.id === lesson.id)
  const isDone = done.includes(lesson.id)
  const step = lesson.steps[stepIdx]

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

      <div className="tabs">
        {(
          [
            ['steps', 'Bosqichlar'],
            ['sim', 'Simulyator'],
            ['code', 'Tayyor kod'],
            ['practice', 'Amaliyot'],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            className={`chip${tab === k ? ' on' : ''}`}
            onClick={() => setTab(k)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'steps' ? (
        <>
          <section className="block">
            <h3>
              Bosqich {stepIdx + 1}/{lesson.steps.length}
            </h3>
            <h2 className="step-title">{step.title}</h2>
            <p className="step-detail">{step.detail}</p>
            <div className="actions">
              <button
                type="button"
                className="btn ghost"
                disabled={stepIdx === 0}
                onClick={() => setStepIdx((s) => Math.max(0, s - 1))}
              >
                ← Orqaga
              </button>
              <button
                type="button"
                className="btn primary"
                onClick={() => {
                  if (stepIdx < lesson.steps.length - 1) {
                    setStepIdx((s) => s + 1)
                  } else {
                    setTab('sim')
                  }
                }}
              >
                {stepIdx < lesson.steps.length - 1
                  ? 'Keyingi bosqich →'
                  : 'Simulyatorga →'}
              </button>
            </div>
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
            <h3>Maqsad</h3>
            <ul>
              {lesson.goals.map((g) => (
                <li key={g}>{g}</li>
              ))}
            </ul>
          </section>
        </>
      ) : null}

      {tab === 'sim' ? (
        <section className="block">
          <Simulator kind={lesson.sim} />
          <div className="actions">
            <button
              type="button"
              className="btn ghost"
              onClick={() => setTab('steps')}
            >
              ← Bosqichlar
            </button>
            <button
              type="button"
              className="btn primary"
              onClick={() => setTab('code')}
            >
              Tayyor kod →
            </button>
          </div>
        </section>
      ) : null}

      {tab === 'code' ? (
        <section className="block">
          <div className="code-head">
            <h3>Arduino IDE ga joylang</h3>
            <button type="button" className="btn ghost" onClick={() => void copyCode()}>
              {copied ? 'Nusxalandi ✓' : 'Nusxa olish'}
            </button>
          </div>
          <pre className="code">
            <code>{lesson.code}</code>
          </pre>
          <p className="tip">💡 {lesson.tip}</p>
          <ol className="howto">
            <li>Arduino IDE → File → New</li>
            <li>Kodni joylashtiring (Ctrl+V)</li>
            <li>Tools → Board / Port ni tekshiring</li>
            <li>→ Upload · “Done uploading” ni kuting</li>
          </ol>
          <div className="actions">
            <button
              type="button"
              className="btn ghost"
              onClick={() => setTab('sim')}
            >
              ← Simulyator
            </button>
            <button
              type="button"
              className="btn primary"
              onClick={() => setTab('practice')}
            >
              Amaliyot →
            </button>
          </div>
        </section>
      ) : null}

      {tab === 'practice' ? (
        <section className="block">
          <h3>Amaliy qiling</h3>
          <ol className="practice-list">
            {lesson.practice.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ol>
          <div className="actions">
            <button
              type="button"
              className={`btn${isDone ? ' ghost' : ' primary'}`}
              onClick={() => toggleDone(lesson.id)}
            >
              {isDone ? 'Belgina olib tashlash' : 'Darsni tugalladim ✓'}
            </button>
            <button type="button" className="btn primary" onClick={nextLesson}>
              Keyingi dars →
            </button>
          </div>
        </section>
      ) : null}
    </div>
  )
}
