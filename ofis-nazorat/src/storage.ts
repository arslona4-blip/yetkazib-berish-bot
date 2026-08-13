import type { LogEvent, Person } from './types'

const PEOPLE_KEY = 'ofis_nazorat_people_v1'
const LOGS_KEY = 'ofis_nazorat_logs_v1'

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function writeJson(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value))
}

export function loadPeople(): Person[] {
  return readJson<Person[]>(PEOPLE_KEY, [])
}

export function savePeople(people: Person[]) {
  writeJson(PEOPLE_KEY, people)
}

export function loadLogs(): LogEvent[] {
  return readJson<LogEvent[]>(LOGS_KEY, [])
}

export function saveLogs(logs: LogEvent[]) {
  // oxirgi 2000 ta yetarli
  writeJson(LOGS_KEY, logs.slice(0, 2000))
}

export function uid(): string {
  return `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
}

export function todayKey(iso = new Date().toISOString()): string {
  return iso.slice(0, 10)
}

export function exportLogsCsv(logs: LogEvent[]): string {
  const rows = [['vaqt', 'ism', 'hodisa'], ...logs.map((l) => [l.at, l.name, l.type])]
  return rows
    .map((r) => r.map((c) => `"${String(c).replaceAll('"', '""')}"`).join(','))
    .join('\n')
}
