import { defaultState, type ScheduleState } from './schedule'

const KEY = 'maktab-dars-jadvali-v1'

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
