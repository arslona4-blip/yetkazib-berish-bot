import type { Lesson, Word } from './lessons'

export function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

export function pickWords(lesson: Lesson, n = 6): Word[] {
  return shuffle(lesson.words).slice(0, Math.min(n, lesson.words.length))
}

export function scrambleWord(word: string) {
  const letters = word.replace(/\s+/g, '').split('')
  if (letters.length < 2) return letters.join('')
  let out = shuffle(letters).join('')
  let guard = 0
  while (out.toLowerCase() === word.replace(/\s+/g, '').toLowerCase() && guard < 12) {
    out = shuffle(letters).join('')
    guard += 1
  }
  return out
}

export type MatchPair = { id: string; en: string; uz: string }

export function makeMatchPairs(lesson: Lesson, n = 5): MatchPair[] {
  return pickWords(lesson, n).map((w, i) => ({
    id: `${lesson.id}-${i}-${w.en}`,
    en: w.en,
    uz: w.uz,
  }))
}

export type MemoryCard = {
  id: string
  pairId: string
  label: string
  side: 'en' | 'uz'
}

export function makeMemoryCards(lesson: Lesson, n = 4): MemoryCard[] {
  const pairs = pickWords(lesson, n)
  const cards: MemoryCard[] = []
  pairs.forEach((w, i) => {
    const pairId = `p${i}`
    cards.push({ id: `${pairId}-en`, pairId, label: w.en, side: 'en' })
    cards.push({ id: `${pairId}-uz`, pairId, label: w.uz, side: 'uz' })
  })
  return shuffle(cards)
}

export const GAME_LIST = [
  {
    id: 'match',
    title: 'Juftlash',
    blurb: 'EN ↔ UZ bog‘lang',
    emoji: '🔗',
  },
  {
    id: 'scramble',
    title: 'Harflar',
    blurb: 'So‘zni yig‘ing',
    emoji: '🔤',
  },
  {
    id: 'memory',
    title: 'Xotira',
    blurb: 'Kartalarni oching',
    emoji: '🧠',
  },
  {
    id: 'lightning',
    title: 'Chaqmoq',
    blurb: '60 soniya quiz',
    emoji: '⚡',
  },
] as const

export type GameId = (typeof GAME_LIST)[number]['id']
