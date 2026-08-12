import { useEffect, useMemo, useState } from 'react'
import {
  DAYS,
  DEFAULT_PERIODS,
  SUBJECT_SUGGESTIONS,
  cellKey,
  todayDayId,
  type DayId,
} from './schedule'
import { loadSchedule, saveSchedule } from './progress'

export default function App() {
  const [state, setState] = useState(() => loadSchedule())
  const [day, setDay] = useState<DayId>(() => todayDayId() ?? 'dush')
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')

  const today = todayDayId()
  const dayMeta = DAYS.find((d) => d.id === day)!

  useEffect(() => {
    saveSchedule(state)
  }, [state])

  const filledToday = useMemo(() => {
    return DEFAULT_PERIODS.filter((p) => state.subjects[cellKey(day, p.n)]?.trim()).length
  }, [state.subjects, day])

  function openEdit(key: string) {
    setEditing(key)
    setDraft(state.subjects[key] || '')
  }

  function commitEdit() {
    if (!editing) return
    const value = draft.trim()
    setState((s) => ({
      ...s,
      subjects: { ...s.subjects, [editing]: value },
    }))
    setEditing(null)
  }

  function clearDay() {
    setState((s) => {
      const subjects = { ...s.subjects }
      for (const p of DEFAULT_PERIODS) {
        subjects[cellKey(day, p.n)] = ''
      }
      return { ...s, subjects }
    })
  }

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">O‘quvchilar uchun</p>
        <h1 className="brand">
          Dars <span>jadvali</span>
        </h1>
        <p className="tagline">
          Sinfingiz fanlarini bir marta to‘ldiring — har kuni telefoningizda ko‘ring.
        </p>

        <div className="id-row">
          <label className="field">
            <span>Sinf</span>
            <input
              value={state.className}
              onChange={(e) => setState((s) => ({ ...s, className: e.target.value }))}
              placeholder="7-A"
              maxLength={12}
            />
          </label>
          <label className="field">
            <span>Maktab</span>
            <input
              value={state.schoolName}
              onChange={(e) => setState((s) => ({ ...s, schoolName: e.target.value }))}
              placeholder="№12-maktab"
              maxLength={40}
            />
          </label>
        </div>
      </header>

      <nav className="days" aria-label="Hafta kunlari">
        {DAYS.map((d) => (
          <button
            key={d.id}
            type="button"
            className={`day-btn ${day === d.id ? 'on' : ''} ${today === d.id ? 'today' : ''}`}
            onClick={() => setDay(d.id)}
          >
            {d.short}
          </button>
        ))}
      </nav>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>{dayMeta.full}</h2>
            <p>
              {state.className || 'Sinf'} · {filledToday}/{DEFAULT_PERIODS.length} dars
              {today === day ? ' · Bugun' : ''}
            </p>
          </div>
          <button type="button" className="text-btn" onClick={clearDay}>
            Kunni tozalash
          </button>
        </div>

        <ol className="periods">
          {DEFAULT_PERIODS.map((p) => {
            const key = cellKey(day, p.n)
            const subject = state.subjects[key] || ''
            const isEdit = editing === key
            return (
              <li key={key} className={`period ${subject ? '' : 'empty'} ${isEdit ? 'edit' : ''}`}>
                <div className="p-num">{p.n}</div>
                <div className="p-body">
                  {isEdit ? (
                    <div className="edit-box">
                      <input
                        autoFocus
                        list="subject-list"
                        value={draft}
                        placeholder="Fan nomi…"
                        onChange={(e) => setDraft(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') commitEdit()
                          if (e.key === 'Escape') setEditing(null)
                        }}
                      />
                      <div className="edit-actions">
                        <button type="button" className="btn btn-primary" onClick={commitEdit}>
                          Saqlash
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => setEditing(null)}
                        >
                          Bekor
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button type="button" className="subject-btn" onClick={() => openEdit(key)}>
                      <strong>{subject || 'Fan qo‘shish'}</strong>
                      <span>
                        {p.start} – {p.end}
                      </span>
                    </button>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      </section>

      <datalist id="subject-list">
        {SUBJECT_SUGGESTIONS.map((s) => (
          <option key={s} value={s} />
        ))}
      </datalist>

      <p className="foot">
        Ma’lumot telefoningizda saqlanadi. Bo‘sh katakni bosib fan yozing.
      </p>
    </div>
  )
}
