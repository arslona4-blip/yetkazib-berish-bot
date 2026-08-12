import {
  DAYS,
  SUBJECT_COLOR_PALETTE,
  cellKey,
  createProfile,
  emptyCell,
  emptyCells,
  type DayId,
  type Period,
  type Profile,
} from './model'

export function colorForSubject(
  subject: string,
  map: Record<string, string>,
): string {
  if (!subject.trim()) return '#94a3b8'
  if (map[subject]) return map[subject]
  let h = 0
  for (let i = 0; i < subject.length; i++) h = (h * 31 + subject.charCodeAt(i)) >>> 0
  return SUBJECT_COLOR_PALETTE[h % SUBJECT_COLOR_PALETTE.length]
}

export function applyTemplate(name: 'empty' | 'sample7' | 'sample9'): Profile {
  if (name === 'empty') return createProfile({ className: '5-A', cells: emptyCells(createProfile().periods) })
  const p = createProfile({ className: name === 'sample9' ? '9-A' : '7-A' })
  const sample: Partial<Record<DayId, string[]>> = {
    dush: ['Matematika', 'Ona tili', 'Ingliz tili', 'Tarix', 'Fizika', 'Biologiya', 'Informatika', 'Tarbiya', 'Jismoniy tarbiya'],
    sesh: ['Algebra', 'Adabiyot', 'Kimyo', 'Geografiya', 'Rus tili', 'Fizika', 'Matematika', 'Musiqa', 'Texnologiya'],
    chor: ['Geometriya', 'Ingliz tili', 'Tarix', 'Ona tili', 'Informatika', 'Biologiya', 'Kimyo', 'Tarbiya', 'Jismoniy tarbiya'],
    pay: ['Matematika', 'Fizika', 'Adabiyot', 'Geografiya', 'Ingliz tili', 'Rus tili', 'Algebra', 'Chizmachilik', 'Texnologiya'],
    jum: ['Ona tili', 'Tarix', 'Kimyo', 'Biologiya', 'Informatika', 'Matematika', 'Ingliz tili', 'Tarbiya', 'Jismoniy tarbiya'],
    shan: ['Matematika', 'Fizika', 'Adabiyot', 'Geografiya', 'Ingliz tili', '', '', '', ''],
  }
  for (const day of DAYS) {
    const list = sample[day.id] || []
    for (let i = 0; i < p.periods.length; i++) {
      const subj = list[i] || ''
      if (name === 'sample7' && i >= 7) {
        p.cells[cellKey(day.id, p.periods[i].n)] = emptyCell()
        continue
      }
      p.cells[cellKey(day.id, p.periods[i].n)] = {
        ...emptyCell(),
        subject: subj,
        teacher: subj ? 'O‘qituvchi' : '',
        room: subj ? String(200 + i) : '',
      }
    }
  }
  return p
}

export function buildIcs(profile: Profile): string {
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Jadval//UZ//EN',
    'CALSCALE:GREGORIAN',
  ]
  const now = new Date()
  // next 8 weeks of lessons
  for (let w = 0; w < 8; w++) {
    for (const day of DAYS) {
      const jsDay = DAYS.findIndex((d) => d.id === day.id) + 1
      for (const p of profile.periods) {
        const cell = profile.cells[cellKey(day.id, p.n)]
        if (!cell?.subject.trim()) continue
        const start = nextWeekday(now, jsDay, w, p.start)
        const end = nextWeekday(now, jsDay, w, p.end)
        lines.push('BEGIN:VEVENT')
        lines.push(`UID:${day.id}-${p.n}-${w}@jadval`)
        lines.push(`DTSTAMP:${icsStamp(new Date())}`)
        lines.push(`DTSTART:${icsStamp(start)}`)
        lines.push(`DTEND:${icsStamp(end)}`)
        lines.push(`SUMMARY:${escapeIcs(cell.subject)}`)
        lines.push(
          `DESCRIPTION:${escapeIcs([cell.teacher, cell.room, cell.note].filter(Boolean).join(' · '))}`,
        )
        lines.push('END:VEVENT')
      }
    }
  }
  lines.push('END:VCALENDAR')
  return lines.join('\r\n')
}

