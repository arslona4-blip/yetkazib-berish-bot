export type Gender = 'male' | 'female' | 'other'

export type Person = {
  id: string
  firstName: string
  lastName: string
  gender: Gender
  birthYear: string
  deathYear: string
  photoDataUrl: string
  notes: string
  fatherId: string | null
  motherId: string | null
  spouseId: string | null
  isRoot: boolean
  createdAt: string
}

export type TreeData = {
  version: 1
  ownerName: string
  treeTitle: string
  people: Person[]
  updatedAt: string
}

export type Screen =
  | 'welcome'
  | 'onboarding'
  | 'tree'
  | 'people'
  | 'person'
  | 'about'
  | 'share'
  | 'join'

