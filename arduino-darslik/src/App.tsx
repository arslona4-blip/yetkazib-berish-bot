import { useMemo, useState } from 'react'
import { LESSONS, LEVEL_LABEL, type Lesson } from './lessons'
import { loadDone, saveDone } from './progress'
import { Simulator } from './Simulator'
import './styles.css'

type View = 'home' | 'lesson'
type Tab = 'steps' | 'sim' | 'code' | 'tasks' | 'practice'

export default function App() {
  const [view, setView] = useState<View>('home')
  const [lessonId, setLessonId] = useState(LESSONS[0].id)
  const [done, setDone] = useState<string[]>(() => loadDone())
  const [filter, setFilter] = useState<'all' | Lesson['level']>('all')
  const [tab, setTab] = useState<Tab>('steps')
  const [stepIdx, setStepIdx] = useState(0)
  const [taskIdx, setTaskIdx] = useState(0)
  const [copied, setCopied] = useState(false)
  const [showSolution, setShowSolution] = useState(false)

  const lesson = useMemo(
    () => LESSONS.find((l) => l.id === lessonId) || LESSONS[0],
    [lessonId],
  )

  const filtered = useMemo(() => {
    if (filter === 'all') return LESSONS
    return LESSONS.filter((l) => l.level === filter)
  }, [filter])

  const progress = Math.round((done.length / LESSONS.length) * 100)
  const task = lesson.tasks[taskIdx] || lesson.tasks[0]

  function openLesson(id: string) {
    setLessonId(id)
    setView('lesson')
    setTab('steps')
    setStepIdx(0)
    setTaskIdx(0)
    setShowSolution(false)
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

  async function copyText(text: string) {
    try {
      await navigator.clipboard.writeText(text)
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
          <p className="eyebrow">32-GR · Robototexnika · Telefon/PC</p>
          <h1>
            Arduino <span>Darslik</span>
          </h1>
          <p className="lead">
            6 ta dars: komponentlar, svetofor, PWM, Serial, int, if/else. Har
            darsda bosqichlar, simulyator, tayyor kod va topshiriq yechimlari.
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
              ['loyiha', 'Amaliyot'],
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
            return (
              <button
                key={l.id}
                type="button"
                className={`card${isDone ? ' done' : ''}`}
                onClick={() => openLesson(l.id)}
              >
                <div className="card-top">
                  <span className="num">{String(l.num).padStart(2, '0')}</span>
                  <span className="tag">{LEVEL_LABEL[l.level]}</span>
                </div>
                <h2>{l.title}</h2>
                <p>{l.summary}</p>
                <div className="card-foot">
                  <span>
                    {l.minutes} daq · {l.tasks.length} topshiriq
                  </span>
                  <span>{isDone ? '✓ Tugadi' : 'Boshlash →'}</span>
                </div>
              </button>
            )
          })}
        </section>

        <footer className="foot">1-darsdan boshlang: Arduino + maket + LED</footer>
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
            {idx + 1}/{LESSONS.length} · {lesson.minutes} daq ·{' '}
            {lesson.tasks.length} topshiriq
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
            ['code', 'Dars kodi'],
            ['tasks', 'Topshiriqlar'],
            ['practice', 'Yakun'],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            className={`chip${tab === k ? ' on' : ''}`}
            onClick={() => {
              setTab(k)
              setCopied(false)
              if (k === 'tasks') setShowSolution(false)
            }}
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
                  if (stepIdx < lesson.steps.length - 1) setStepIdx((s) => s + 1)
                  else setTab('sim')
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
            <button type="button" className="btn ghost" onClick={() => setTab('steps')}>
              ← Bosqichlar
            </button>
            <button type="button" className="btn primary" onClick={() => setTab('code')}>
              Dars kodi →
            </button>
          </div>
        </section>
      ) : null}

      {tab === 'code' ? (
        <section className="block">
          <div className="code-head">
            <h3>Asosiy dars kodi</h3>
            <button
              type="button"
              className="btn ghost"
              onClick={() => void copyText(lesson.code)}
            >
              {copied ? 'Nusxalandi ✓' : 'Nusxa olish'}
            </button>
          </div>
          <pre className="code">
            <code>{lesson.code}</code>
          </pre>
          <p className="tip">💡 {lesson.tip}</p>
          <ol className="howto">
            <li>Arduino IDE → File → New</li>
            <li>Kodni joylashtiring</li>
            <li>Board / Port ni tekshiring</li>
            <li>Upload → Done uploading</li>
          </ol>
          <div className="actions">
            <button type="button" className="btn ghost" onClick={() => setTab('sim')}>
              ← Simulyator
            </button>
            <button
              type="button"
              className="btn primary"
              onClick={() => setTab('tasks')}
            >
              Topshiriqlarga →
            </button>
          </div>
        </section>
      ) : null}

      {tab === 'tasks' && task ? (
        <section className="block">
          <div className="task-nav">
            {lesson.tasks.map((t) => (
              <button
                key={t.n}
                type="button"
                className={`chip${taskIdx === t.n - 1 ? ' on' : ''}`}
                onClick={() => {
                  setTaskIdx(t.n - 1)
                  setShowSolution(false)
                  setCopied(false)
                }}
              >
                {t.n}
              </button>
            ))}
          </div>
          <h3>
            Topshiriq {task.n}. {task.title}
          </h3>
          <p className="step-detail">{task.text}</p>
          <div className="actions">
            <button
              type="button"
              className="btn ghost"
              onClick={() => setShowSolution((v) => !v)}
            >
              {showSolution ? 'Yechimni yashirish' : 'Yechim kodini ko‘rsatish'}
            </button>
          </div>
          {showSolution ? (
            <>
              <div className="code-head" style={{ marginTop: 12 }}>
                <h3>Yechim</h3>
                <button
                  type="button"
                  className="btn ghost"
                  onClick={() => void copyText(task.code)}
                >
                  {copied ? 'Nusxalandi ✓' : 'Nusxa olish'}
                </button>
              </div>
              <pre className="code">
                <code>{task.code}</code>
              </pre>
            </>
          ) : (
            <p className="tip">Avval o‘zingiz yozing, keyin yechimni oching.</p>
          )}
          <div className="actions">
            <button
              type="button"
              className="btn ghost"
              disabled={taskIdx === 0}
              onClick={() => {
                setTaskIdx((i) => Math.max(0, i - 1))
                setShowSolution(false)
              }}
            >
              ← Oldingi
            </button>
            <button
              type="button"
              className="btn primary"
              onClick={() => {
                if (taskIdx < lesson.tasks.length - 1) {
                  setTaskIdx((i) => i + 1)
                  setShowSolution(false)
                } else setTab('practice')
              }}
            >
              {taskIdx < lesson.tasks.length - 1
                ? 'Keyingi topshiriq →'
                : 'Yakun →'}
            </button>
          </div>
        </section>
      ) : null}

      {tab === 'practice' ? (
        <section className="block">
          <h3>Yakuniy amaliyot</h3>
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
