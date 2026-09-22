export type ThemeId = 'jade' | 'midnight' | 'petal' | 'sand'

export type EventId =
  | 'toy'
  | 'nikoh'
  | 'sunnat'
  | 'tugilgan'
  | 'yubiley'
  | 'uy'
  | 'umumiy'

export type InviteData = {
  eventId: EventId
  themeId: ThemeId
  title: string
  hosts: string
  guest: string
  date: string
  time: string
  place: string
  note: string
  phone: string
}

export type Theme = {
  id: ThemeId
  label: string
  bg0: string
  bg1: string
  ink: string
  muted: string
  accent: string
  line: string
  paper: string
}

export type EventKind = {
  id: EventId
  label: string
  defaultTitle: string
  defaultNote: string
  hint: string
}

export const THEMES: Theme[] = [
  {
    id: 'jade',
    label: 'Zumrad',
    bg0: '#0B2A22',
    bg1: '#145C48',
    ink: '#F3EDE0',
    muted: 'rgba(243,237,224,0.72)',
    accent: '#D4AF6A',
    line: 'rgba(212,175,106,0.55)',
    paper: 'rgba(243,237,224,0.06)',
  },
  {
    id: 'midnight',
    label: 'Tun',
    bg0: '#0A1224',
    bg1: '#1A2F55',
    ink: '#EAF0FF',
    muted: 'rgba(234,240,255,0.7)',
    accent: '#9EC5FF',
    line: 'rgba(158,197,255,0.45)',
    paper: 'rgba(234,240,255,0.05)',
  },
  {
    id: 'petal',
    label: 'Gul',
    bg0: '#3A1524',
    bg1: '#7A2E4A',
    ink: '#FFF0F5',
    muted: 'rgba(255,240,245,0.72)',
    accent: '#F0B7C8',
    line: 'rgba(240,183,200,0.5)',
    paper: 'rgba(255,240,245,0.06)',
  },
  {
    id: 'sand',
    label: 'Qum',
    bg0: '#2A2118',
    bg1: '#5A4632',
    ink: '#F7F1E6',
    muted: 'rgba(247,241,230,0.72)',
    accent: '#E0C28A',
    line: 'rgba(224,194,138,0.5)',
    paper: 'rgba(247,241,230,0.06)',
  },
]

export const EVENTS: EventKind[] = [
  {
    id: 'toy',
    label: 'To‘y',
    defaultTitle: 'To‘yga taklif',
    defaultNote: 'Hurmat bilan taklif etamiz',
    hint: 'Kelin-kuyov oilasi',
  },
  {
    id: 'nikoh',
    label: 'Nikoh',
    defaultTitle: 'Nikoh to‘yi',
    defaultNote: 'Marosimimizda biz bilan bo‘ling',
    hint: 'Nikoh marosimi',
  },
  {
    id: 'sunnat',
    label: 'Sunnat',
    defaultTitle: 'Sunnat to‘yi',
    defaultNote: 'Oilaimiz bayramiga taklif',
    hint: 'Bolajon uchun',
  },
  {
    id: 'tugilgan',
    label: 'Tug‘ilgan kun',
    defaultTitle: 'Tug‘ilgan kun',
    defaultNote: 'Bayramimizni birga nishonlaylik',
    hint: 'Yubiley / kun',
  },
  {
    id: 'yubiley',
    label: 'Yubiley',
    defaultTitle: 'Yubiley kechasi',
    defaultNote: 'Sizni kutamiz',
    hint: 'Yillar bayrami',
  },
  {
    id: 'uy',
    label: 'Yangi uy',
    defaultTitle: 'Yangi uyga taklif',
    defaultNote: 'Uyimizni birga ochaylik',
    hint: 'Ko‘chish / ochilish',
  },
  {
    id: 'umumiy',
    label: 'Boshqa',
    defaultTitle: 'Taklifnoma',
    defaultNote: 'Hurmat bilan',
    hint: 'Erkin matn',
  },
]

export function themeById(id: ThemeId): Theme {
  return THEMES.find((t) => t.id === id) || THEMES[0]
}

export function eventById(id: EventId): EventKind {
  return EVENTS.find((e) => e.id === id) || EVENTS[0]
}

export function defaultInvite(): InviteData {
  const ev = EVENTS[0]
  return {
    eventId: ev.id,
    themeId: 'jade',
    title: ev.defaultTitle,
    hosts: 'Alievlar oilasi',
    guest: '',
    date: '2026-yil 15-may',
    time: '18:00',
    place: 'Bekobod, Saryuz mahalla',
    note: ev.defaultNote,
    phone: '',
  }
}
