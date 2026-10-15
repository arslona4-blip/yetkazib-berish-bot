import { useEffect, useRef, useState } from 'react'
import { isoDate, uid, type AppSettings, type EventItem, type Profile } from './model'
import {
  L,
  absentRun,
  computeBadges,
  dayInfo,
  gradeSummary,
  lessonState,
  tomorrowBag,
  upcomingEvents,
  upcomingExams,
  type Lang,
} from './insights'
import { formatCountdown, playAlarmSound, vibrateAlarm } from './alarm'
import { Icon } from './Icon'

type Patch = (fn: (p: Profile) => Profile) => void

/* —— Uyga vazifa rasmlari (IndexedDB) —— */

const DB = 'maktab-jadval-photos'
const STORE = 'photos'

function db(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(STORE)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function tx<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const d = await db()
  return new Promise((resolve, reject) => {
    const r = fn(d.transaction(STORE, mode).objectStore(STORE))
    r.onsuccess = () => resolve(r.result)
    r.onerror = () => reject(r.error)
  })
}

export const photoStore = {
  put: (key: string, blob: Blob) => tx('readwrite', (s) => s.put(blob, key)),
  get: (key: string) => tx<Blob | undefined>('readonly', (s) => s.get(key)),
  del: (key: string) => tx('readwrite', (s) => s.delete(key)),
}

async function shrink(file: File, max = 1024): Promise<Blob> {
  const img = await createImageBitmap(file)
  const k = Math.min(1, max / Math.max(img.width, img.height))
  const c = document.createElement('canvas')
  c.width = Math.round(img.width * k)
  c.height = Math.round(img.height * k)
  c.getContext('2d')!.drawImage(img, 0, 0, c.width, c.height)
  return new Promise((resolve) => c.toBlob((b) => resolve(b ?? file), 'image/jpeg', 0.7))
}

function usePhotoUrl(key?: string) {
  const [url, setUrl] = useState<string | null>(null)
  useEffect(() => {
    if (!key) {
      setUrl(null)
      return
    }
    let u: string | null = null
    let alive = true
    void photoStore.get(key).then((b) => {
      if (!alive || !b) return
      u = URL.createObjectURL(b)
      setUrl(u)
    })
    return () => {
      alive = false
      if (u) URL.revokeObjectURL(u)
    }
  }, [key])
  return url
}

export function PhotoThumb({ photoKey, size = 56 }: { photoKey?: string; size?: number }) {
  const url = usePhotoUrl(photoKey)
  const [big, setBig] = useState(false)
  if (!url) return null
  return (
    <>
      <img
        src={url}
        alt=""
        className="hw-thumb"
        style={{ width: size, height: size }}
        onClick={(e) => {
          e.preventDefault()
          setBig(true)
        }}
      />
      {big && (
        <div className="overlay photo-view" onClick={() => setBig(false)}>
          <img src={url} alt="" />
        </div>
      )}
    </>
  )
}

/** Tahrirlash oynasidagi rasm tanlash */
export function PhotoPicker({
  photoKey,
  onChange,
  lang,
}: {
  photoKey?: string
  onChange: (key: string | undefined) => void
  lang: Lang
}) {
  const ref = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  return (
    <div className="photo-pick">
      <PhotoThumb photoKey={photoKey} />
      <button type="button" className="btn-ghost" disabled={busy} onClick={() => ref.current?.click()}>
        <Icon name="camera" size={16} /> {photoKey ? L(lang, 'Rasmni almashtirish', 'Заменить фото') : L(lang, 'Vazifa rasmi', 'Фото задания')}
      </button>
      {photoKey && (
        <button type="button" className="btn-ghost" onClick={() => onChange(undefined)}>
          ✕
        </button>
      )}
      <input
        ref={ref}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        onChange={async (e) => {
          const f = e.target.files?.[0]
          e.target.value = ''
          if (!f) return
          setBusy(true)
          try {
            const key = `hw-${uid()}`
            await photoStore.put(key, await shrink(f))
            onChange(key)
          } catch {
            alert(L(lang, 'Rasmni saqlab bo‘lmadi', 'Не удалось сохранить фото'))
          } finally {
            setBusy(false)
          }
        }}
      />
    </div>
  )
}

/* —— Ertaga sumkaga —— */

