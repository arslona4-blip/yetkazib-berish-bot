import { useEffect, useMemo, useState } from 'react'
import {
  DAYS,
  DEFAULT_PERIODS,
  SUBJECT_SUGGESTIONS,
  cellKey,
  currentPeriod,
  parseClock,
  todayDayId,
  type DayId,
} from './schedule'
import {
  loadAlarmSettings,
  loadFired,
  loadSchedule,
  saveAlarmSettings,
  saveFired,
  saveSchedule,
} from './progress'
import {
  ensureNotifyPermission,
  findDueAlarm,
  formatCountdown,
  nextLessonsToday,
  playAlarmSound,
  showSystemNotification,
  vibrateAlarm,
  type AlarmEvent,
  type AlarmSettings,
} from './alarm'

export default function App() {
  const [state, setState] = useState(() => loadSchedule())
  const [alarm, setAlarm] = useState<AlarmSettings>(() => loadAlarmSettings())
  const [day, setDay] = useState<DayId>(() => todayDayId() ?? 'dush')
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [now, setNow] = useState(() => new Date())
  const [activeAlarm, setActiveAlarm] = useState<AlarmEvent | null>(null)
  const [fired, setFired] = useState(() => loadFired())
  const [perm, setPerm] = useState<NotificationPermission>(() =>
    typeof Notification !== 'undefined' ? Notification.permission : 'denied',
  )
  const [alarmOpen, setAlarmOpen] = useState(false)

  const today = todayDayId(now)
  const dayMeta = DAYS.find((d) => d.id === day)!
  const livePeriod = today === day ? currentPeriod(now) : null

  useEffect(() => {
    saveSchedule(state)
  }, [state])

  useEffect(() => {
    saveAlarmSettings(alarm)
  }, [alarm])

  useEffect(() => {
    const t = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(t)
  }, [])

  useEffect(() => {
    if (activeAlarm) return
    const due = findDueAlarm(state.subjects, alarm, fired, now)
    if (!due) return
    setActiveAlarm(due)
    setFired((prev) => {
      const next = new Set(prev)
      next.add(due.id)
      saveFired(next)
      return next
    })
    const title =
      due.kind === 'before'
        ? `${alarm.minutesBefore} daqiqadan keyin dars`
        : 'Dars boshlandi!'
    const body = `${due.period.n}-dars · ${due.subject} · ${due.period.start}`
    showSystemNotification(title, body)
    if (alarm.sound) void playAlarmSound(5)
    if (alarm.vibrate) vibrateAlarm()
  }, [now, state.subjects, alarm, fired, activeAlarm])

  const upcoming = useMemo(() => {
    const list = nextLessonsToday(state.subjects, today, now)
    return list.find((x) => x.start.getTime() > now.getTime() - 30_000) ?? null
  }, [state.subjects, today, now])

  const weekFilled = useMemo(() => {
    let n = 0
    let total = 0
    for (const d of DAYS) {
      for (const p of DEFAULT_PERIODS) {
        total++
        if (state.subjects[cellKey(d.id, p.n)]?.trim()) n++
      }
    }
    return { n, total, pct: total ? Math.round((n / total) * 100) : 0 }
  }, [state.subjects])

  const filledDay = useMemo(() => {
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
    if (!window.confirm(`${dayMeta.full} fanlarini tozalaysizmi?`)) return
    setState((s) => {
      const subjects = { ...s.subjects }
      for (const p of DEFAULT_PERIODS) {
        subjects[cellKey(day, p.n)] = ''
      }
      return { ...s, subjects }
    })
  }

  async function enableBudilnik() {
    const p = await ensureNotifyPermission()
    setPerm(p)
    setAlarm((a) => ({ ...a, enabled: true }))
    try {
      await playAlarmSound(1)
    } catch {
      /* ignore */
    }
  }

  async function testAlarm() {
    const p = await ensureNotifyPermission()
    setPerm(p)
    showSystemNotification('Sinov budilnik', 'Dars eslatmasi ishlayapti')
    if (alarm.sound) await playAlarmSound(3)
    if (alarm.vibrate) vibrateAlarm()
    setActiveAlarm({
      id: 'test',
      period: DEFAULT_PERIODS[0],
      subject: 'Sinov darsi',
      kind: 'before',
      at: new Date(),
    })
  }

  const clock = now.toLocaleTimeString('uz-UZ', {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className="app">
      <div className="bg-grid" aria-hidden="true" />

      <header className="hero">
        <div className="hero-top">
          <p className="brand">Jadval</p>
          <time className="live-clock" dateTime={now.toISOString()}>
            {clock}
          </time>
        </div>
        <p className="tagline">
          Ixtisoslashtirilgan maktab — 9 dars, budilnik va shaxsiy fanlar.
        </p>

        <div className="identity">
          <label className="field">
            <span>Sinf</span>
            <input
              value={state.className}
              onChange={(e) => setState((s) => ({ ...s, className: e.target.value }))}
              placeholder="9-A"
              maxLength={12}
            />
          </label>
          <label className="field grow">
            <span>Maktab</span>
            <input
              value={state.schoolName}
              onChange={(e) => setState((s) => ({ ...s, schoolName: e.target.value }))}
              placeholder="Ixtisoslashtirilgan maktab"
              maxLength={48}
            />
          </label>
        </div>

        <div className="hero-cta">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              if (today) setDay(today)
              document.getElementById('timetable')?.scrollIntoView({ behavior: 'smooth' })
            }}
          >
            Bugungi dars
          </button>
          <button
            type="button"
            className={`btn btn-ghost ${alarm.enabled ? 'active' : ''}`}
            onClick={() => setAlarmOpen((v) => !v)}
          >
            Budilnik {alarm.enabled ? '· yoqiq' : ''}
          </button>
        </div>
      </header>

      {upcoming && (
        <section className="status" aria-live="polite">
          <div className="status-label">
            {upcoming.start.getTime() <= now.getTime() &&
            parseClock(upcoming.period.end, now).getTime() > now.getTime()
              ? 'Hozirgi dars'
              : 'Keyingi dars'}
          </div>
          <div className="status-main">
            <span className="status-num">{upcoming.period.n}</span>
            <div>
              <strong>{upcoming.subject}</strong>
              <p>
                {upcoming.period.start}–{upcoming.period.end}
                {upcoming.start.getTime() > now.getTime()
                  ? ` · ${formatCountdown(upcoming.start.getTime() - now.getTime())}`
                  : ''}
              </p>
            </div>
          </div>
          <div className="status-meter" aria-hidden="true">
            <span style={{ width: `${weekFilled.pct}%` }} />
          </div>
          <p className="status-meta">
            Hafta to‘ldirilgan: {weekFilled.n}/{weekFilled.total}
          </p>
        </section>
      )}

      {alarmOpen && (
        <section className={`alarm-panel ${alarm.enabled ? 'on' : ''}`}>
          <div className="alarm-top">
            <div>
              <h2>Budilnik</h2>
              <p>
                {alarm.enabled
                  ? `Darsdan ${alarm.minutesBefore} daqiqa oldin va boshlanishida`
                  : 'Yoqing — darsni o‘tkazib yubormaysiz'}
              </p>
            </div>
            <button
              type="button"
              className={`switch ${alarm.enabled ? 'on' : ''}`}
              aria-pressed={alarm.enabled}
              onClick={() => {
                if (!alarm.enabled) void enableBudilnik()
                else setAlarm((a) => ({ ...a, enabled: false }))
              }}
            >
              <i />
            </button>
          </div>

          <div className="alarm-grid">
            <label className="opt">
              <span>Oldindan</span>
              <select
                value={alarm.minutesBefore}
                onChange={(e) =>
                  setAlarm((a) => ({ ...a, minutesBefore: Number(e.target.value) }))
                }
              >
                <option value={3}>3 daqiqa</option>
                <option value={5}>5 daqiqa</option>
                <option value={10}>10 daqiqa</option>
                <option value={15}>15 daqiqa</option>
              </select>
            </label>
            <label className="opt check">
              <input
                type="checkbox"
                checked={alarm.sound}
                onChange={(e) => setAlarm((a) => ({ ...a, sound: e.target.checked }))}
              />
              Ovoz
            </label>
            <label className="opt check">
              <input
                type="checkbox"
                checked={alarm.vibrate}
                onChange={(e) => setAlarm((a) => ({ ...a, vibrate: e.target.checked }))}
              />
              Tebranish
            </label>
          </div>

          <div className="alarm-actions">
            <button type="button" className="btn btn-ghost" onClick={() => void testAlarm()}>
              Sinab ko‘rish
            </button>
            {perm !== 'granted' && (
              <button type="button" className="btn btn-primary" onClick={() => void enableBudilnik()}>
                Ruxsat berish
              </button>
            )}
          </div>
          <p className="hint">
            Ishonchli eslatma uchun ilovani ochiq qoldiring yoki telefoningizga o‘rnating.
          </p>
        </section>
      )}

      <nav className="days" aria-label="Hafta kunlari">
        {DAYS.map((d) => (
          <button
            key={d.id}
            type="button"
            className={`day ${day === d.id ? 'on' : ''} ${today === d.id ? 'today' : ''}`}
            onClick={() => setDay(d.id)}
          >
            <span>{d.short}</span>
            {today === d.id && <i className="dot" />}
          </button>
        ))}
      </nav>

      <section className="timetable" id="timetable">
        <div className="tt-head">
          <div>
            <h2>{dayMeta.full}</h2>
            <p>
              {state.className || 'Sinf'} · {filledDay}/9
              {today === day ? ' · Bugun' : ''}
            </p>
          </div>
          <button type="button" className="linkish" onClick={clearDay}>
            Tozalash
          </button>
        </div>

        <ol className="timeline">
          {DEFAULT_PERIODS.map((p, idx) => {
            const key = cellKey(day, p.n)
            const subject = state.subjects[key] || ''
            const isEdit = editing === key
            const isLive = livePeriod?.n === p.n
            const isPast =
              today === day && parseClock(p.end, now).getTime() < now.getTime() && !isLive
            return (
              <li
                key={key}
                className={[
                  'slot',
                  subject ? 'filled' : 'empty',
                  isEdit ? 'editing' : '',
                  isLive ? 'live' : '',
                  isPast ? 'past' : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
                style={{ animationDelay: `${0.04 + idx * 0.035}s` }}
              >
                <div className="rail">
                  <span className="n">{p.n}</span>
                  {idx < DEFAULT_PERIODS.length - 1 && <span className="line" />}
                </div>
                <div className="slot-body">
                  {isEdit ? (
                    <div className="editor">
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
                      <div className="editor-actions">
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
                    <button type="button" className="slot-btn" onClick={() => openEdit(key)}>
                      <div className="slot-title">
                        <strong>{subject || 'Fan qo‘shish'}</strong>
                        {isLive && <em className="live-tag">Hozir</em>}
                      </div>
                      <span className="slot-time">
                        {p.start} — {p.end}
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

      <footer className="foot">
        Fan yozilgan darslar uchun budilnik ishlaydi. Katakni bosib tahrirlang.
      </footer>

      {activeAlarm && (
        <div className="overlay" role="alertdialog" aria-modal="true">
          <div className="modal">
            <p className="modal-kicker">
              {activeAlarm.kind === 'before' ? 'Eslatma' : 'Qo‘ng‘iroq'}
            </p>
            <h2>
              {activeAlarm.period.n}-dars
              <span>{activeAlarm.subject}</span>
            </h2>
            <p className="modal-time">{activeAlarm.period.start}</p>
            <button type="button" className="btn btn-primary big" onClick={() => setActiveAlarm(null)}>
              O‘chirish
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
