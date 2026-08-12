export const DAYS = [
  { id: 'dush', short: 'Dush', full: 'Dushanba', shortRu: 'Пн', fullRu: 'Понедельник' },
  { id: 'sesh', short: 'Sesh', full: 'Seshanba', shortRu: 'Вт', fullRu: 'Вторник' },
  { id: 'chor', short: 'Chor', full: 'Chorshanba', shortRu: 'Ср', fullRu: 'Среда' },
  { id: 'pay', short: 'Pay', full: 'Payshanba', shortRu: 'Чт', fullRu: 'Четверг' },
  { id: 'jum', short: 'Jum', full: 'Juma', shortRu: 'Пт', fullRu: 'Пятница' },
  { id: 'shan', short: 'Shan', full: 'Shanba', shortRu: 'Сб', fullRu: 'Суббота' },
] as const

export type DayId = (typeof DAYS)[number]['id']

export type Period = { n: number; start: string; end: string }

export type Cell = {
  subject: string
  teacher: string
  room: string
  note: string
  homework: string
  homeworkDone: boolean
}

export type EventItem = {
  id: string
  date: string
  title: string
  type: 'exam' | 'holiday' | 'other'
}

export type GradeItem = {
  id: string
  subject: string
  score: number
  date: string
  note: string
}

export type ClubItem = {
  id: string
  title: string
  day: DayId
  time: string
}

export type CheckItem = { id: string; text: string; done: boolean }
export type Announcement = { id: string; text: string; at: string }

export type Profile = {
  id: string
  className: string
  schoolName: string
  periods: Period[]
  cells: Record<string, Cell>
  /** YYYY-MM-DD -> periodN -> override subject/teacher/room */
  substitutions: Record<string, Record<string, Partial<Cell>>>
  events: EventItem[]
  grades: GradeItem[]
  attendance: Record<string, 'present' | 'absent' | 'late'>
  checklist: CheckItem[]
  announcements: Announcement[]
  clubs: ClubItem[]
  subjectColors: Record<string, string>
  favorites: string[]
  commuteMinutes: number
  alarmMessage: string
}

export type AlarmSettings = {
  enabled: boolean
  minutesBefore: number
  sound: boolean
  vibrate: boolean
}

export type AppSettings = {
  activeProfileId: string
  profiles: Profile[]
  theme: 'light' | 'dark'
  lang: 'uz' | 'ru'
  parentMode: boolean
  pin: string
  alarm: AlarmSettings
  streak: { count: number; lastDate: string }
  weatherCity: string
}

export const DEFAULT_PERIODS: Period[] = [
  { n: 1, start: '08:00', end: '08:45' },
  { n: 2, start: '08:55', end: '09:40' },
  { n: 3, start: '09:50', end: '10:35' },
  { n: 4, start: '10:55', end: '11:40' },
  { n: 5, start: '11:50', end: '12:35' },
  { n: 6, start: '12:45', end: '13:30' },
  { n: 7, start: '13:40', end: '14:25' },
  { n: 8, start: '14:35', end: '15:20' },
  { n: 9, start: '15:30', end: '16:15' },
]

export const SUBJECT_SUGGESTIONS = [
  'Ona tili',
  'Adabiyot',
  'Matematika',
  'Algebra',
  'Geometriya',
  'Ingliz tili',
  'Rus tili',
  'Tarix',
  'Fizika',
  'Kimyo',
  'Biologiya',
  'Geografiya',
  'Informatika',
  'Jismoniy tarbiya',
  'Tarbiya',
  'Chizmachilik',
  'Musiqa',
  'Texnologiya',
]

export const SUBJECT_COLOR_PALETTE = [
  '#0f766e',
  '#0369a1',
  '#7c3aed',
  '#c2410c',
  '#be123c',
  '#15803d',
  '#a16207',
  '#4338ca',
]

export function emptyCell(): Cell {
  return {
    subject: '',
    teacher: '',
    room: '',
    note: '',
    homework: '',
    homeworkDone: false,
  }
}

export function cellKey(day: DayId, period: number): string {
  return `${day}-${period}`
}

export function emptyCells(periods: Period[]): Record<string, Cell> {
  const out: Record<string, Cell> = {}
  for (const day of DAYS) {
    for (const p of periods) out[cellKey(day.id, p.n)] = emptyCell()
  }
  return out
}

export function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
}

export function createProfile(partial?: Partial<Profile>): Profile {
  const periods = partial?.periods ?? DEFAULT_PERIODS.map((p) => ({ ...p }))
  return {
    id: partial?.id ?? uid(),
    className: partial?.className ?? '9-A',
    schoolName: partial?.schoolName ?? 'Ixtisoslashtirilgan maktab',
    periods,
    cells: partial?.cells ?? emptyCells(periods),
    substitutions: partial?.substitutions ?? {},
    events: partial?.events ?? [],
    grades: partial?.grades ?? [],
    attendance: partial?.attendance ?? {},
    checklist: partial?.checklist ?? [
      { id: uid(), text: 'Daftarlar', done: false },
      { id: uid(), text: 'Forma', done: false },
      { id: uid(), text: 'Nonushta', done: false },
    ],
    announcements: partial?.announcements ?? [],
    clubs: partial?.clubs ?? [],
    subjectColors: partial?.subjectColors ?? {},
    favorites: partial?.favorites ?? [],
    commuteMinutes: partial?.commuteMinutes ?? 20,
    alarmMessage: partial?.alarmMessage ?? 'Darsga tayyorlaning!',
  }
}

export function defaultSettings(): AppSettings {
  const p = createProfile()
  return {
    activeProfileId: p.id,
    profiles: [p],
    theme: 'light',
    lang: 'uz',
    parentMode: false,
    pin: '',
    alarm: { enabled: true, minutesBefore: 5, sound: true, vibrate: true },
    streak: { count: 0, lastDate: '' },
    weatherCity: 'Tashkent',
  }
}

export function todayDayId(d = new Date()): DayId | null {
  const map: (DayId | null)[] = [null, 'dush', 'sesh', 'chor', 'pay', 'jum', 'shan']
  return map[d.getDay()]
}

export function parseClock(hhmm: string, now = new Date()): Date {
  const [h, m] = hhmm.split(':').map(Number)
  const d = new Date(now)
  d.setHours(h, m, 0, 0)
  return d
}

export function currentPeriod(periods: Period[], now = new Date()): Period | null {
  const t = now.getTime()
  for (const p of periods) {
    const a = parseClock(p.start, now).getTime()
    const b = parseClock(p.end, now).getTime()
    if (t >= a && t < b) return p
  }
  return null
}

export function isoDate(d = new Date()): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function getEffectiveCell(
  profile: Profile,
  day: DayId,
  period: number,
  dateISO = isoDate(),
): Cell {
  const base = profile.cells[cellKey(day, period)] ?? emptyCell()
  const sub = profile.substitutions[dateISO]?.[String(period)]
  if (!sub) return { ...base }
  return { ...base, ...sub, subject: sub.subject?.trim() ? sub.subject : base.subject }
}
