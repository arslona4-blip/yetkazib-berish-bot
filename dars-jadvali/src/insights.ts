import {
  DAYS,
  getEffectiveCell,
  isoDate,
  parseClock,
  todayDayId,
  type AppSettings,
  type DayId,
  type EventItem,
  type Period,
  type Profile,
} from './model'

export type Lang = 'uz' | 'ru'
export const L = (lang: Lang, uz: string, ru: string) => (lang === 'ru' ? ru : uz)

export function dayInfo(id: DayId) {
  return DAYS.find((d) => d.id === id)!
}

export function subjectsOn(profile: Profile, day: DayId, dateISO: string) {
  const out: { period: Period; subject: string; homework: string }[] = []
  for (const p of profile.periods) {
    const c = getEffectiveCell(profile, day, p.n, dateISO)
    const subject = c.subject.trim()
    if (subject) out.push({ period: p, subject, homework: c.homework.trim() })
  }
  return out
}

/** Ertangi (yoki keyingi) o'qish kuni — yakshanbani o'tkazib yuboradi */
export function nextSchoolDay(profile: Profile, now = new Date()) {
  for (let i = 1; i <= 7; i++) {
    const d = new Date(now)
    d.setDate(d.getDate() + i)
    const id = todayDayId(d)
    if (!id) continue
    const iso = isoDate(d)
    const lessons = subjectsOn(profile, id, iso)
    if (lessons.length) return { date: d, iso, day: id, lessons }
  }
  return null
}

export function tomorrowBag(profile: Profile, now = new Date()) {
  const next = nextSchoolDay(profile, now)
  if (!next) return null
  const subjects = [...new Set(next.lessons.map((l) => l.subject))]
  const items: { subject: string; item: string }[] = []
  for (const s of subjects) {
    const list = profile.bagItems[s]
    if (list?.length) for (const item of list) items.push({ subject: s, item })
    else items.push({ subject: s, item: `${s}: daftar, kitob` })
  }
  return { ...next, subjects, items, packed: profile.bagPacked[next.iso] ?? [] }
}

/** O'zbekiston maktablari: 1-chorak sen–okt, 2-chorak noy–dek, 3-chorak yan–mar, 4-chorak apr–may */
export function quarterOf(d: Date): number {
  const m = d.getMonth() + 1
  if (m === 9 || m === 10) return 1
  if (m === 11 || m === 12) return 2
  if (m >= 1 && m <= 3) return 3
  return 4
}

export function gradeSummary(profile: Profile, quarter?: number, now = new Date()) {
  const q = quarter ?? quarterOf(now)
  const year = now.getFullYear()
  const schoolYearStart = now.getMonth() + 1 >= 9 ? year : year - 1
  const inQuarter = profile.grades.filter((g) => {
    const d = new Date(g.date)
    if (Number.isNaN(d.getTime())) return false
    const sy = d.getMonth() + 1 >= 9 ? d.getFullYear() : d.getFullYear() - 1
    return sy === schoolYearStart && quarterOf(d) === q
  })
  const by = new Map<string, number[]>()
  for (const g of inQuarter) {
    const k = g.subject.trim() || '—'
    by.set(k, [...(by.get(k) ?? []), g.score])
  }
  const subjects = [...by.entries()]
    .map(([subject, scores]) => ({
      subject,
      count: scores.length,
      avg: scores.reduce((a, b) => a + b, 0) / scores.length,
    }))
    .sort((a, b) => a.avg - b.avg)
  const all = inQuarter.map((g) => g.score)
  const overall = all.length ? all.reduce((a, b) => a + b, 0) / all.length : null
  const weakest = subjects.find((s) => s.avg < 4) ?? null
  return { quarter: q, subjects, overall, weakest, count: all.length }
}

export function daysUntil(dateISO: string, now = new Date()) {
  const a = new Date(isoDate(now) + 'T00:00:00')
  const b = new Date(dateISO + 'T00:00:00')
  return Math.round((b.getTime() - a.getTime()) / 86_400_000)
}

export function upcomingExams(profile: Profile, now = new Date()) {
  return profile.events
    .filter((e) => e.type === 'exam')
    .map((e) => ({ ...e, daysLeft: daysUntil(e.date, now) }))
    .filter((e) => e.daysLeft >= 0)
    .sort((a, b) => a.daysLeft - b.daysLeft)
}

export function upcomingEvents(profile: Profile, now = new Date()): (EventItem & { daysLeft: number })[] {
  return profile.events
    .map((e) => ({ ...e, daysLeft: daysUntil(e.date, now) }))
    .filter((e) => e.daysLeft >= 0)
    .sort((a, b) => a.daysLeft - b.daysLeft)
}

