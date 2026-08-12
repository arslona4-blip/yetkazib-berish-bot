const KEY = 'dars-jadvali-done-v1'

export function loadDone(): Set<string> {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return new Set()
    const arr = JSON.parse(raw) as string[]
    return new Set(Array.isArray(arr) ? arr : [])
  } catch {
    return new Set()
  }
}

export function saveDone(ids: Set<string>) {
  localStorage.setItem(KEY, JSON.stringify([...ids]))
}
