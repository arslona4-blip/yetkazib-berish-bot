export type Lesson = {
  id: string
  num: number
  title: string
  topic: string
  date: string // YYYY-MM-DD
  time: string // HH:MM
  minutes: number
  tasks: number
  arduinoPath: string
}

/** 32-GR Online Robototexnika — haftalik onlayn darslar (Juma 20:51) */
export const GROUP = {
  name: '32-GR',
  course: 'Online Robototexnika',
  mode: 'Onlayn',
  weekday: 'Juma',
  time: '20:51',
  timezone: 'Toshkent',
}

export const LESSONS: Lesson[] = [
  {
    id: 'dars1',
    num: 1,
    title: 'Arduino, maket, LED',
    topic: 'Komponentlar bilan tanishish, LED yoqib-o‘chirish',
    date: '2026-05-15',
    time: '20:51',
    minutes: 45,
    tasks: 7,
    arduinoPath: '/arduino/',
  },
  {
    id: 'dars2',
    num: 2,
    title: 'Svetofor (3 LED)',
    topic: '3 ta LED ni svetofor tartibida boshqarish',
    date: '2026-05-22',
    time: '20:51',
    minutes: 35,
    tasks: 2,
    arduinoPath: '/arduino/',
  },
  {
    id: 'dars3',
    num: 3,
    title: 'PWM va analog pinlar',
    topic: 'Yorqinlikni analogWrite bilan boshqarish',
    date: '2026-05-29',
    time: '20:51',
    minutes: 50,
    tasks: 5,
    arduinoPath: '/arduino/',
  },
  {
    id: 'dars4',
    num: 4,
    title: 'Serial Monitor',
    topic: 'Monitor portda matn chiqarish',
    date: '2026-06-05',
    time: '20:51',
    minutes: 40,
    tasks: 12,
    arduinoPath: '/arduino/',
  },
  {
    id: 'dars5',
    num: 5,
    title: 'o‘zgaruvchilar (int)',
    topic: 'int tipi, qiymat o‘zgartirish, PWM bilan bog‘lash',
    date: '2026-06-12',
    time: '20:51',
    minutes: 45,
    tasks: 6,
    arduinoPath: '/arduino/',
  },
  {
    id: 'dars6',
    num: 6,
    title: 'if / else',
    topic: 'Shart operatori, hisoblagich, LED holatlari',
    date: '2026-06-19',
    time: '20:51',
    minutes: 55,
    tasks: 10,
    arduinoPath: '/arduino/',
  },
]

export function lessonStart(l: Lesson): Date {
  const [y, m, d] = l.date.split('-').map(Number)
  const [hh, mm] = l.time.split(':').map(Number)
  return new Date(y, m - 1, d, hh, mm, 0, 0)
}

export function formatUzDate(iso: string): string {
  const [y, m, d] = iso.split('-')
  return `${d}.${m}.${y}`
}

const WEEKDAYS = ['Yak', 'Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan']

export function weekdayShort(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return WEEKDAYS[new Date(y, m - 1, d).getDay()]
}

export function getNextLesson(now = new Date()): Lesson | null {
  for (const l of LESSONS) {
    if (lessonStart(l).getTime() >= now.getTime() - 60 * 60 * 1000) return l
  }
  return null
}