export type LessonState =
  | { kind: 'lesson'; period: Period; subject: string; endsAt: Date }
  | { kind: 'break'; next: Period; subject: string; startsAt: Date }
  | { kind: 'before'; next: Period; subject: string; startsAt: Date }
  | { kind: 'after' }
  | { kind: 'off' }

export function lessonState(profile: Profile, now = new Date()): LessonState {
  const day = todayDayId(now)
  if (!day) return { kind: 'off' }
  const lessons = subjectsOn(profile, day, isoDate(now))
  if (!lessons.length) return { kind: 'off' }
  const t = now.getTime()
  for (let i = 0; i < lessons.length; i++) {
    const l = lessons[i]
    const a = parseClock(l.period.start, now)
    const b = parseClock(l.period.end, now)
    if (t >= a.getTime() && t < b.getTime())
      return { kind: 'lesson', period: l.period, subject: l.subject, endsAt: b }
    if (t < a.getTime())
      return {
        kind: i === 0 ? 'before' : 'break',
        next: l.period,
        subject: l.subject,
        startsAt: a,
      }
  }
  return { kind: 'after' }
}

export type Badge = { id: string; icon: string; titleUz: string; titleRu: string; got: boolean; hintUz: string; hintRu: string }

export function computeBadges(settings: AppSettings, profile: Profile): Badge[] {
  const streak = settings.streak.count
  const cells = Object.values(profile.cells)
  const filled = cells.filter((c) => c.subject.trim()).length
  const hw = cells.filter((c) => c.homework.trim())
  const fives = profile.grades.filter((g) => g.score >= 5).length
  const sum = gradeSummary(profile)
  const focusCount = profile.focusLog.length
  const focusMin = profile.focusLog.reduce((a, b) => a + b.minutes, 0)
  let presentRun = 0
  for (let i = 0; i < 14; i++) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    if (!todayDayId(d)) continue
    const v = profile.attendance[isoDate(d)]
    if (v === 'present' || v === 'late') presentRun++
    else if (i > 0) break
  }
  const b = (
    id: string,
    icon: string,
    titleUz: string,
    titleRu: string,
    got: boolean,
    hintUz: string,
    hintRu: string,
  ): Badge => ({ id, icon, titleUz, titleRu, got, hintUz, hintRu })
  return [
    b('s3', '🔥', '3 kun ketma-ket', '3 дня подряд', streak >= 3, 'Ilovani 3 kun ochish', 'Открыть 3 дня подряд'),
    b('s7', '⚡', 'Bir hafta', 'Неделя', streak >= 7, '7 kun ketma-ket', '7 дней подряд'),
    b('s30', '🏆', 'Bir oy', 'Месяц', streak >= 30, '30 kun ketma-ket', '30 дней подряд'),
    b('table', '🗓️', 'Jadval ustasi', 'Мастер расписания', filled >= 20, '20 ta dars kiriting', 'Заполните 20 уроков'),
    b('hw', '✅', 'Hammasi bajarildi', 'Всё сделано', hw.length > 0 && hw.every((c) => c.homeworkDone), 'Barcha vazifalarni bajaring', 'Выполните все задания'),
    b('five', '⭐', 'Birinchi 5', 'Первая пятёрка', fives >= 1, '5 baho oling', 'Получите 5'),
    b('fives10', '🌟', '10 ta besh', '10 пятёрок', fives >= 10, '10 ta 5 baho', '10 оценок «5»'),
    b('avg', '🎓', "A'lochi", 'Отличник', sum.overall !== null && sum.count >= 5 && sum.overall >= 4.5, "Chorak o'rtachasi 4.5+", 'Средний балл 4.5+'),
    b('focus1', '🎯', 'Diqqat', 'Фокус', focusCount >= 1, '1 ta fokus seans', '1 фокус-сессия'),
    b('focus10', '🧠', 'Chuqur fokus', 'Глубокий фокус', focusMin >= 250, '250 daqiqa fokus', '250 минут фокуса'),
    b('attend', '🏫', 'Darsga qatnashdi', 'Посещаемость', presentRun >= 5, '5 kun ketma-ket darsda', '5 дней без пропусков'),
  ]
}

/** Ketma-ket qoldirilgan o'qish kunlari (bugundan orqaga) */
export function absentRun(profile: Profile, now = new Date()) {
  let run = 0
  for (let i = 0; i < 30; i++) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    if (!todayDayId(d)) continue
    const v = profile.attendance[isoDate(d)]
    if (v === 'absent') run++
    else if (v || i > 0) break
  }
  return run
}

