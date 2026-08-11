import type { Person } from '../types'

export function displayName(p: Person): string {
  return [p.firstName, p.lastName].filter(Boolean).join(' ').trim() || 'Nomsiz'
}

export function yearsLabel(p: Person): string {
  if (!p.birthYear && !p.deathYear) return ''
  if (p.birthYear && p.deathYear) return `${p.birthYear}–${p.deathYear}`
  if (p.birthYear) return `${p.birthYear}–`
  return `†${p.deathYear}`
}

export function getRoot(people: Person[]): Person | null {
  return people.find((p) => p.isRoot) || people[0] || null
}

export function getPerson(people: Person[], id: string | null | undefined): Person | null {
  if (!id) return null
  return people.find((p) => p.id === id) || null
}

export function getChildren(people: Person[], parentId: string): Person[] {
  return people.filter(
    (p) => p.fatherId === parentId || p.motherId === parentId,
  )
}

export function getParents(people: Person[], person: Person): {
  father: Person | null
  mother: Person | null
} {
  return {
    father: getPerson(people, person.fatherId),
    mother: getPerson(people, person.motherId),
  }
}

export type TreeNode = {
  person: Person
  spouse: Person | null
  children: TreeNode[]
}

/** Focus person at center; parents above (not nested deep), children below. */
export function buildFocusTree(people: Person[], focusId: string): {
  father: Person | null
  mother: Person | null
  focus: Person
  spouse: Person | null
  children: Person[]
} | null {
  const focus = getPerson(people, focusId)
  if (!focus) return null
  const { father, mother } = getParents(people, focus)
  const spouse = getPerson(people, focus.spouseId)
  const children = getChildren(people, focus.id)
  return { father, mother, focus, spouse, children }
}