export function BagSheet({ profile, lang, readOnly, patch }: { profile: Profile; lang: Lang; readOnly: boolean; patch: Patch }) {
  const bag = tomorrowBag(profile)
  const [editSubj, setEditSubj] = useState<string | null>(null)
  const [text, setText] = useState('')
  if (!bag) return <p className="muted">{L(lang, 'Keyingi darslar topilmadi. Avval jadvalni to‘ldiring.', 'Следующих уроков нет. Сначала заполните расписание.')}</p>
  const d = dayInfo(bag.day)
  const packedSet = new Set(bag.packed)
  const done = bag.items.filter((i) => packedSet.has(i.item)).length
  const toggle = (item: string, on: boolean) =>
    patch((p) => {
      const cur = new Set(p.bagPacked[bag.iso] ?? [])
      if (on) cur.add(item)
      else cur.delete(item)
      const keep = Object.fromEntries(Object.entries(p.bagPacked).filter(([k]) => k >= bag.iso))
      return { ...p, bagPacked: { ...keep, [bag.iso]: [...cur] } }
    })
  return (
    <div className="form-stack">
      <p className="muted">
        {L(lang, `${d.full}, ${bag.iso} · ${done}/${bag.items.length} tayyor`, `${d.fullRu}, ${bag.iso} · готово ${done}/${bag.items.length}`)}
      </p>
      <div className="mini-bar">
        <i style={{ width: `${bag.items.length ? (done / bag.items.length) * 100 : 0}%` }} />
      </div>
      {bag.items.map((i) => (
        <label key={i.subject + i.item} className="check-card">
          <input type="checkbox" checked={packedSet.has(i.item)} onChange={(e) => toggle(i.item, e.target.checked)} />
          <div>
            <strong>{i.item}</strong>
            <p>{i.subject}</p>
          </div>
        </label>
      ))}
      {!readOnly && (
        <>
          <h4 className="subh">{L(lang, 'Fanga nima kerak', 'Что нужно к предмету')}</h4>
          {bag.subjects.map((s) =>
            editSubj === s ? (
              <div key={s} className="form-stack">
                <label>
                  {s}
                  <input
                    autoFocus
                    value={text}
                    placeholder={L(lang, 'daftar, kitob, sirkul', 'тетрадь, учебник, циркуль')}
                    onChange={(e) => setText(e.target.value)}
                  />
                </label>
                <div className="row">
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => {
                      const list = text.split(',').map((x) => x.trim()).filter(Boolean)
                      patch((p) => ({ ...p, bagItems: { ...p.bagItems, [s]: list } }))
                      setEditSubj(null)
                    }}
                  >
                    OK
                  </button>
                  <button type="button" className="btn-ghost" onClick={() => setEditSubj(null)}>
                    ✕
                  </button>
                </div>
              </div>
            ) : (
              <button
                key={s}
                type="button"
                className="btn-ghost bag-subj"
                onClick={() => {
                  setText((profile.bagItems[s] ?? []).join(', '))
                  setEditSubj(s)
                }}
              >
                <strong>{s}</strong>
                <span>{(profile.bagItems[s] ?? []).join(', ') || L(lang, 'belgilanmagan', 'не задано')}</span>
              </button>
            ),
          )}
        </>
      )}
    </div>
  )
}

/* —— Baholar: chorak o'rtachasi —— */

export function GradesInsight({ profile, lang }: { profile: Profile; lang: Lang }) {
  const s = gradeSummary(profile)
  if (s.overall === null)
    return <p className="muted">{L(lang, `${s.quarter}-chorakda hali baho yo‘q`, `В ${s.quarter} четверти пока нет оценок`)}</p>
  return (
    <div className="grade-box">
      <div className="grade-head">
        <div>
          <span>{L(lang, `${s.quarter}-chorak o‘rtacha`, `Средний за ${s.quarter} четв.`)}</span>
          <b>{s.overall.toFixed(2)}</b>
        </div>
        {s.weakest && (
          <div className="warn">
            <span>{L(lang, 'E’tibor kerak', 'Требует внимания')}</span>
            <b>
              {s.weakest.subject} · {s.weakest.avg.toFixed(1)}
            </b>
          </div>
        )}
      </div>
      {s.subjects.map((x) => (
        <div key={x.subject} className="grade-bar">
          <span>{x.subject}</span>
          <div className="mini-bar">
            <i style={{ width: `${(x.avg / 5) * 100}%`, background: x.avg < 4 ? 'var(--rose)' : undefined }} />
          </div>
          <b>{x.avg.toFixed(1)}</b>
        </div>
      ))}
    </div>
  )
}

