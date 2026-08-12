import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
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
import {
  SERVICES,
  serviceDesc,
  serviceTitle,
  type ServiceId,
} from './services'
import { Icon } from './Icon'

type Tab = 'home' | 'schedule' | 'tasks' | 'profile'

export default function App() {
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings())
  const [tab, setTab] = useState<Tab>('home')
  const [sheet, setSheet] = useState<ServiceId | null>(null)
  const [day, setDay] = useState<DayId>(() => todayDayId() ?? 'dush')
  const [now, setNow] = useState(() => new Date())
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState<Cell>(emptyCell())
  const [unlocked, setUnlocked] = useState(false)
  const [activeAlarm, setActiveAlarm] = useState<AlarmEvent | null>(null)
  const [fired, setFired] = useState(() => loadFired())
  const [weather, setWeather] = useState<{ temp: number; text: string } | null>(null)
  const [query, setQuery] = useState('')
  const [voiceMsg, setVoiceMsg] = useState('')
  const [weekMode, setWeekMode] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const dict = t(settings.lang)
  const profile = activeProfile(settings)
  const today = todayDayId(now)
  const readOnly = settings.parentMode && !unlocked
  const dateISO = isoDate(now)
  const lang = settings.lang

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
    const hash = location.hash.replace(/^#share=/, '')
    if (!hash) return
    const data = decodeShare(hash)
    if (!data) return
    const p = createProfile(data)
    setSettings((s) => ({
      ...s,
      profiles: [...s.profiles, p],
      activeProfileId: p.id,
    }))
    location.hash = ''
  }, [])

  useEffect(() => {
    const d = isoDate()
    if (settings.streak.lastDate === d) return
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const y = isoDate(yesterday)
    setSettings((s) => ({
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
    speak(`${due.message}. ${due.subject}`, lang)
  }, [now, profile, settings.alarm, fired, activeAlarm, readOnly, lang])

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
    const items: { key: string; label: string; cell: Cell }[] = []
    for (const d of DAYS) {
      for (const p of profile.periods) {
        const c = profile.cells[cellKey(d.id, p.n)]
        if (c?.homework.trim()) {
          items.push({
            key: cellKey(d.id, p.n),
            label: `${lang === 'ru' ? d.shortRu : d.short} · ${p.n}. ${c.subject}`,
            cell: c,
          })
        }
      }
    }
    return items
  }, [profile, lang])

  const filteredServices = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return SERVICES
    return SERVICES.filter((s) =>
      `${serviceTitle(s, lang)} ${serviceDesc(s, lang)}`.toLowerCase().includes(q),
    )
  }, [query, lang])

  const featured = SERVICES.filter((s) => s.featured)

  function openService(id: ServiceId) {
    if (id === 'schedule') {
      setWeekMode(false)
      setTab('schedule')
      setSheet(null)
      return
    }
    if (id === 'week') {
      setWeekMode(true)
      setTab('schedule')
      setSheet(null)
      return
    }
    if (id === 'homework') {
      setTab('tasks')
      setSheet(null)
      return
    }
    if (id === 'print') {
      window.print()
      return
    }
    if (id === 'share') {
      const code = encodeShare(profile)
      shareText(dict.brand, `${location.origin}/jadval/#share=${code}`)
      return
    }
    if (id === 'calendar') {
      const blob = new Blob([buildIcs(profile)], { type: 'text/calendar' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${profile.className}.ics`
      a.click()
      URL.revokeObjectURL(url)
      return
    }
    if (id === 'admin') {
      downloadJson(`sinf-${profile.className}.json`, profile)
      return
    }
    if (id === 'backup') {
      downloadJson(`jadval-backup.json`, settings)
      return
    }
    setSheet(id)
  }

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

  async function onVoice() {
    try {
      const text = await listenOnce(lang)
      setVoiceMsg(text)
      const dayNow = todayDayId()
      if (!dayNow) {
        speak('Bugun dars yo‘q', lang)
        return
      }
      const liveP = currentPeriod(profile.periods, new Date())
      if (liveP) {
        const c = getEffectiveCell(profile, dayNow, liveP.n)
        const ans = `Hozir ${liveP.n}-dars, ${c.subject || 'bo‘sh'}`
        speak(ans, lang)
        setVoiceMsg(ans)
        return
      }
      const next = nextLessonsToday(profile).find((x) => x.start > new Date())
      const ans = next
        ? `Keyingi ${next.period.n}-dars, ${next.subject}`
        : 'Bugun dars qolmadi'
      speak(ans, lang)
      setVoiceMsg(ans)
    } catch {
      setVoiceMsg(lang === 'ru' ? 'Микрофон недоступен' : 'Mikrofon ishlamadi')
    }
  }

  const clock = now.toLocaleTimeString(lang === 'ru' ? 'ru-RU' : 'uz-UZ', {
    hour: '2-digit',
    minute: '2-digit',
  })

  const greet = lang === 'ru' ? 'Здравствуйте' : 'Assalomu alaykum'
  const heroMeta = [clock, weather ? `${weather.temp}°` : ''].filter(Boolean).join(' · ')

  return (
    <div className="app">
      {tab === 'home' && (
        <>
          <header className="hero">
            <div className="hero-bg" aria-hidden />
            <div className="hero-top">
              <button type="button" className="icon-btn" onClick={() => setTab('profile')} aria-label="menu">
                <Icon name="menu" size={18} />
              </button>
              <div className="hero-actions">
                <button type="button" className="icon-btn" onClick={() => openService('announce')}>
                  <Icon name="chat" size={18} />
                </button>
                <button type="button" className="icon-btn badge" onClick={() => openService('alarm')}>
                  <Icon name="alarm" size={18} />
                </button>
              </div>
            </div>
            <p className="greet">{greet}</p>
            <p className="hero-sub">{heroMeta}</p>

            <div className="feature-rail">
              {featured.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className={`feature-card tone-${s.tone}`}
                  onClick={() => openService(s.id)}
                >
                  <span className="f-ico">
                    <Icon name={s.icon} size={28} />
                  </span>
                  <strong>{serviceTitle(s, lang)}</strong>
                  <small>{serviceDesc(s, lang)}</small>
                </button>
              ))}
            </div>
          </header>

          <section className="section">
            <div className="section-h">
              <h2>{lang === 'ru' ? 'Виджеты' : 'Vidjetlar'}</h2>
              <button type="button" className="text-link" onClick={() => openService('widget')}>
                ⚙
              </button>
            </div>
            <div className="widgets">
              <button type="button" className="widget" onClick={() => openService('schedule')}>
                <span className="w-ico">
                  <Icon name="schedule" />
                </span>
                <div>
                  <strong>{lang === 'ru' ? 'Следующий урок' : 'Keyingi dars'}</strong>
                  <p>
                    {upcoming
                      ? `${upcoming.period.n}. ${upcoming.subject}`
                      : lang === 'ru'
                        ? 'Нет уроков'
                        : 'Dars yo‘q'}
                  </p>
                </div>
                <span className="chev">›</span>
              </button>
              <button type="button" className="widget" onClick={() => openService('weather')}>
                <span className="w-ico">
                  <Icon name="weather" />
                </span>
                <div>
                  <strong>{dict.weather}</strong>
                  <p>{weather ? `${weather.temp}° · ${weather.text}` : '…'}</p>
                </div>
                <span className="chev">›</span>
              </button>
              <button type="button" className="widget" onClick={() => openService('homework')}>
                <span className="w-ico">
                  <Icon name="homework" />
                </span>
                <div>
                  <strong>{dict.homework}</strong>
                  <p>
                    {homeworks.filter((h) => !h.cell.homeworkDone).length}{' '}
                    {lang === 'ru' ? 'активных' : 'ta faol'}
                  </p>
                </div>
                <span className="chev">›</span>
              </button>
              <button type="button" className="widget" onClick={() => openService('motivation')}>
                <span className="w-ico">
                  <Icon name="motivation" />
                </span>
                <div>
                  <strong>{dict.streak}</strong>
                  <p>
                    {settings.streak.count} {lang === 'ru' ? 'дней' : 'kun'}
                  </p>
                </div>
                <span className="chev">›</span>
              </button>
            </div>
          </section>

          {(progress.kind !== 'idle' || upcoming) && (
            <section className="live-strip">
              <div>
                <span>{progress.kind === 'break' ? dict.break : dict.next}</span>
                <strong>
                  {progress.kind === 'lesson' && today
                    ? `${progress.n}. ${getEffectiveCell(profile, today, progress.n!).subject || '—'}`
                    : upcoming
                      ? `${upcoming.period.n}. ${upcoming.subject}`
                      : '—'}
                </strong>
              </div>
              {progress.kind !== 'idle' && (
                <div className="mini-bar">
                  <i style={{ width: `${progress.pct}%` }} />
                </div>
              )}
              {upcoming && upcoming.start > now && (
                <em>{formatCountdown(upcoming.start.getTime() - now.getTime())}</em>
              )}
            </section>
          )}

          <section className="section">
            <div className="search">
              <Icon name="search" size={18} />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={lang === 'ru' ? 'Сервисни изланг' : 'Xizmatni izlang'}
              />
            </div>
            <div className="section-h" style={{ marginTop: '1rem' }}>
              <h2>{lang === 'ru' ? 'Все сервисы' : 'Barcha xizmatlar'}</h2>
              <span className="count">{filteredServices.length}</span>
            </div>
            <div className="service-grid">
              {filteredServices.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className={`svc tone-${s.tone}`}
                  onClick={() => openService(s.id)}
                >
                  <span className="svc-ico">
                    <Icon name={s.icon} size={20} />
                  </span>
                  <strong>{serviceTitle(s, lang)}</strong>
                </button>
              ))}
            </div>
          </section>
        </>
      )}

      {tab === 'schedule' && (
        <section className="page">
          <div className="page-h">
            <div>
              <h1>{weekMode ? dict.week : dict.todayLesson}</h1>
              <p>
                {[profile.className, `${stats.filled}/${stats.total}`].filter(Boolean).join(' · ')}
              </p>
            </div>
            <div className="seg">
              <button type="button" className={!weekMode ? 'on' : ''} onClick={() => setWeekMode(false)}>
                {lang === 'ru' ? 'День' : 'Kun'}
              </button>
              <button type="button" className={weekMode ? 'on' : ''} onClick={() => setWeekMode(true)}>
                {dict.week}
              </button>
            </div>
          </div>

          {!weekMode && (
            <>
              <nav className="days">
                {DAYS.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    className={`day ${day === d.id ? 'on' : ''} ${today === d.id ? 'today' : ''}`}
                    onClick={() => setDay(d.id)}
                  >
                    {lang === 'ru' ? d.shortRu : d.short}
                  </button>
                ))}
              </nav>
              <ol className="timeline">
                {profile.periods.map((p) => {
                  const key = cellKey(day, p.n)
                  const cell = getEffectiveCell(profile, day, p.n, dateISO)
                  const col = colorForSubject(cell.subject, profile.subjectColors)
                  const isLive = live?.n === p.n
                  return (
                    <li key={key} className={`slot ${isLive ? 'live' : ''}`}>
                      <span className="n" style={{ background: cell.subject ? col : '#94a3b8' }}>
                        {p.n}
                      </span>
                      <button type="button" className="slot-btn" onClick={() => openEdit(key)}>
                        <strong>
                          {profile.favorites.includes(cell.subject) ? '★ ' : ''}
                          {cell.subject || dict.empty}
                        </strong>
                        <span>
                          {p.start}–{p.end}
                          {cell.room ? ` · ${cell.room}` : ''}
                          {cell.teacher ? ` · ${cell.teacher}` : ''}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ol>
            </>
          )}

          {weekMode && (
            <div className="week">
              <div className="week-head">
                <i />
                {DAYS.map((d) => (
                  <b key={d.id}>{lang === 'ru' ? d.shortRu : d.short}</b>
                ))}
              </div>
              {profile.periods.map((p) => (
                <div key={p.n} className="week-row">
                  <em>{p.n}</em>
                  {DAYS.map((d) => {
                    const c = getEffectiveCell(profile, d.id, p.n, dateISO)
                    const col = colorForSubject(c.subject, profile.subjectColors)
                    return (
                      <button
                        key={d.id}
                        type="button"
                        style={{ background: c.subject ? `${col}28` : undefined }}
                        onClick={() => {
                          setDay(d.id)
                          setWeekMode(false)
                          openEdit(cellKey(d.id, p.n))
                        }}
                      >
                        {c.subject ? c.subject.slice(0, 6) : '·'}
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {tab === 'tasks' && (
        <section className="page">
          <div className="page-h">
            <h1>{dict.tasks}</h1>
          </div>
          <div className="cards">
            {homeworks.length === 0 && <p className="empty-hint">—</p>}
            {homeworks.map((h) => (
              <label key={h.key} className="check-card">
                <input
                  type="checkbox"
                  disabled={readOnly}
                  checked={h.cell.homeworkDone}
                  onChange={(e) =>
                    patchProfile((p) => ({
                      ...p,
                      cells: {
                        ...p.cells,
                        [h.key]: { ...h.cell, homeworkDone: e.target.checked },
                      },
                    }))
                  }
                />
                <div>
                  <strong>{h.label}</strong>
                  <p>{h.cell.homework}</p>
                </div>
              </label>
            ))}
          </div>
          <h3 className="subh">{dict.checklist}</h3>
          <div className="cards">
            {profile.checklist.map((c) => (
              <label key={c.id} className="check-card">
                <input
                  type="checkbox"
                  disabled={readOnly}
                  checked={c.done}
                  onChange={(e) =>
                    patchProfile((p) => ({
                      ...p,
                      checklist: p.checklist.map((x) =>
                        x.id === c.id ? { ...x, done: e.target.checked } : x,
                      ),
                    }))
                  }
                />
                <span>{c.text}</span>
              </label>
            ))}
          </div>
        </section>
      )}

      {tab === 'profile' && (
        <section className="page">
          <div className="profile-hero">
            <div className="avatar">
              {(profile.className || 'J').slice(0, 2).toUpperCase()}
            </div>
            <div>
              <h1>{profile.className || (lang === 'ru' ? 'Класс' : 'Sinf')}</h1>
              <p>{profile.schoolName || (lang === 'ru' ? 'Школа' : 'Maktab')}</p>
            </div>
          </div>
          <div className="profile-grid">
            {(
              [
                'profiles',
                'bells',
                'theme',
                'lang',
                'parent',
                'pin',
                'install',
                'backup',
                'templates',
                'commute',
              ] as ServiceId[]
            ).map((id) => {
              const s = SERVICES.find((x) => x.id === id)!
              return (
                <button key={id} type="button" className="profile-item" onClick={() => openService(id)}>
                  <span className="p-ico">
                    <Icon name={s.icon} size={20} />
                  </span>
                  <strong>{serviceTitle(s, lang)}</strong>
                  <i>›</i>
                </button>
              )
            })}
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
                if ('profiles' in data) setSettings(data as AppSettings)
                else {
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
        </section>
      )}

      {/* Center quick sheet trigger handled in nav */}
      <nav className="tabbar no-print">
        <button type="button" className={tab === 'home' ? 'on' : ''} onClick={() => setTab('home')}>
          <Icon name="home" size={20} />
          {lang === 'ru' ? 'Главная' : 'Asosiy'}
        </button>
        <button
          type="button"
          className={tab === 'schedule' ? 'on' : ''}
          onClick={() => {
            setWeekMode(false)
            setTab('schedule')
          }}
        >
          <Icon name="schedule" size={20} />
          {dict.todayLesson.split(' ')[0]}
        </button>
        <button
          type="button"
          className="center"
          onClick={() => openService('voice')}
          aria-label="quick"
        >
          <Icon name="voice" size={22} />
        </button>
        <button type="button" className={tab === 'tasks' ? 'on' : ''} onClick={() => setTab('tasks')}>
          <Icon name="homework" size={20} />
          {dict.tasks}
        </button>
        <button type="button" className={tab === 'profile' ? 'on' : ''} onClick={() => setTab('profile')}>
          <Icon name="user" size={20} />
          {lang === 'ru' ? 'Профиль' : 'Profil'}
        </button>
      </nav>

      {sheet && (
        <Sheet
          title={serviceTitle(SERVICES.find((s) => s.id === sheet)!, lang)}
          icon={SERVICES.find((s) => s.id === sheet)!.icon}
          onClose={() => setSheet(null)}
        >
          {sheet === 'bells' && (
            <div className="bell-grid">
              {profile.periods.map((p, idx) => (
                <div key={p.n} className="bell-row">
                  <span className="bell-n">{p.n}</span>
                  <input
                    disabled={readOnly}
                    value={p.start}
                    onChange={(e) => {
                      const start = e.target.value
                      patchProfile((pr) => ({
                        ...pr,
                        periods: pr.periods.map((x, i) => (i === idx ? { ...x, start } : x)),
                      }))
                    }}
                  />
                  <span className="dash">—</span>
                  <input
                    disabled={readOnly}
                    value={p.end}
                    onChange={(e) => {
                      const end = e.target.value
                      patchProfile((pr) => ({
                        ...pr,
                        periods: pr.periods.map((x, i) => (i === idx ? { ...x, end } : x)),
                      }))
                    }}
                  />
                </div>
              ))}
            </div>
          )}

          {sheet === 'alarm' && (
            <div className="form-stack">
              <label className="switch">
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
                Oldindan (min)
                <select
                  value={settings.alarm.minutesBefore}
                  disabled={readOnly}
                  onChange={(e) =>
                    update((s) => ({
                      ...s,
                      alarm: { ...s.alarm, minutesBefore: Number(e.target.value) },
                    }))
                  }
                >
                  {[3, 5, 10, 15].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Eslatma matni
                <input
                  disabled={readOnly}
                  value={profile.alarmMessage}
                  onChange={(e) => patchProfile((p) => ({ ...p, alarmMessage: e.target.value }))}
                />
              </label>
              <button
                type="button"
                className="btn-primary"
                onClick={async () => {
                  await ensureNotifyPermission()
                  if (settings.alarm.sound) await playAlarmSound(2)
                  vibrateAlarm()
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
          )}

          {sheet === 'grades' && (
            <div className="form-stack">
              {profile.grades.map((g) => (
                <div key={g.id} className="mini-row">
                  <strong>
                    {g.subject}: {g.score}
                  </strong>
                  <span>{g.date}</span>
                </div>
              ))}
              {!readOnly && (
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => {
                    const subject = prompt(dict.subject) || ''
                    const score = Number(prompt('5/4/3') || '5')
                    if (!subject) return
                    patchProfile((p) => ({
                      ...p,
                      grades: [...p.grades, { id: uid(), subject, score, date: isoDate(), note: '' }],
                    }))
                  }}
                >
                  + {dict.add}
                </button>
              )}
            </div>
          )}

          {sheet === 'attendance' && (
            <div className="seg big">
              {(['present', 'absent', 'late'] as const).map((k) => (
                <button
                  key={k}
                  type="button"
                  className={profile.attendance[dateISO] === k ? 'on' : ''}
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
          )}

          {sheet === 'events' && (
            <div className="form-stack">
              {profile.events.map((ev) => (
                <div key={ev.id} className="mini-row">
                  <strong>
                    {dict[ev.type]} · {ev.date}
                  </strong>
                  <span>{ev.title}</span>
                </div>
              ))}
              {!readOnly && (
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => {
                    const title = prompt(dict.events) || ''
                    if (!title) return
                    patchProfile((p) => ({
                      ...p,
                      events: [...p.events, { id: uid(), title, date: isoDate(), type: 'exam' }],
                    }))
                  }}
                >
                  + {dict.add}
                </button>
              )}
            </div>
          )}

          {sheet === 'clubs' && (
            <div className="form-stack">
              {profile.clubs.map((c) => (
                <div key={c.id} className="mini-row">
                  <strong>{c.title}</strong>
                  <span>
                    {c.day} · {c.time}
                  </span>
                </div>
              ))}
              {!readOnly && (
                <button
                  type="button"
                  className="btn-ghost"
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
          )}

          {sheet === 'checklist' && (
            <div className="form-stack">
              {profile.checklist.map((c) => (
                <label key={c.id} className="check-card">
                  <input
                    type="checkbox"
                    disabled={readOnly}
                    checked={c.done}
                    onChange={(e) =>
                      patchProfile((p) => ({
                        ...p,
                        checklist: p.checklist.map((x) =>
                          x.id === c.id ? { ...x, done: e.target.checked } : x,
                        ),
                      }))
                    }
                  />
                  <span>{c.text}</span>
                </label>
              ))}
            </div>
          )}

          {sheet === 'weather' && (
            <div className="weather-card">
              <div className="w-big">{weather ? `${weather.temp}°` : '—'}</div>
              <p>{weather?.text || '…'}</p>
              <label>
                Shahar
                <input
                  value={settings.weatherCity}
                  onChange={(e) => update((s) => ({ ...s, weatherCity: e.target.value }))}
                />
              </label>
            </div>
          )}

          {sheet === 'voice' && (
            <div className="form-stack center-text">
              <p>{lang === 'ru' ? 'Спросите: какой сейчас урок?' : 'So‘rang: hozir nechinchi dars?'}</p>
              <button type="button" className="btn-primary" onClick={() => void onVoice()}>
                <Icon name="voice" size={18} /> {dict.voice}
              </button>
              {voiceMsg && <p className="muted">{voiceMsg}</p>}
            </div>
          )}

          {sheet === 'theme' && (
            <div className="seg big">
              <button
                type="button"
                className={settings.theme === 'light' ? 'on' : ''}
                onClick={() => update((s) => ({ ...s, theme: 'light' }))}
              >
                {dict.light}
              </button>
              <button
                type="button"
                className={settings.theme === 'dark' ? 'on' : ''}
                onClick={() => update((s) => ({ ...s, theme: 'dark' }))}
              >
                {dict.dark}
              </button>
            </div>
          )}

          {sheet === 'lang' && (
            <div className="seg big">
              <button
                type="button"
                className={settings.lang === 'uz' ? 'on' : ''}
                onClick={() => update((s) => ({ ...s, lang: 'uz' }))}
              >
                O‘zbek
              </button>
              <button
                type="button"
                className={settings.lang === 'ru' ? 'on' : ''}
                onClick={() => update((s) => ({ ...s, lang: 'ru' }))}
              >
                Русский
              </button>
            </div>
          )}

          {sheet === 'parent' && (
            <div className="form-stack">
              <label className="switch">
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
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => {
                    if (!settings.pin) {
                      setUnlocked(true)
                      return
                    }
                    const v = prompt(dict.pin)
                    if (v === settings.pin) setUnlocked(true)
                  }}
                >
                  {unlocked ? dict.lock : dict.unlock}
                </button>
              )}
            </div>
          )}

          {sheet === 'pin' && (
            <label className="form-stack">
              {dict.pin}
              <input
                type="password"
                disabled={readOnly}
                value={settings.pin}
                onChange={(e) => update((s) => ({ ...s, pin: e.target.value }))}
                placeholder="1234"
              />
            </label>
          )}

          {sheet === 'profiles' && (
            <div className="form-stack">
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
              {!readOnly && (
                <button
                  type="button"
                  className="btn-ghost"
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
            </div>
          )}

          {sheet === 'templates' && (
            <div className="seg col">
              {(['empty', 'sample7', 'sample9'] as const).map((name) => (
                <button
                  key={name}
                  type="button"
                  className="btn-ghost"
                  disabled={readOnly}
                  onClick={() => {
                    if (!confirm('OK?')) return
                    const p = applyTemplate(name)
                    p.id = profile.id
                    patchProfile(() => p)
                    setSheet(null)
                  }}
                >
                  {name}
                </button>
              ))}
            </div>
          )}

          {sheet === 'commute' && (
            <label className="form-stack">
              {dict.commute} (min)
              <input
                type="number"
                disabled={readOnly}
                value={profile.commuteMinutes}
                onChange={(e) =>
                  patchProfile((p) => ({ ...p, commuteMinutes: Number(e.target.value) || 0 }))
                }
              />
            </label>
          )}

          {sheet === 'install' && (
            <ol className="steps">
              <li>Brauzer menyusi → Share / Menyu</li>
              <li>«Add to Home Screen» ni bosing</li>
              <li>Jadval ilova kabi ochiladi</li>
            </ol>
          )}

          {sheet === 'widget' && (
            <div className="widget-xl">
              <strong>{profile.className || dict.brand}</strong>
              <p>
                {upcoming
                  ? `${upcoming.period.n}. ${upcoming.subject} · ${upcoming.period.start}`
                  : '—'}
              </p>
              <small>
                🔥 {settings.streak.count} · {weather ? `${weather.temp}°` : ''}
              </small>
            </div>
          )}

          {sheet === 'motivation' && (
            <div className="center-text">
              <div className="streak-big">{settings.streak.count}</div>
              <p>
                {settings.streak.count >= 7
                  ? lang === 'ru'
                    ? 'Отличная серия!'
                    : 'Ajoyib ketma-ketlik!'
                  : lang === 'ru'
                    ? 'Каждый день — шаг вперёд'
                    : 'Har kun — oldinga qadam'}
              </p>
            </div>
          )}

          {sheet === 'announce' && (
            <div className="form-stack">
              {profile.announcements.map((a) => (
                <div key={a.id} className="mini-row">
                  <span>{a.text}</span>
                </div>
              ))}
              {!readOnly && (
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => {
                    const text = prompt(dict.announce)
                    if (!text) return
                    patchProfile((p) => ({
                      ...p,
                      announcements: [
                        { id: uid(), text, at: new Date().toISOString() },
                        ...p.announcements,
                      ],
                    }))
                  }}
                >
                  + {dict.add}
                </button>
              )}
            </div>
          )}

          {sheet === 'stats' && (
            <div className="form-stack">
              {stats.top.map(([name, n]) => (
                <div key={name} className="stat">
                  <i style={{ background: colorForSubject(name, profile.subjectColors) }} />
                  <span>{name}</span>
                  <b>{n}</b>
                </div>
              ))}
            </div>
          )}

          {sheet === 'favorites' && (
            <p className="muted">{profile.favorites.join(', ') || '—'}</p>
          )}

          {(sheet === 'colors' || sheet === 'notes' || sheet === 'substitute') && (
            <p className="muted">
              {lang === 'ru'
                ? 'Откройте урок в расписании и редактируйте там.'
                : 'Darsni jadvaldan ochib tahrirlang (o‘qituvchi, xona, rang, o‘rinbosar).'}
            </p>
          )}

          {sheet === 'backup' && (
            <div className="seg col">
              <button
                type="button"
                className="btn-primary"
                onClick={() => downloadJson('jadval-backup.json', settings)}
              >
                {dict.backup}
              </button>
              <button type="button" className="btn-ghost" onClick={() => fileRef.current?.click()}>
                {dict.restore}
              </button>
            </div>
          )}
        </Sheet>
      )}

      {editing && (
        <div className="overlay">
          <div className="sheet-card form">
            <h3>{dict.subject}</h3>
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
            <label className="switch">
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
                  patchProfile((p) => ({
                    ...p,
                    subjectColors: { ...p.subjectColors, [draft.subject]: e.target.value },
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
                className="btn-ghost"
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
                }}
              >
                Bugungi o‘rinbosar
              </button>
            )}
            <div className="row">
              <button type="button" className="btn-primary" onClick={commitEdit}>
                {dict.save}
              </button>
              <button type="button" className="btn-ghost" onClick={() => setEditing(null)}>
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

      {activeAlarm && (
        <div className="overlay">
          <div className="sheet-card alarm">
            <p className="kicker">{activeAlarm.kind === 'before' ? 'Eslatma' : 'Qo‘ng‘iroq'}</p>
            <h2>
              {activeAlarm.period.n}-dars
              <span>{activeAlarm.subject}</span>
            </h2>
            <p>{activeAlarm.message}</p>
            <button type="button" className="btn-primary" onClick={() => setActiveAlarm(null)}>
              O‘chirish
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function Sheet({
  title,
  icon,
  onClose,
  children,
}: {
  title: string
  icon: string
  onClose: () => void
  children: ReactNode
}) {
  return (
    <div className="overlay sheet-overlay" onClick={onClose}>
      <div className="sheet-card sheet-panel" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-h">
          <div>
            <span className="sheet-ico">
              <Icon name={icon} size={26} />
            </span>
            <h2>{title}</h2>
          </div>
          <button type="button" className="icon-btn dark" onClick={onClose}>
            <Icon name="close" size={16} />
          </button>
        </div>
        <div className="sheet-body">{children}</div>
      </div>
    </div>
  )
}