function nextWeekday(from: Date, jsDay: number, weekOffset: number, hhmm: string): Date {
  const d = new Date(from)
  const diff = (jsDay - d.getDay() + 7) % 7
  d.setDate(d.getDate() + diff + weekOffset * 7)
  const [h, m] = hhmm.split(':').map(Number)
  d.setHours(h, m, 0, 0)
  return d
}

function icsStamp(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}T${pad(d.getHours())}${pad(d.getMinutes())}00`
}

function escapeIcs(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\n/g, '\\n')
}

export async function fetchWeather(city: string): Promise<{ temp: number; text: string } | null> {
  try {
    const geo = await fetch(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=uz&format=json`,
    ).then((r) => r.json())
    const loc = geo?.results?.[0]
    if (!loc) return null
    const w = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${loc.latitude}&longitude=${loc.longitude}&current=temperature_2m,weather_code`,
    ).then((r) => r.json())
    const code = w?.current?.weather_code ?? 0
    return {
      temp: Math.round(w?.current?.temperature_2m ?? 0),
      text: weatherText(code),
    }
  } catch {
    return null
  }
}

function weatherText(code: number): string {
  if (code === 0) return 'Ochiq'
  if (code <= 3) return 'Bulutli'
  if (code <= 67) return 'Yomg‘ir'
  if (code <= 77) return 'Qor'
  return 'Noma’lum'
}

const UZ_ORDINAL: Record<number, string> = {
  1: 'birinchi',
  2: 'ikkinchi',
  3: 'uchinchi',
  4: 'to‘rtinchi',
  5: 'beshinchi',
  6: 'oltinchi',
  7: 'yettinchi',
  8: 'sakkizinchi',
  9: 'to‘qqizinchi',
  10: 'o‘ninchi',
}

const RU_ORDINAL: Record<number, string> = {
  1: 'первый',
  2: 'второй',
  3: 'третий',
  4: 'четвёртый',
  5: 'пятый',
  6: 'шестой',
  7: 'седьмой',
  8: 'восьмой',
  9: 'девятый',
  10: 'десятый',
}

/** Raqam o‘rniga so‘z — TTS “dva” demasligi uchun */
export function periodOrdinal(n: number, lang: 'uz' | 'ru'): string {
  if (lang === 'ru') return RU_ORDINAL[n] || String(n)
  return UZ_ORDINAL[n] || `${n}-`
}

export function sayCurrentLesson(
  n: number,
  subject: string,
  lang: 'uz' | 'ru',
): string {
  const ord = periodOrdinal(n, lang)
  const fan = subject.trim() || (lang === 'ru' ? 'предмет не указан' : 'fan belgilanmagan')
  if (lang === 'ru') return `Сейчас ${ord} урок. Предмет: ${fan}.`
  return `Hozir ${ord} dars. Fan: ${fan}.`
}

export function sayNextLesson(
  n: number,
  subject: string,
  lang: 'uz' | 'ru',
): string {
  const ord = periodOrdinal(n, lang)
  const fan = subject.trim() || (lang === 'ru' ? 'предмет не указан' : 'fan belgilanmagan')
  if (lang === 'ru') return `Следующий — ${ord} урок. Предмет: ${fan}.`
  return `Keyingi dars — ${ord} dars. Fan: ${fan}.`
}

function pickVoice(lang: 'uz' | 'ru'): SpeechSynthesisVoice | null {
  if (!('speechSynthesis' in window)) return null
  const voices = window.speechSynthesis.getVoices()
  if (!voices.length) return null
  if (lang === 'ru') {
    return (
      voices.find((v) => v.lang.toLowerCase().startsWith('ru')) ||
      voices.find((v) => /russia|русский/i.test(v.name)) ||
      null
    )
  }
  // O‘zbek ovozi kam — turkcha fonetika yaqinroq; raqamlar allaqachon so‘z
  return (
    voices.find((v) => v.lang.toLowerCase().startsWith('uz')) ||
    voices.find((v) => v.lang.toLowerCase().startsWith('tr')) ||
    voices.find((v) => /uzbek|turkish|türk|o‘zbek|ozbek/i.test(v.name)) ||
    voices.find((v) => v.lang.toLowerCase().startsWith('en')) ||
    null
  )
}

export function speak(text: string, lang: 'uz' | 'ru') {
  if (!('speechSynthesis' in window)) return
  const run = () => {
    const u = new SpeechSynthesisUtterance(text)
    // Raqamsiz matn; tr-TR ba’zan uz-UZ dan yaxshiroq o‘qiydi
    u.lang = lang === 'ru' ? 'ru-RU' : 'tr-TR'
    const voice = pickVoice(lang)
    if (voice) {
      u.voice = voice
      u.lang = voice.lang || u.lang
    }
    u.rate = 0.92
    u.pitch = 1
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(u)
  }
  // ba’zi brauzerlarda ovozlar kech yuklanadi
  if (window.speechSynthesis.getVoices().length === 0) {
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.onvoiceschanged = null
      run()
    }
    // fallback
    window.setTimeout(run, 250)
  } else {
    run()
  }
}

export function listenOnce(lang: 'uz' | 'ru'): Promise<string> {
  return new Promise((resolve, reject) => {
    const w = window as unknown as {
      SpeechRecognition?: new () => {
        lang: string
        interimResults: boolean
        maxAlternatives: number
        start: () => void
        onresult: ((ev: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void) | null
        onerror: ((ev: Event) => void) | null
      }
      webkitSpeechRecognition?: new () => {
        lang: string
        interimResults: boolean
        maxAlternatives: number
        start: () => void
        onresult: ((ev: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void) | null
        onerror: ((ev: Event) => void) | null
      }
    }
    const SR = w.SpeechRecognition || w.webkitSpeechRecognition
    if (!SR) {
      reject(new Error('no-speech'))
      return
    }
    const rec = new SR()
    rec.lang = lang === 'ru' ? 'ru-RU' : 'uz-UZ'
    rec.interimResults = false
    rec.maxAlternatives = 1
    rec.onresult = (e) => resolve(e.results[0][0].transcript)
    rec.onerror = () => reject(new Error('err'))
    rec.start()
  })
}

export function shareText(title: string, text: string) {
  if (navigator.share) {
    void navigator.share({ title, text })
    return
  }
  void navigator.clipboard.writeText(text)
  alert('Nusxa olindi')
}

export function periodsProgress(
  periods: Period[],
  now = new Date(),
): { kind: 'lesson' | 'break' | 'idle'; n?: number; pct: number; label: string } {
  const t = now.getTime()
  for (let i = 0; i < periods.length; i++) {
    const p = periods[i]
    const a = parse(p.start, now)
    const b = parse(p.end, now)
    if (t >= a && t < b) {
      return {
        kind: 'lesson',
        n: p.n,
        pct: Math.round(((t - a) / (b - a)) * 100),
        label: `${p.n}-dars`,
      }
    }
    if (i < periods.length - 1) {
      const next = periods[i + 1]
      const c = parse(next.start, now)
      if (t >= b && t < c) {
        return {
          kind: 'break',
          n: p.n,
          pct: Math.round(((t - b) / (c - b)) * 100),
          label: 'Tanaffus',
        }
      }
    }
  }
  return { kind: 'idle', pct: 0, label: '' }
}

function parse(hhmm: string, now: Date) {
  const [h, m] = hhmm.split(':').map(Number)
  const d = new Date(now)
  d.setHours(h, m, 0, 0)
  return d.getTime()
}

export function weekStats(profile: Profile) {
  const count: Record<string, number> = {}
  let filled = 0
  let total = 0
  for (const day of DAYS) {
    for (const p of profile.periods) {
      total++
      const c = profile.cells[cellKey(day.id, p.n)]
      if (c?.subject.trim()) {
        filled++
        count[c.subject] = (count[c.subject] || 0) + 1
      }
    }
  }
  const top = Object.entries(count).sort((a, b) => b[1] - a[1]).slice(0, 5)
  return { filled, total, top }
}

export function encodeShare(profile: Profile): string {
  const slim = {
    className: profile.className,
    schoolName: profile.schoolName,
    periods: profile.periods,
    cells: profile.cells,
  }
  return btoa(unescape(encodeURIComponent(JSON.stringify(slim))))
}

export function decodeShare(raw: string): Partial<Profile> | null {
  try {
    return JSON.parse(decodeURIComponent(escape(atob(raw)))) as Partial<Profile>
  } catch {
    return null
  }
}