const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/[ʻʼ’‘`']/g, "'")
    .replace(/\s+/g, ' ')
    .trim()

const has = (q: string, words: string[]) => words.some((w) => q.includes(w))

/** Ovozli savolga javob; tushunmasa null qaytaradi */
export function answerQuestion(text: string, profile: Profile, lang: Lang, now = new Date()): string | null {
  const q = norm(text)
  const tomorrow = has(q, ['ertaga', 'завтра'])

  if (has(q, ['imtihon', 'nazorat', 'экзамен', 'контрольн'])) {
    const ex = upcomingExams(profile, now)[0]
    if (!ex) return L(lang, "Yaqin imtihon yo'q", 'Ближайших экзаменов нет')
    if (ex.daysLeft === 0) return L(lang, `Bugun imtihon: ${ex.title}`, `Сегодня экзамен: ${ex.title}`)
    return L(lang, `${ex.title} — ${ex.daysLeft} kundan keyin`, `${ex.title} — через ${ex.daysLeft} дн.`)
  }

  if (has(q, ['sumka', 'olib bor', 'nima olib', 'портфел', 'взять', 'собрать'])) {
    const bag = tomorrowBag(profile, now)
    if (!bag) return L(lang, "Keyingi darslar topilmadi", 'Следующие уроки не найдены')
    return L(lang, `Sumkaga: ${bag.items.map((i) => i.item).join(', ')}`, `В портфель: ${bag.items.map((i) => i.item).join(', ')}`)
  }

  if (has(q, ['vazifa', 'uy ish', 'задани', 'домашн', 'дз'])) {
    const subj = profile.periods.length
      ? [...new Set(Object.values(profile.cells).map((c) => c.subject.trim()).filter(Boolean))].find((s) =>
          q.includes(norm(s).slice(0, Math.max(4, norm(s).length - 2))),
        )
      : undefined
    const list = Object.values(profile.cells).filter(
      (c) => c.homework.trim() && !c.homeworkDone && (!subj || c.subject.trim() === subj),
    )
    if (!list.length) return L(lang, "Bajarilmagan vazifa yo'q", 'Невыполненных заданий нет')
    return list
      .slice(0, 4)
      .map((c) => `${c.subject}: ${c.homework}`)
      .join('. ')
  }

  if (has(q, ['nechta dars', 'necha dars', 'сколько урок'])) {
    if (tomorrow) {
      const n = nextSchoolDay(profile, now)
      return n
        ? L(lang, `${dayInfo(n.day).full} kuni ${n.lessons.length} ta dars`, `В ${dayInfo(n.day).fullRu.toLowerCase()} ${n.lessons.length} уроков`)
        : L(lang, "Dars yo'q", 'Уроков нет')
    }
    const day = todayDayId(now)
    const n = day ? subjectsOn(profile, day, isoDate(now)).length : 0
    return L(lang, `Bugun ${n} ta dars`, `Сегодня ${n} уроков`)
  }

  if (tomorrow) {
    const n = nextSchoolDay(profile, now)
    if (!n) return L(lang, "Keyingi darslar topilmadi", 'Следующие уроки не найдены')
    const names = n.lessons.map((l) => l.subject).join(', ')
    return L(lang, `${dayInfo(n.day).full}: ${names}`, `${dayInfo(n.day).fullRu}: ${names}`)
  }

  if (has(q, ['bugun', 'сегодня'])) {
    const day = todayDayId(now)
    const list = day ? subjectsOn(profile, day, isoDate(now)) : []
    if (!list.length) return L(lang, "Bugun dars yo'q", 'Сегодня уроков нет')
    return L(lang, 'Bugun: ', 'Сегодня: ') + list.map((l) => l.subject).join(', ')
  }

  if (has(q, ['baho', "o'rtacha", 'оценк', 'средн'])) {
    const s = gradeSummary(profile, undefined, now)
    if (s.overall === null) return L(lang, "Bu chorakda baho yo'q", 'В этой четверти оценок нет')
    const tail = s.weakest ? L(lang, `. E'tibor: ${s.weakest.subject}`, `. Внимание: ${s.weakest.subject}`) : ''
    return L(lang, `${s.quarter}-chorak o'rtacha: ${s.overall.toFixed(1)}`, `Средний за ${s.quarter} четверть: ${s.overall.toFixed(1)}`) + tail
  }

  return null
}
