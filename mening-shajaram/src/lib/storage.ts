import type { Person, TreeData } from '../types'

const KEY = 'mening-shajaram:v1'

export function loadTree(): TreeData | null {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as TreeData
    if (!data || data.version !== 1 || !Array.isArray(data.people)) return null
    return data
  } catch {
    return null
  }
}

export function saveTree(data: TreeData): void {
  const next: TreeData = {
    ...data,
    updatedAt: new Date().toISOString(),
  }
  localStorage.setItem(KEY, JSON.stringify(next))
}

export function clearTree(): void {
  localStorage.removeItem(KEY)
}

export function createEmptyTree(ownerName: string, root: Person): TreeData {
  return {
    version: 1,
    ownerName: ownerName.trim(),
    treeTitle: `${ownerName.trim()} oilasi`,
    people: [root],
    updatedAt: new Date().toISOString(),
  }
}

export function upsertPerson(data: TreeData, person: Person): TreeData {
  const idx = data.people.findIndex((p) => p.id === person.id)
  const people = [...data.people]
  if (idx >= 0) people[idx] = person
  else people.push(person)

  // Keep spouse link two-way when possible
  if (person.spouseId) {
    const spouse = people.find((p) => p.id === person.spouseId)
    if (spouse && spouse.spouseId !== person.id) {
      const sIdx = people.findIndex((p) => p.id === spouse.id)
      people[sIdx] = { ...spouse, spouseId: person.id }
    }
  }

  return { ...data, people }
}

export function deletePerson(data: TreeData, personId: string): TreeData {
  const people = data.people
    .filter((p) => p.id !== personId)
    .map((p) => ({
      ...p,
      fatherId: p.fatherId === personId ? null : p.fatherId,
      motherId: p.motherId === personId ? null : p.motherId,
      spouseId: p.spouseId === personId ? null : p.spouseId,
      isRoot: p.isRoot && p.id !== personId,
    }))

  if (people.length && !people.some((p) => p.isRoot)) {
    people[0] = { ...people[0], isRoot: true }
  }

  return { ...data, people }
}

export function newPersonId(): string {
  return crypto.randomUUID()
}
