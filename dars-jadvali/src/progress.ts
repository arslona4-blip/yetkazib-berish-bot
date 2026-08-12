import { defaultState, type ScheduleState } from './schedule'
import { DEFAULT_ALARM, type AlarmSettings } from './alarm'

const KEY = 'maktab-dars-jadvali-v1'
const ALARM_KEY = 'maktab-dars-jadvali-alarm-v1'
const FIRED_KEY = 'maktab-dars-jadvali-fired-v1'

export function loadSchedule(): ScheduleState {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return defaultState()
    const parsed = JSON.parse(raw) as Partial<ScheduleState>
    const base = defaultState()
    return {
      className: typeof parsed.className === 'string' ? parsed.className : base.className,
      schoolName: typeof parsed.schoolName === 'string' ? parsed.schoolName : base.schoolName,
      subjects: { ...base.subjects, ...(parsed.subjects || {}) },
    }
  } catch {
    return defaultState()
  }
}

export function saveSchedule(state: ScheduleState) {
  localStorage.setItem(KEY, JSON.stringify(state))
}

export function loadAlarmSettings(): AlarmSettings {
  try {
    const raw = localStorage.getItem(ALARM_KEY)
    if (!raw) return { ...DEFAULT_ALARM }
    const p = JSON.parse(raw) as Partial<AlarmSettings>
    return {
      enabled: typeof p.enabled === 'boolean' ? p.enabled : DEFAULT_ALARM.enabled,
      minutesBefore:
        typeof p.minutesBefore === 'number' ? p.minutesBefore : DEFAULT_ALARM.minutesBefore,
      sound: typeof p.sound === 'boolean' ? p.sound : DEFAULT_ALARM.sound,
      vibrate: typeof p.vibrate === 'boolean' ? p.vibrate : DEFAULT_ALARM.vibrate,
    }
  } catch {
    return { ...DEFAULT_ALARM }
  }
}

export function saveAlarmSettings(s: AlarmSettings) {
  localStorage.setItem(ALARM_KEY, JSON.stringify(s))
}

/** Bugun ishlagan budilnik id lari (kun o‘zgasa tozalanadi) */
export function loadFired(): Set<string> {
  try {
    const raw = localStorage.getItem(FIRED_KEY)
    if (!raw) return new Set()
    const parsed = JSON.parse(raw) as { day: string; ids: string[] }
    const today = new Date().toDateString()
    if (parsed.day !== today) return new Set()
    return new Set(parsed.ids || [])
  } catch {
    return new Set()
  }
}

export function saveFired(ids: Set<string>) {
  localStorage.setItem(
    FIRED_KEY,
    JSON.stringify({ day: new Date().toDateString(), ids: [...ids] }),
  )
}
