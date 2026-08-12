import { useEffect, useMemo, useState } from 'react'
import {
  DAYS,
  DEFAULT_PERIODS,
  SUBJECT_SUGGESTIONS,
  cellKey,
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

  const today = todayDayId(now)
  const dayMeta = DAYS.find((d) => d.id === day)!

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

  async function enableBudilnik() {
    const p = await ensureNotifyPermission()
    setPerm(p)
    setAlarm((a) => ({ ...a, enabled: true }))
    try {
      await playAlarmSound(1)
    } catch {
      /* user gesture may be required once */
    }
  }

  function dismissAlarm() {
    setActiveAlarm(null)
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

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">O‘quvchilar uchun</p>
        <h1 className="brand">
          Dars <span>jadvali</span>
        </h1>
        <p className="tagline">
          Fanlaringizni yozing — budilnik darsdan oldin eslatib turadi.
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

      <section className={`alarm-card ${alarm.enabled ? 'on' : ''}`}>
        <div className="alarm-top">
          <div>
            <h2>Budilnik</h2>
            <p>
              {alarm.enabled
                ? `Darsdan ${alarm.minutesBefore} daqiqa oldin + boshlanishida`
                : 'O‘chiq — yoqing, darsni o‘tkazib yubormang'}
            </p>
          </div>
          <button
            type="button"
            className={`toggle ${alarm.enabled ? 'on' : ''}`}
            aria-pressed={alarm.enabled}
            onClick={() => {
              if (!alarm.enabled) void enableBudilnik()
              else setAlarm((a) => ({ ...a, enabled: false }))
            }}
          >
            {alarm.enabled ? 'YOQIQ' : 'O‘CHIQ'}
          </button>
        </div>

        {upcoming && alarm.enabled && (
          <div className="next-box">
            <span>Keyingi dars</span>
            <strong>
              {upcoming.period.n}. {upcoming.subject}
            </strong>
            <em>
              {upcoming.start.getTime() > now.getTime()
                ? formatCountdown(upcoming.start.getTime() - now.getTime())
                : 'Hozir'}{' '}
              · {upcoming.period.start}
            </em>
          </div>
        )}

        <div className="alarm-opts">
          <label>
            Oldindan
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
          <label className="check">
            <input
              type="checkbox"
              checked={alarm.sound}
              onChange={(e) => setAlarm((a) => ({ ...a, sound: e.target.checked }))}
            />
            Ovoz
          </label>
          <label className="check">
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
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void enableBudilnik()}
            >
              Bildirishnoma ruxsati
            </button>
          )}
        </div>
        <p className="alarm-hint">
          Ishlashi uchun ilovani ochiq qoldiring yoki telefoningizga o‘rnating. Fon rejimida
          ba’zi telefonlarda cheklov bo‘lishi mumkin.
        </p>
      </section>

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
        Budilnik faqat fan yozilgan darslar uchun ishlaydi. Bo‘sh katakni bosib fan qo‘shing.
      </p>

      {activeAlarm && (
        <div className="alarm-overlay" role="alertdialog" aria-modal="true">
          <div className="alarm-modal">
            <p className="pulse-label">
              {activeAlarm.kind === 'before' ? 'Eslatma' : 'Qo‘ng‘iroq'}
            </p>
            <h2>
              {activeAlarm.period.n}-dars
              <br />
              {activeAlarm.subject}
            </h2>
            <p className="alarm-time">{activeAlarm.period.start}</p>
            <button type="button" className="btn btn-primary big" onClick={dismissAlarm}>
              O‘chirish
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