export function GradeAdder({ subjects, lang, onAdd }: { subjects: string[]; lang: Lang; onAdd: (subject: string, score: number) => void }) {
  const [subject, setSubject] = useState(subjects[0] ?? '')
  return (
    <div className="form-stack">
      <label>
        {L(lang, 'Fan', 'Предмет')}
        <input list="subjects" value={subject} onChange={(e) => setSubject(e.target.value)} />
      </label>
      <div className="seg big five">
        {[5, 4, 3, 2].map((n) => (
          <button key={n} type="button" disabled={!subject.trim()} onClick={() => onAdd(subject.trim(), n)}>
            {n}
          </button>
        ))}
      </div>
    </div>
  )
}

/* —— Imtihon va sanalar —— */

export function EventsEditor({ profile, lang, readOnly, patch }: { profile: Profile; lang: Lang; readOnly: boolean; patch: Patch }) {
  const [title, setTitle] = useState('')
  const [date, setDate] = useState('')
  const [type, setType] = useState<EventItem['type']>('exam')
  const list = upcomingEvents(profile)
  const past = profile.events.filter((e) => !list.some((x) => x.id === e.id))
  const typeName = (t: EventItem['type']) =>
    t === 'exam' ? L(lang, 'Imtihon', 'Экзамен') : t === 'holiday' ? L(lang, 'Bayram', 'Праздник') : L(lang, 'Boshqa', 'Другое')
  return (
    <div className="form-stack">
      {list.length === 0 && <p className="muted">{L(lang, 'Yaqin sanalar yo‘q', 'Ближайших дат нет')}</p>}
      {list.map((e) => (
        <div key={e.id} className="event-row">
          <span className={`days-left ${e.type}`}>
            {e.daysLeft === 0 ? L(lang, 'Bugun', 'Сегодня') : e.daysLeft}
            {e.daysLeft > 0 && <small>{L(lang, 'kun', 'дн')}</small>}
          </span>
          <div>
            <strong>{e.title}</strong>
            <p>
              {typeName(e.type)} · {e.date}
            </p>
          </div>
          {!readOnly && (
            <button type="button" className="icon-btn dark" aria-label="delete" onClick={() => patch((p) => ({ ...p, events: p.events.filter((x) => x.id !== e.id) }))}>
              <Icon name="close" size={14} />
            </button>
          )}
        </div>
      ))}
      {past.length > 0 && !readOnly && (
        <button type="button" className="btn-ghost" onClick={() => patch((p) => ({ ...p, events: p.events.filter((x) => list.some((l) => l.id === x.id)) }))}>
          {L(lang, `O‘tgan ${past.length} ta sanani tozalash`, `Удалить прошедшие (${past.length})`)}
        </button>
      )}
      {!readOnly && (
        <>
          <h4 className="subh">{L(lang, 'Yangi sana', 'Новая дата')}</h4>
          <label>
            {L(lang, 'Nomi', 'Название')}
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={L(lang, 'Matematika nazorat ishi', 'Контрольная по математике')} />
          </label>
          <label>
            {L(lang, 'Sana', 'Дата')}
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>
          <div className="seg big">
            {(['exam', 'holiday', 'other'] as const).map((t) => (
              <button key={t} type="button" className={type === t ? 'on' : ''} onClick={() => setType(t)}>
                {typeName(t)}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn-primary"
            disabled={!title.trim() || !date}
            onClick={() => {
              patch((p) => ({ ...p, events: [...p.events, { id: uid(), title: title.trim(), date, type }] }))
              setTitle('')
              setDate('')
            }}
          >
            + {L(lang, 'Qo‘shish', 'Добавить')}
          </button>
        </>
      )}
    </div>
  )
}

export function examWidgetText(profile: Profile, lang: Lang) {
  const ex = upcomingExams(profile)[0]
  if (!ex) return L(lang, 'Yaqin imtihon yo‘q', 'Экзаменов нет')
  if (ex.daysLeft === 0) return L(lang, `Bugun: ${ex.title}`, `Сегодня: ${ex.title}`)
  return L(lang, `${ex.daysLeft} kun · ${ex.title}`, `${ex.daysLeft} дн · ${ex.title}`)
}

/* —— Fokus taymer (Pomodoro) —— */

type FocusState = { mode: 'idle' | 'work' | 'break'; endsAt: number; minutes: number; pausedLeft: number | null }
const FOCUS_KEY = 'maktab-jadval-focus-v1'
const idle: FocusState = { mode: 'idle', endsAt: 0, minutes: 25, pausedLeft: null }

function loadFocus(): FocusState {
  try {
    return { ...idle, ...(JSON.parse(localStorage.getItem(FOCUS_KEY) || '{}') as Partial<FocusState>) }
  } catch {
    return idle
  }
}

export function useFocus(now: Date, onWorkDone: (minutes: number) => void, sound: boolean) {
  const [st, setSt] = useState<FocusState>(loadFocus)
  const done = useRef(onWorkDone)
  done.current = onWorkDone

  useEffect(() => {
    localStorage.setItem(FOCUS_KEY, JSON.stringify(st))
  }, [st])

  useEffect(() => {
    if (st.mode === 'idle' || st.pausedLeft !== null || now.getTime() < st.endsAt) return
    if (sound) void playAlarmSound(3)
    vibrateAlarm()
    if (st.mode === 'work') {
      done.current(st.minutes)
      setSt({ ...st, mode: 'break', endsAt: Date.now() + 5 * 60_000 })
    } else setSt({ ...idle, minutes: st.minutes })
  }, [now, st, sound])

  const left = st.mode === 'idle' ? st.minutes * 60_000 : (st.pausedLeft ?? Math.max(0, st.endsAt - now.getTime()))
  return {
    ...st,
    left,
    start: (minutes = st.minutes) => setSt({ mode: 'work', minutes, endsAt: Date.now() + minutes * 60_000, pausedLeft: null }),
    pause: () => setSt((s) => ({ ...s, pausedLeft: Math.max(0, s.endsAt - Date.now()) })),
    resume: () => setSt((s) => ({ ...s, endsAt: Date.now() + (s.pausedLeft ?? 0), pausedLeft: null })),
    stop: () => setSt((s) => ({ ...idle, minutes: s.minutes })),
    setMinutes: (minutes: number) => setSt((s) => (s.mode === 'idle' ? { ...s, minutes } : s)),
  }
}

export type Focus = ReturnType<typeof useFocus>

export function FocusSheet({ focus, profile, lang }: { focus: Focus; profile: Profile; lang: Lang }) {
  const total = (focus.mode === 'break' ? 5 : focus.minutes) * 60_000
  const pct = focus.mode === 'idle' ? 0 : 100 - (focus.left / total) * 100
  const todayISO = isoDate()
  const today = profile.focusLog.filter((f) => f.date === todayISO)
  const todayMin = today.reduce((a, b) => a + b.minutes, 0)
  return (
    <div className="form-stack center-text">
      <div className="focus-ring" style={{ ['--p' as string]: `${pct}%` }}>
        <div>
          <b>{formatCountdown(focus.left)}</b>
          <span>
            {focus.mode === 'work'
              ? L(lang, 'Diqqat', 'Фокус')
              : focus.mode === 'break'
                ? L(lang, 'Dam olish', 'Перерыв')
                : L(lang, 'Tayyor', 'Готов')}
          </span>
        </div>
      </div>
      {focus.mode === 'idle' ? (
        <>
          <div className="seg big">
            {[15, 25, 45].map((m) => (
              <button key={m} type="button" className={focus.minutes === m ? 'on' : ''} onClick={() => focus.setMinutes(m)}>
                {m} {L(lang, 'daq', 'мин')}
              </button>
            ))}
          </div>
          <button type="button" className="btn-primary" onClick={() => focus.start()}>
            ▶ {L(lang, 'Boshlash', 'Старт')}
          </button>
        </>
      ) : (
        <div className="row">
          {focus.pausedLeft === null ? (
            <button type="button" className="btn-primary" style={{ flex: 1 }} onClick={focus.pause}>
              ❚❚ {L(lang, 'Pauza', 'Пауза')}
            </button>
          ) : (
            <button type="button" className="btn-primary" style={{ flex: 1 }} onClick={focus.resume}>
              ▶ {L(lang, 'Davom', 'Продолжить')}
            </button>
          )}
          <button type="button" className="btn-ghost" onClick={focus.stop}>
            ■ {L(lang, 'To‘xtatish', 'Стоп')}
          </button>
        </div>
      )}
      <p className="muted">
        {L(lang, `Bugun: ${today.length} seans · ${todayMin} daqiqa. Jami: ${profile.focusLog.length} seans`, `Сегодня: ${today.length} сесс. · ${todayMin} мин. Всего: ${profile.focusLog.length}`)}
      </p>
    </div>
  )
}

/* —— Dars / tanaffus banneri —— */

export function LessonBanner({ profile, now, lang }: { profile: Profile; now: Date; lang: Lang }) {
  const s = lessonState(profile, now)
  if (s.kind === 'lesson')
    return (
      <div className="lesson-banner on">
        <span>🔕</span>
        <div>
          <strong>{L(lang, `Darsda: ${s.period.n}. ${s.subject}`, `Идёт урок: ${s.period.n}. ${s.subject}`)}</strong>
          <p>{L(lang, `Telefonni jim rejimga qo‘ying · ${formatCountdown(s.endsAt.getTime() - now.getTime())} qoldi`, `Включите беззвучный режим · осталось ${formatCountdown(s.endsAt.getTime() - now.getTime())}`)}</p>
        </div>
      </div>
    )
  if (s.kind === 'break')
    return (
      <div className="lesson-banner brk">
        <span>☕</span>
        <div>
          <strong>{L(lang, 'Tanaffus', 'Перемена')}</strong>
          <p>{L(lang, `Keyingi: ${s.next.n}. ${s.subject} · ${formatCountdown(s.startsAt.getTime() - now.getTime())}`, `Далее: ${s.next.n}. ${s.subject} · ${formatCountdown(s.startsAt.getTime() - now.getTime())}`)}</p>
        </div>
      </div>
    )
  return null
}

/* —— Ota-ona: bolam hozir qayerda —— */

export function ParentNowCard({ profile, now, lang }: { profile: Profile; now: Date; lang: Lang }) {
  const s = lessonState(profile, now)
  const absent = absentRun(profile, now)
  const exam = upcomingExams(profile, now).find((e) => e.daysLeft <= 7)
  let title: string
  let sub = ''
  if (s.kind === 'lesson') {
    title = L(lang, `Hozir ${s.period.n}-dars: ${s.subject}`, `Сейчас ${s.period.n}-й урок: ${s.subject}`)
    sub = L(lang, `${s.period.start}–${s.period.end}`, `${s.period.start}–${s.period.end}`)
  } else if (s.kind === 'break') {
    title = L(lang, 'Hozir tanaffus', 'Сейчас перемена')
    sub = L(lang, `Keyingi: ${s.subject} (${s.next.start})`, `Далее: ${s.subject} (${s.next.start})`)
  } else if (s.kind === 'before') {
    title = L(lang, 'Darslar hali boshlanmagan', 'Уроки ещё не начались')
    sub = L(lang, `1-dars: ${s.subject} · ${s.next.start}`, `Первый урок: ${s.subject} · ${s.next.start}`)
  } else if (s.kind === 'after') {
    title = L(lang, 'Bugungi darslar tugadi', 'Уроки на сегодня закончились')
  } else {
    title = L(lang, 'Bugun dars yo‘q', 'Сегодня уроков нет')
  }
  return (
    <section className="parent-card">
      <span className="kicker">{L(lang, 'Ota-ona uchun', 'Для родителей')}</span>
      <strong>{title}</strong>
      {sub && <p>{sub}</p>}
      {exam && (
        <p className="pc-alert">
          📝 {exam.daysLeft === 0 ? L(lang, `Bugun imtihon: ${exam.title}`, `Сегодня экзамен: ${exam.title}`) : L(lang, `${exam.daysLeft} kundan keyin imtihon: ${exam.title}`, `Через ${exam.daysLeft} дн. экзамен: ${exam.title}`)}
        </p>
      )}
      {absent >= 3 && (
        <p className="pc-alert danger">
          ⚠️ {L(lang, `${absent} kun ketma-ket darsga kelmagan`, `${absent} дня подряд пропуски`)}
        </p>
      )}
    </section>
  )
}

/* —— Yutuqlar —— */

export function BadgesSheet({ settings, profile, lang }: { settings: AppSettings; profile: Profile; lang: Lang }) {
  const list = computeBadges(settings, profile)
  const got = list.filter((b) => b.got).length
  return (
    <div className="form-stack">
      <p className="muted center-text">
        {L(lang, `${got}/${list.length} ta nishon olindi`, `Получено ${got}/${list.length}`)}
      </p>
      <div className="badge-grid">
        {list.map((b) => (
          <div key={b.id} className={`badge-item ${b.got ? 'got' : ''}`}>
            <span>{b.icon}</span>
            <strong>{L(lang, b.titleUz, b.titleRu)}</strong>
            <small>{L(lang, b.hintUz, b.hintRu)}</small>
          </div>
        ))}
      </div>
    </div>
  )
}

export function badgeCount(settings: AppSettings, profile: Profile) {
  return computeBadges(settings, profile).filter((b) => b.got).length
}
