export const DAYS = [
  { id: 'dush', short: 'Dush', full: 'Dushanba' },
  { id: 'sesh', short: 'Sesh', full: 'Seshanba' },
  { id: 'chor', short: 'Chor', full: 'Chorshanba' },
  { id: 'pay', short: 'Pay', full: 'Payshanba' },
  { id: 'jum', short: 'Jum', full: 'Juma' },
  { id: 'shan', short: 'Shan', full: 'Shanba' },
] as const

export type DayId = (typeof DAYS)[number]['id']

export type Period = {
  n: number
  start: string
  end: string
}

/** Ixtisoslashtirilgan maktab qo‘ng‘iroq jadvali — 9 dars */
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

export type CellKey = `${DayId}-${number}`

export type ScheduleState = {
  className: string
  schoolName: string
  subjects: Record<string, string>
}

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

/** JS getDay(): 0=Yak … 6=Shan → bizning DayId (Yakshanba yo‘q) */
export function todayDayId(d = new Date()): DayId | null {
  const map: (DayId | null)[] = [null, 'dush', 'sesh', 'chor', 'pay', 'jum', 'shan']
  return map[d.getDay()]
}

export function cellKey(day: DayId, period: number): CellKey {
  return `${day}-${period}`
}

export function emptySubjects(): Record<string, string> {
  const out: Record<string, string> = {}
  for (const day of DAYS) {
    for (const p of DEFAULT_PERIODS) {
      out[cellKey(day.id, p.n)] = ''
    }
  }
  return out
}

export function defaultState(): ScheduleState {
  return {
    className: '7-A',
    schoolName: 'Maktab',
    subjects: emptySubjects(),
  }
}
