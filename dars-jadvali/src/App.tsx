import { useMemo, useState } from 'react'
import {
  GROUP,
  LESSONS,
  formatUzDate,
  getNextLesson,
  lessonStart,
  weekdayShort,
  type Lesson,
} from './schedule'
import { loadDone, saveDone } from './progress'

function statusOf(l: Lesson, nextId: string | null, now: Date) {
  if (nextId && l.id === nextId) return 'next' as const
  if (lessonStart(l).getTime() < now.getTime()) return 'past' as const
  return 'upcoming' as const
}

export default function App() {
  const now = useMemo(() => new Date(), [])
  const next = useMemo(() => getNextLesson(now), [now])
  const [done, setDone] = useState(() => loadDone())
  const [selected, setSelected] = useState<Lesson | null>(next)

  const doneCount = LESSONS.filter((l) => done.has(l.id)).length

  function toggleDone(id: string) {
    setDone((prev) => {
      const nextSet = new Set(prev)
      if (nextSet.has(id)) nextSet.delete(id)
      else nextSet.add(id)
      saveDone(nextSet)
      return nextSet
    })
  }

  return (
    <div className="app">
      <header className="hero">
        <p className="brand">
          32<span>-GR</span>
        </p>
        <p className="course">{GROUP.course}</p>
        <p className="tagline">
          O‘quvchilar uchun dars jadvali — sana, vaqt va darslik bir joyda.
        </p>
        <div className="meta-row">
          <span className="chip">{GROUP.weekday} · {GROUP.time}</span>
          <span className="chip">{GROUP.mode}</span>
          <span className="chip">{GROUP.timezone}</span>
          <span className="chip">
            {doneCount}/{LESSONS.length} bajarildi
          </span>
        </div>
        <div className="cta-row">
          {next ? (
            <a className="btn btn-primary" href={next.arduinoPath}>
              Keyingi dars → {next.num}
            </a>
          ) : (
            <a className="btn btn-primary" href="/arduino/">
              Darslikka o‘tish
            </a>
          )}
          <a className="btn btn-ghost" href="/arduino/">
            Arduino Darslik
          </a>
        </div>
      </header>

      <section className="section">
        <div className="section-head">
          <h2>Dars jadvali</h2>
          <p>6 ta dars · Juma 20:51</p>
        </div>

        <div className="list">
          {LESSONS.map((l) => {
            const st = statusOf(l, next?.id ?? null, now)
            const isDone = done.has(l.id)
            return (
              <button
                key={l.id}
                type="button"
                className={`lesson ${st === 'next' ? 'next' : ''} ${isDone ? 'done' : ''}`}
                onClick={() => setSelected(l)}
              >
                <div className="num">{l.num}</div>
                <div className="body">
                  <h3>{l.title}</h3>
                  <p className="topic">{l.topic}</p>
                  <div className="when">
                    <span>
                      <strong>{weekdayShort(l.date)}</strong> {formatUzDate(l.date)}
                    </span>
                    <span>{l.time}</span>
                    <span>{l.minutes} daq</span>
                    <span>{l.tasks} topshiriq</span>
                  </div>
                </div>
                <div className="side">
                  {st === 'next' && <span className="badge">Keyingi</span>}
                  {st === 'past' && !isDone && <span className="badge past">O‘tdi</span>}
                  {isDone && <span className="badge">✓</span>}
                  <span
                    role="checkbox"
                    aria-checked={isDone}
                    aria-label="Bajarildi deb belgilash"
                    className={`check ${isDone ? 'on' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleDone(l.id)
                    }}
                  >
                    ✓
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </section>

      {selected && (
        <section className="detail" aria-live="polite">
          <h3>
            {selected.num}-dars. {selected.title}
          </h3>
          <p>{selected.topic}</p>
          <p>
            {formatUzDate(selected.date)} · {selected.time} · {selected.minutes} daqiqa ·{' '}
            {selected.tasks} ta uyga vazifa
          </p>
          <div className="actions">
            <a className="btn btn-primary" href={selected.arduinoPath}>
              Darslikni ochish
            </a>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => toggleDone(selected.id)}
            >
              {done.has(selected.id) ? 'Belgila olib tashlash' : 'Bajarildi'}
            </button>
          </div>
        </section>
      )}

      <p className="foot">
        Telefon yoki PC ga o‘rnatib qo‘ying. Darslik:{' '}
        <a href="/arduino/">/arduino/</a>
      </p>
    </div>
  )
}
