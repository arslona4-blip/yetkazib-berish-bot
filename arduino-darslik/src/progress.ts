const KEY = 'arduino-darslik-progress-v1'

export function loadDone(): string[] {
  try {
    const raw = localStorage.getItem(KEY)
    const arr = raw ? (JSON.parse(raw) as string[]) : []
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

export function saveDone(ids: string[]) {
  localStorage.setItem(KEY, JSON.stringify(ids))
}
