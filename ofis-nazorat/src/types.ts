export type PersonStatus = 'inside' | 'outside'

export type Person = {
  id: string
  name: string
  descriptor: number[]
  thumb: string
  status: PersonStatus
  createdAt: string
}

export type LogEvent = {
  id: string
  personId: string
  name: string
  type: 'kirish' | 'chiqish'
  at: string
  thumb?: string
}
