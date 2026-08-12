import { useEffect, useMemo, useRef, useState } from 'react'
import {
  DAYS,
  SUBJECT_COLOR_PALETTE,
  SUBJECT_SUGGESTIONS,
  cellKey,
  createProfile,
  currentPeriod,
  emptyCell,
  getEffectiveCell,
  isoDate,
  todayDayId,
  uid,
  type AppSettings,
  type Cell,
  type DayId,
  type Profile,
} from './model'
import { activeProfile, downloadJson, loadSettings, readJsonFile, saveSettings } from './store'
import { t } from './i18n'
import {
  applyTemplate,
  buildIcs,
  colorForSubject,
  decodeShare,
  encodeShare,
  fetchWeather,
  listenOnce,
  periodsProgress,
  shareText,
  speak,
  weekStats,
} from './features'
import {
  ensureNotifyPermission,
  findDueAlarm,
  formatCountdown,
  loadFired,
  nextLessonsToday,
  playAlarmSound,
  saveFired,
  showSystemNotification,
  vibrateAlarm,
  type AlarmEvent,
} from './alarm'

type Tab = 'today' | 'week' | 'tasks' | 'more'

export default function App() {
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings())
  const [tab, setTab] = useState<Tab>('today')
  const [day, setDay] = useState<DayId>(() => todayDayId() ?? 'dush')
  const [now, setNow] = useState(() => new Date())
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState<Cell>(emptyCell())
  const [unlocked, setUnlocked] = useState(false)
  const [activeAlarm, setActiveAlarm] = useState<AlarmEvent | null>(null)
  const [fired, setFired] = useState(() => loadFired())
  const [weather, setWeather] = useState<{ temp: number; text: string } | null>(null)
  const [installOpen, setInstallOpen] = useState(false)
  const [voiceMsg, setVoiceMsg] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const dict = t(settings.lang)
  const profile = activeProfile(settings)
  const today = todayDayId(now)
  const readOnly = settings.parentMode && !unlocked
  const dateISO = isoDate(now)

  useEffect(() => {
    saveSettings(settings)
    document.documentElement.dataset.theme = settings.theme
  }, [settings])

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    void fetchWeather(settings.weatherCity).then(setWeather)
  }, [settings.weatherCity])

  useEffect(() => {
    // import from URL hash share
    const hash = location.hash.replace(/^#share=/, '')
    if (!hash) return
    const data = decodeShare(hash)
    if (!data) return
    const p = createProfile(data)
    update((s) => ({
      ...s,
      profiles: [...s.profiles, p],
      activeProfileId: p.id,
    }))
    location.hash = ''
    alert(settings.lang === 'ru' ? 'Расписание импортировано' : 'Jadval yuklandi')
  }, [])

  useEffect(() => {
    // streak: open app once per day
    const d = isoDate()
    if (settings.streak.lastDate === d) return
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const y = isoDate(yesterday)
    update((s) => ({
      ...s,
      streak: {
        lastDate: d,
        count: s.streak.lastDate === y ? s.streak.count + 1 : 1,
      },
    }))
  }, [])

  useEffect(() => {
    if (activeAlarm || readOnly) return
    const due = findDueAlarm(profile, settings.alarm, fired, now)
    if (!due) return
    setActiveAlarm(due)
    setFired((prev) => {
      const next = new Set(prev)
      next.add(due.id)
      saveFired(next)
      return next
    })
    showSystemNotification(due.message, `${due.period.n}. ${due.subject}`)
    if (settings.alarm.sound) void playAlarmSound(5)
    if (settings.alarm.vibrate) vibrateAlarm()
    speak(`${due.message}. ${due.subject}`, settings.lang)
  }, [now, profile, settings.alarm, fired, activeAlarm, readOnly, settings.lang])

  function update(fn: (s: AppSettings) => AppSettings) {
    setSettings((s) => fn(s))
  }

  function patchProfile(fn: (p: Profile) => Profile) {
    update((s) => ({
      ...s,
      profiles: s.profiles.map((p) => (p.id === s.activeProfileId ? fn(p) : p)),
    }))
  }

  const upcoming = useMemo(() => {
    const list = nextLessonsToday(profile, now)
    return list.find((x) => x.start.getTime() > now.getTime() - 30_000) ?? null
  }, [profile, now])

  const progress = periodsProgress(profile.periods, now)
  const stats = weekStats(profile)
  const live = today === day ? currentPeriod(profile.periods, now) : null

  const homeworks = useMemo(() => {
    const items: { key: string; day: string; n: number; cell: Cell }[] = []
    for (const d of DAYS) {
      for (const p of profile.periods) {
        const c = profile.cells[cellKey(d.id, p.n)]
        if (c?.homework.trim()) {
          items.push({
            key: cellKey(d.id, p.n),
            day: settings.lang === 'ru' ? d.fullRu : d.full,
            n: p.n,
            cell: c,
          })
        }
      }
    }
    return items
  }, [profile, settings.lang])

  function openEdit(key: string) {
    if (readOnly) return
    const [d, n] = key.split('-') as [DayId, string]
    setDraft(getEffectiveCell(profile, d, Number(n), dateISO))
    setEditing(key)
  }

  function commitEdit() {
    if (!editing) return
    const [d, n] = editing.split('-') as [DayId, string]
    patchProfile((p) => ({
      ...p,
      cells: { ...p.cells, [cellKey(d, Number(n))]: { ...draft } },
    }))
    setEditing(null)
  }

  function tryUnlock() {
    if (!settings.pin) {
      setUnlocked(true)
      return
    }
    const v = prompt(dict.pin)
    if (v === settings.pin) setUnlocked(true)
    else alert('PIN xato')
  }

  async function onVoice() {
    try {
      const text = await listenOnce(settings.lang)
      setVoiceMsg(text)
      const dayNow = todayDayId()
      if (!dayNow) {
        speak('Bugun dars yo‘q', settings.lang)
        return
      }
      const liveP = currentPeriod(profile.periods, new Date())
      if (liveP) {
        const c = getEffectiveCell(profile, dayNow, liveP.n)
        const ans = `Hozir ${liveP.n}-dars, ${c.subject || 'bo‘sh'}`
        speak(ans, settings.lang)
        setVoiceMsg(ans)
        return
      }
      const next = nextLessonsToday(profile).find((x) => x.start > new Date())
      const ans = next
        ? `Keyingi dars ${next.period.n}, ${next.subject}, soat ${next.period.start}`
        : 'Bugun dars qolmadi'
      speak(ans, settings.lang)
      setVoiceMsg(ans)
    } catch {
      setVoiceMsg(settings.lang === 'ru' ? 'Микрофон недоступен' : 'Mikrofon ishlamadi')
    }
  }

  function exportIcs() {
    const ics = buildIcs(profile)
    const blob = new Blob([ics], { type: 'text/calendar' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${profile.className}-jadval.ics`
    a.click()
    URL.revokeObjectURL(url)
  }

  function doShare() {
    const code = encodeShare(profile)
    const link = `${location.origin}/jadval/#share=${code}`
    shareText(dict.brand, `${profile.className} — ${profile.schoolName}\n${link}`)
  }

  const clock = now.toLocaleTimeString(settings.lang === 'ru' ? 'ru-RU' : 'uz-UZ', {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className="shell">
      <div className="bg" aria-hidden />
      <header className="hero no-print">
        <div className="hero-row">
          <h1 className="brand">{dict.brand}</h1>
          <time className="clock">{clock}</time>
        </div>
        <p className="tag">{dict.tagline}</p>
        <div className="quick">
          <span className="pill">
            {profile.className} · {profile.schoolName}
          </span>
          {weather && (
            <span className="pill accent">
              {dict.weather}: {weather.temp}° · {weather.text}
            </span>
          )}
          <span className="pill">
            {dict.streak}: {settings.streak.count}
          </span>
        </div>
        {(upcoming || progress.kind !== 'idle') && (
          <div className="status">
            <div className="status-top">
              <span>{progress.kind === 'break' ? dict.break : upcoming ? dict.next : dict.now}</span>
              <strong>
                {progress.kind === 'lesson'
                  ? `${progress.n}. ${getEffectiveCell(profile, today!, progress.n!).subject || '—'}`
                  : upcoming
                    ? `${upcoming.period.n}. ${upcoming.subject}`
                    : progress.label}
              </strong>
            </div>
            {progress.kind !== 'idle' && (
              <div className="bar">
                <i style={{ width: `${progress.pct}%` }} />
              </div>
            )}
            {upcoming && upcoming.start > now && (
              <em>
                {formatCountdown(upcoming.start.getTime() - now.getTime())} · {upcoming.period.start}
              </em>
            )}
          </div>
        )}
      </header>

      {tab === 'today' && (
        <section className="panel">
          <div className="panel-h">
            <div>
              <h2>{dict.todayLesson}</h2>
              <p>
                {stats.filled}/{stats.total} {dict.filled}
              </p>
            </div>
            <div className="row-actions no-print">
              <button type="button" className="ghost" onClick={() => setInstallOpen(true)}>
                {dict.install}
              </button>
              <button type="button" className="ghost" onClick={() => window.print()}>
                {dict.print}
              </button>
            </div>
          </div>
          <nav className="days no-print">
            {DAYS.map((d) => (
              <button
                key={d.id}
                type="button"
                className={`day ${day === d.id ? 'on' : ''} ${today === d.id ? 'today' : ''}`}
                onClick={() => setDay(d.id)}
              >
                {settings.lang === 'ru' ? d.shortRu : d.short}
              </button>
            ))}
          </nav>
          <ol className="timeline">
            {profile.periods.map((p) => {
              const key = cellKey(day, p.n)
              const cell = getEffectiveCell(profile, day, p.n, dateISO)
              const col = colorForSubject(cell.subject, profile.subjectColors)
              const isLive = live?.n === p.n
              const fav = profile.favorites.includes(cell.subject)
              return (
                <li key={key} className={`slot ${isLive ? 'live' : ''} ${cell.subject ? '' : 'empty'}`}>
                  <div className="rail">
                    <span style={{ background: cell.subject ? col : undefined }}>{p.n}</span>
                  </div>
                  <button
                    type="button"
                    className="slot-btn"
                    onClick={() => openEdit(key)}
                    style={{ borderColor: cell.subject ? `${col}55` : undefined }}
                  >
                    <div className="slot-t">
                      <strong>
                        {fav ? '★ ' : ''}
                        {cell.subject || dict.empty}
                      </strong>
                      {isLive && <em>{dict.now}</em>}
                    </div>
                    <span>
                      {p.start}–{p.end}
                      {cell.room ? ` · ${cell.room}` : ''}
                      {cell.teacher ? ` · ${cell.teacher}` : ''}
                    </span>
                    {cell.note && <small>{cell.note}</small>}
                    {cell.homework && (
                      <small className={cell.homeworkDone ? 'done' : 'hw'}>
                        {dict.homework}: {cell.homework}
                      </small>
                    )}
                  </button>
                </li>
              )
            })}
          </ol>
        </section>
      )}

      {tab === 'week' && (
        <section className="panel week-panel">
          <div className="panel-h">
            <h2>{dict.week}</h2>
            <p>
              {profile.className} · 9 {dict.todayLesson.toLowerCase()}
            </p>
          </div>
          <div className="week-grid">
            <div className="week-head">
              <div />
              {DAYS.map((d) => (
                <div key={d.id} className="week-day">
                  {settings.lang === 'ru' ? d.shortRu : d.short}
                </div>
              ))}
            </div>
            {profile.periods.map((p) => (
              <div key={p.n} className="week-row">
                <div className="week-n">{p.n}</div>
                {DAYS.map((d) => {
                  const c = getEffectiveCell(profile, d.id, p.n, dateISO)
                  const col = colorForSubject(c.subject, profile.subjectColors)
                  return (
                    <button
                      key={d.id}
                      type="button"
                      className="week-cell"
                      style={{
                        background: c.subject ? `${col}22` : undefined,
                        borderColor: c.subject ? col : undefined,
                      }}
                      onClick={() => {
                        setDay(d.id)
                        setTab('today')
                        openEdit(cellKey(d.id, p.n))
                      }}
                      title={c.subject}
                    >
                      {c.subject ? c.subject.slice(0, 8) : '·'}
                    </button>
                  )
                })}
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === 'tasks' && (
        <section className="panel stack">
          <div className="panel-h">
            <h2>{dict.tasks}</h2>
          </div>
          {homeworks.length === 0 && <p className="muted">—</p>}
          {homeworks.map((h) => (
            <label key={h.key} className="task-row">
              <input
                type="checkbox"
                disabled={readOnly}
                checked={h.cell.homeworkDone}
                onChange={(e) => {
                  patchProfile((p) => ({
                    ...p,
                    cells: {
                      ...p.cells,
                      [h.key]: { ...h.cell, homeworkDone: e.target.checked },
                    },
                  }))
                }}
              />
              <div>
                <strong>
                  {h.day} · {h.n}. {h.cell.subject}
                </strong>
                <p>{h.cell.homework}</p>
              </div>
            </label>
          ))}

          <h3>{dict.checklist}</h3>
          {profile.checklist.map((c) => (
            <label key={c.id} className="task-row">
              <input
                type="checkbox"
                disabled={readOnly}
                checked={c.done}
                onChange={(e) => {
                  patchProfile((p) => ({
                    ...p,
                    checklist: p.checklist.map((x) =>
                      x.id === c.id ? { ...x, done: e.target.checked } : x,
                    ),
                  }))
                }}
              />
              <span>{c.text}</span>
            </label>
          ))}
          {!readOnly && (
            <button
              type="button"
              className="ghost"
              onClick={() => {
                const text = prompt(dict.checklist)
                if (!text) return
                patchProfile((p) => ({
                  ...p,
                  checklist: [...p.checklist, { id: uid(), text, done: false }],
                }))
              }}
            >
              + {dict.add}
            </button>
          )}

          <h3>{dict.grades}</h3>
          {profile.grades.map((g) => (
            <div key={g.id} className="line-item">
              <strong>
                {g.subject}: {g.score}
              </strong>
              <span>
                {g.date} {g.note}
              </span>
            </div>
          ))}
          {!readOnly && (
            <button
              type="button"
              className="ghost"
              onClick={() => {
                const subject = prompt(dict.subject) || ''
                const score = Number(prompt('5 / 4 / 3...') || '5')
                if (!subject) return
                patchProfile((p) => ({
                  ...p,
                  grades: [
                    ...p.grades,
                    { id: uid(), subject, score, date: isoDate(), note: '' },
                  ],
                }))
              }}
            >
              + {dict.grades}
            </button>
          )}

          <h3>{dict.attendance}</h3>
          <div className="row-actions">
            {(['present', 'absent', 'late'] as const).map((k) => (
              <button
                key={k}
                type="button"
                className={`ghost ${profile.attendance[dateISO] === k ? 'on' : ''}`}
                disabled={readOnly}
                onClick={() =>
                  patchProfile((p) => ({
                    ...p,
                    attendance: { ...p.attendance, [dateISO]: k },
                  }))
                }
              >
                {dict[k]}
              </button>
            ))}
          </div>
        </section>
      )}

      {tab === 'more' && (
        <section className="panel stack more">
          <h2>{dict.more}</h2>

          <div className="cardish">
            <h3>{dict.widget}</h3>
            <div className="widget-preview">
              <strong>{profile.className}</strong>
              <p>
                {upcoming
                  ? `${upcoming.period.n}. ${upcoming.subject} · ${upcoming.period.start}`
                  : '—'}
              </p>
              <small>
                {dict.streak} {settings.streak.count} · {weather ? `${weather.temp}°` : ''}
              </small>
            </div>
          </div>

          <div className="cardish">
            <h3>{dict.alarm}</h3>
            <label className="switch-row">
              <span>{dict.alarm}</span>
              <input
                type="checkbox"
                checked={settings.alarm.enabled}
                disabled={readOnly}
                onChange={(e) =>
                  update((s) => ({ ...s, alarm: { ...s.alarm, enabled: e.target.checked } }))
                }
              />
            </label>
            <label>
              {dict.commute} (min)
              <input
                type="number"
                min={0}
                max={120}
                disabled={readOnly}
                value={profile.commuteMinutes}
                onChange={(e) =>
                  patchProfile((p) => ({ ...p, commuteMinutes: Number(e.target.value) || 0 }))
                }
              />
            </label>
            <label>
              Eslatma matni
              <input
                disabled={readOnly}
                value={profile.alarmMessage}
                onChange={(e) => patchProfile((p) => ({ ...p, alarmMessage: e.target.value }))}
              />
            </label>
            <select
              disabled={readOnly}
              value={settings.alarm.minutesBefore}
              onChange={(e) =>
                update((s) => ({
                  ...s,
                  alarm: { ...s.alarm, minutesBefore: Number(e.target.value) },
                }))
              }
            >
              {[3, 5, 10, 15].map((n) => (
                <option key={n} value={n}>
                  {n} min
                </option>
              ))}
            </select>
            <button
              type="button"
              className="ghost"
              onClick={async () => {
                await ensureNotifyPermission()
                if (settings.alarm.sound) await playAlarmSound(2)
                if (settings.alarm.vibrate) vibrateAlarm()
                setActiveAlarm({
                  id: 'test',
                  period: profile.periods[0],
                  subject: 'Sinov',
                  kind: 'before',
                  message: profile.alarmMessage,
                })
              }}
            >
              {dict.testAlarm}
            </button>
          </div>

          <div className="cardish">
            <h3>{dict.events}</h3>
            {profile.events.map((ev) => (
              <div key={ev.id} className="line-item">
                <strong>
                  {dict[ev.type]} · {ev.date}
                </strong>
                <span>{ev.title}</span>
              </div>
            ))}
            {!readOnly && (
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  const title = prompt(dict.events) || ''
                  const date = prompt('YYYY-MM-DD', isoDate()) || isoDate()
                  if (!title) return
                  patchProfile((p) => ({
                    ...p,
                    events: [...p.events, { id: uid(), title, date, type: 'exam' }],
                  }))
                }}
              >
                + {dict.add}
              </button>
            )}
          </div>

          <div className="cardish">
            <h3>{dict.announce}</h3>
            {profile.announcements.map((a) => (
              <div key={a.id} className="line-item">
                <span>{a.text}</span>
                <small>{new Date(a.at).toLocaleString()}</small>
              </div>
            ))}
            {!readOnly && (
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  const text = prompt(dict.announce)
                  if (!text) return
                  patchProfile((p) => ({
                    ...p,
                    announcements: [{ id: uid(), text, at: new Date().toISOString() }, ...p.announcements],
                  }))
                }}
              >
                + {dict.add}
              </button>
            )}
          </div>

          <div className="cardish">
            <h3>{dict.clubs}</h3>
            {profile.clubs.map((c) => (
              <div key={c.id} className="line-item">
                <strong>{c.title}</strong>
                <span>
                  {c.day} · {c.time}
                </span>
              </div>
            ))}
            {!readOnly && (
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  const title = prompt(dict.clubs) || ''
                  if (!title) return
                  patchProfile((p) => ({
                    ...p,
                    clubs: [...p.clubs, { id: uid(), title, day: 'jum', time: '16:30' }],
                  }))
                }}
              >
                + {dict.add}
              </button>
            )}
          </div>

          <div className="cardish">
            <h3>{dict.stats}</h3>
            {stats.top.map(([name, n]) => (
              <div key={name} className="stat-row">
                <i style={{ background: colorForSubject(name, profile.subjectColors) }} />
                <span>{name}</span>
                <b>{n}</b>
              </div>
            ))}
          </div>

          <div className="cardish">
            <h3>{dict.motivation}</h3>
            <p className="motto">
              {settings.streak.count >= 7
                ? settings.lang === 'ru'
                  ? 'Отличная серия! Так держать.'
                  : 'Ajoyib ketma-ketlik! Davom eting.'
                : settings.lang === 'ru'
                  ? 'Каждый день — маленький шаг вперёд.'
                  : 'Har kun — kichik qadam oldinga.'}
            </p>
          </div>

          <div className="cardish">
            <h3>{dict.voice}</h3>
            <button type="button" className="primary" onClick={() => void onVoice()}>
              {dict.voice}
            </button>
            {voiceMsg && <p className="muted">{voiceMsg}</p>}
          </div>

          <div className="cardish tools">
            <h3>{dict.settings}</h3>
            <div className="row-actions">
              <button type="button" className="ghost" onClick={doShare}>
                {dict.share}
              </button>
              <button type="button" className="ghost" onClick={exportIcs}>
                {dict.calendar}
              </button>
              <button
                type="button"
                className="ghost"
                onClick={() => downloadJson(`jadval-${profile.className}.json`, settings)}
              >
                {dict.backup}
              </button>
              <button type="button" className="ghost" onClick={() => fileRef.current?.click()}>
                {dict.restore}
              </button>
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  downloadJson(`sinf-paketi-${profile.className}.json`, profile)
                }}
              >
                {dict.admin}
              </button>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="application/json"
              hidden
              onChange={async (e) => {
                const f = e.target.files?.[0]
                if (!f) return
                try {
                  const data = (await readJsonFile(f)) as AppSettings | Profile
                  if ('profiles' in data && Array.isArray((data as AppSettings).profiles)) {
                    setSettings(data as AppSettings)
                  } else {
                    const p = createProfile(data as Profile)
                    update((s) => ({
                      ...s,
                      profiles: [...s.profiles, p],
                      activeProfileId: p.id,
                    }))
                  }
                } catch {
                  alert('Fayl xato')
                }
              }}
            />

            <label>
              {dict.theme}
              <select
                value={settings.theme}
                onChange={(e) =>
                  update((s) => ({ ...s, theme: e.target.value as 'light' | 'dark' }))
                }
              >
                <option value="light">{dict.light}</option>
                <option value="dark">{dict.dark}</option>
              </select>
            </label>
            <label>
              {dict.lang}
              <select
                value={settings.lang}
                onChange={(e) =>
                  update((s) => ({ ...s, lang: e.target.value as 'uz' | 'ru' }))
                }
              >
                <option value="uz">O‘zbek</option>
                <option value="ru">Русский</option>
              </select>
            </label>
            <label>
              {dict.weather} city
              <input
                value={settings.weatherCity}
                onChange={(e) => update((s) => ({ ...s, weatherCity: e.target.value }))}
              />
            </label>
            <label className="switch-row">
              <span>{dict.parent}</span>
              <input
                type="checkbox"
                checked={settings.parentMode}
                onChange={(e) => {
                  update((s) => ({ ...s, parentMode: e.target.checked }))
                  setUnlocked(false)
                }}
              />
            </label>
            {settings.parentMode && (
              <button type="button" className="ghost" onClick={tryUnlock}>
                {unlocked ? dict.lock : dict.unlock}
              </button>
            )}
            <label>
              {dict.pin}
              <input
                type="password"
                disabled={readOnly}
                value={settings.pin}
                onChange={(e) => update((s) => ({ ...s, pin: e.target.value }))}
                placeholder="1234"
              />
            </label>

            <h4>{dict.profiles}</h4>
            <select
              value={settings.activeProfileId}
              onChange={(e) => update((s) => ({ ...s, activeProfileId: e.target.value }))}
            >
              {settings.profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.className} — {p.schoolName}
                </option>
              ))}
            </select>
            {!readOnly && (
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  const p = createProfile({ className: 'Yangi' })
                  update((s) => ({
                    ...s,
                    profiles: [...s.profiles, p],
                    activeProfileId: p.id,
                  }))
                }}
              >
                + {dict.profiles}
              </button>
            )}

            <label>
              {dict.class}
              <input
                disabled={readOnly}
                value={profile.className}
                onChange={(e) => patchProfile((p) => ({ ...p, className: e.target.value }))}
              />
            </label>
            <label>
              {dict.school}
              <input
                disabled={readOnly}
                value={profile.schoolName}
                onChange={(e) => patchProfile((p) => ({ ...p, schoolName: e.target.value }))}
              />
            </label>

            <h4>{dict.templates}</h4>
            <div className="row-actions">
              {(['empty', 'sample7', 'sample9'] as const).map((name) => (
                <button
                  key={name}
                  type="button"
                  className="ghost"
                  disabled={readOnly}
                  onClick={() => {
                    if (!confirm('Shablon qo‘llansinmi?')) return
                    const p = applyTemplate(name)
                    p.id = profile.id
                    patchProfile(() => p)
                  }}
                >
                  {name}
                </button>
              ))}
            </div>

            <h4>{dict.periods}</h4>
            {profile.periods.map((p, idx) => (
              <div key={p.n} className="period-edit">
                <b>{p.n}</b>
                <input
                  disabled={readOnly}
                  value={p.start}
                  onChange={(e) => {
                    const start = e.target.value
                    patchProfile((pr) => {
                      const periods = pr.periods.map((x, i) => (i === idx ? { ...x, start } : x))
                      return { ...pr, periods }
                    })
                  }}
                />
                <input
                  disabled={readOnly}
                  value={p.end}
                  onChange={(e) => {
                    const end = e.target.value
                    patchProfile((pr) => {
                      const periods = pr.periods.map((x, i) => (i === idx ? { ...x, end } : x))
                      return { ...pr, periods }
                    })
                  }}
                />
              </div>
            ))}

            <h4>{dict.favorites}</h4>
            <p className="muted">{profile.favorites.join(', ') || '—'}</p>
          </div>
        </section>
      )}

      <nav className="tabs no-print">
        {(
          [
            ['today', dict.todayLesson],
            ['week', dict.week],
            ['tasks', dict.tasks],
            ['more', dict.more],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            className={tab === k ? 'on' : ''}
            onClick={() => setTab(k)}
          >
            {label}
          </button>
        ))}
      </nav>

      {editing && (
        <div className="overlay">
          <div className="modal form">
            <h3>
              {dict.subject} · {editing}
            </h3>
            <label>
              {dict.subject}
              <input
                list="subjects"
                value={draft.subject}
                onChange={(e) => setDraft({ ...draft, subject: e.target.value })}
              />
            </label>
            <label>
              {dict.teacher}
              <input
                value={draft.teacher}
                onChange={(e) => setDraft({ ...draft, teacher: e.target.value })}
              />
            </label>
            <label>
              {dict.room}
              <input
                value={draft.room}
                onChange={(e) => setDraft({ ...draft, room: e.target.value })}
              />
            </label>
            <label>
              {dict.note}
              <input
                value={draft.note}
                onChange={(e) => setDraft({ ...draft, note: e.target.value })}
              />
            </label>
            <label>
              {dict.homework}
              <input
                value={draft.homework}
                onChange={(e) => setDraft({ ...draft, homework: e.target.value })}
              />
            </label>
            <label className="switch-row">
              <span>{dict.done}</span>
              <input
                type="checkbox"
                checked={draft.homeworkDone}
                onChange={(e) => setDraft({ ...draft, homeworkDone: e.target.checked })}
              />
            </label>
            <label className="switch-row">
              <span>{dict.favorites}</span>
              <input
                type="checkbox"
                checked={!!draft.subject && profile.favorites.includes(draft.subject)}
                onChange={(e) => {
                  if (!draft.subject) return
                  patchProfile((p) => {
                    const set = new Set(p.favorites)
                    if (e.target.checked) set.add(draft.subject)
                    else set.delete(draft.subject)
                    return { ...p, favorites: [...set] }
                  })
                }}
              />
            </label>
            <label>
              Rang
              <select
                value={profile.subjectColors[draft.subject] || ''}
                onChange={(e) => {
                  if (!draft.subject) return
                  const color = e.target.value
                  patchProfile((p) => ({
                    ...p,
                    subjectColors: { ...p.subjectColors, [draft.subject]: color },
                  }))
                }}
              >
                <option value="">Auto</option>
                {SUBJECT_COLOR_PALETTE.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            {today === day && (
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  const n = editing.split('-')[1]
                  patchProfile((p) => ({
                    ...p,
                    substitutions: {
                      ...p.substitutions,
                      [dateISO]: {
                        ...(p.substitutions[dateISO] || {}),
                        [n]: {
                          subject: draft.subject,
                          teacher: draft.teacher,
                          room: draft.room,
                        },
                      },
                    },
                  }))
                  alert(settings.lang === 'ru' ? 'Замена на сегодня сохранена' : 'Bugungi o‘rinbosar saqlandi')
                }}
              >
                Bugungi o‘rinbosar
              </button>
            )}
            <div className="row-actions">
              <button type="button" className="primary" onClick={commitEdit}>
                {dict.save}
              </button>
              <button type="button" className="ghost" onClick={() => setEditing(null)}>
                {dict.cancel}
              </button>
            </div>
          </div>
        </div>
      )}

      <datalist id="subjects">
        {SUBJECT_SUGGESTIONS.map((s) => (
          <option key={s} value={s} />
        ))}
      </datalist>

      {installOpen && (
        <div className="overlay" onClick={() => setInstallOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{dict.install}</h3>
            <ol className="install-steps">
              <li>Brauzer menyusini oching</li>
              <li>«Add to Home Screen» / «Bosh ekranga» ni bosing</li>
              <li>Jadvalni ilova kabi oching — offline ishlaydi</li>
            </ol>
            <button type="button" className="primary" onClick={() => setInstallOpen(false)}>
              OK
            </button>
          </div>
        </div>
      )}

      {activeAlarm && (
        <div className="overlay alarm">
          <div className="modal">
            <p className="kicker">{activeAlarm.kind === 'before' ? 'Eslatma' : 'Qo‘ng‘iroq'}</p>
            <h2>
              {activeAlarm.period.n}-dars
              <span>{activeAlarm.subject}</span>
            </h2>
            <p className="msg">{activeAlarm.message}</p>
            <button type="button" className="primary big" onClick={() => setActiveAlarm(null)}>
              O‘chirish
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
