const KEY = 'ingliz-tili-progress-v2'

export type SkillId =
  | 'vocab'
  | 'listening'
  | 'reading'
  | 'writing'
  | 'speaking'
  | 'pronounce'
  | 'quiz'

export type Progress = {
  done: string[]
  scores: Record<string, number>
  skills: Record<string, Partial<Record<SkillId, number>>>
  xp: number
  streak: number
  lastPlayDay: string
  games: Record<string, number>
}

function today() {
  return new Date().toISOString().slice(0, 10)
}

const empty = (): Progress => ({
  done: [],
  scores: {},
  skills: {},
  xp: 0,
  streak: 0,
  lastPlayDay: '',
  games: {},
})

export function loadProgress(): Progress {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) {
      // migrate v1 lightly
      const v1 = localStorage.getItem('ingliz-tili-progress-v1')
      if (v1) {
        const old = JSON.parse(v1) as { done?: string[]; scores?: Record<string, number> }
        const p = empty()
        p.done = Array.isArray(old.done) ? old.done : []
        p.scores = old.scores && typeof old.scores === 'object' ? old.scores : {}
        saveProgress(p)
        return p
      }
      return empty()
    }
    const data = JSON.parse(raw) as Progress
    return {
      done: Array.isArray(data.done) ? data.done : [],
      scores: data.scores && typeof data.scores === 'object' ? data.scores : {},
      skills: data.skills && typeof data.skills === 'object' ? data.skills : {},
      xp: typeof data.xp === 'number' ? data.xp : 0,
      streak: typeof data.streak === 'number' ? data.streak : 0,
      lastPlayDay: typeof data.lastPlayDay === 'string' ? data.lastPlayDay : '',
      games: data.games && typeof data.games === 'object' ? data.games : {},
    }
  } catch {
    return empty()
  }
}

export function saveProgress(p: Progress) {
  localStorage.setItem(KEY, JSON.stringify(p))
}

function bumpStreak(p: Progress) {
  const d = today()
  if (p.lastPlayDay === d) return
  const y = new Date()
  y.setDate(y.getDate() - 1)
  const yday = y.toISOString().slice(0, 10)
  p.streak = p.lastPlayDay === yday ? p.streak + 1 : 1
  p.lastPlayDay = d
}

export function addXp(amount: number) {
  const p = loadProgress()
  bumpStreak(p)
  p.xp += Math.max(0, amount)
  saveProgress(p)
  return p
}

export function markSkill(lessonId: string, skill: SkillId, score: number) {
  const p = loadProgress()
  bumpStreak(p)
  if (!p.skills[lessonId]) p.skills[lessonId] = {}
  const prev = p.skills[lessonId][skill] ?? 0
  p.skills[lessonId][skill] = Math.max(prev, score)
  p.xp += Math.round(score / 10) + 5

  const skills = p.skills[lessonId]
  const vals = Object.values(skills)
  if (vals.length >= 5) {
    const avg = Math.round(vals.reduce((a, b) => a + (b ?? 0), 0) / vals.length)
    if (!p.done.includes(lessonId)) p.done.push(lessonId)
    p.scores[lessonId] = Math.max(p.scores[lessonId] ?? 0, avg)
  }
  saveProgress(p)
  return p
}

export function markGame(gameId: string, score: number, xp = 8) {
  const p = loadProgress()
  bumpStreak(p)
  p.games[gameId] = Math.max(p.games[gameId] ?? 0, score)
  p.xp += xp
  saveProgress(p)
  return p
}

export function lessonSkillCount(p: Progress, lessonId: string) {
  return Object.keys(p.skills[lessonId] || {}).length
}

export function resetProgress() {
  localStorage.removeItem(KEY)
  return empty()
}
