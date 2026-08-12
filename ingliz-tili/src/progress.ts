const KEY = 'ingliz-tili-progress-v1'

export type Progress = {
  done: string[]
  scores: Record<string, number>
}

const empty: Progress = { done: [], scores: {} }

export function loadProgress(): Progress {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { ...empty, done: [], scores: {} }
    const data = JSON.parse(raw) as Progress
    return {
      done: Array.isArray(data.done) ? data.done : [],
      scores:
        data.scores && typeof data.scores === 'object' ? data.scores : {},
    }
  } catch {
    return { ...empty, done: [], scores: {} }
  }
}

export function saveProgress(p: Progress) {
  localStorage.setItem(KEY, JSON.stringify(p))
}

export function markDone(id: string, score: number) {
  const p = loadProgress()
  if (!p.done.includes(id)) p.done.push(id)
  p.scores[id] = Math.max(p.scores[id] ?? 0, score)
  saveProgress(p)
  return p
}

export function resetProgress() {
  localStorage.removeItem(KEY)
  return { ...empty, done: [], scores: {} }
}
