export type ThemeId = 'shohona' | 'pergament' | 'osmon' | 'lolazor'

export type KindId =
  | 'toy'
  | 'nikoh'
  | 'chaqaloq'
  | 'uy'
  | 'yubiley'
  | 'nisbat'
  | 'umumiy'

export type BaxtData = {
  kindId: KindId
  themeId: ThemeId
  title: string
  recipients: string
  from: string
  date: string
  place: string
  blessing: string
  seal: string
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
  light: boolean
}

export type Kind = {
  id: KindId
  label: string
  defaultTitle: string
  defaultBlessing: string
  hint: string
}

export const THEMES: Theme[] = [
  {
    id: 'shohona',
    label: 'Shohona',
    bg0: '#3A1020',
    bg1: '#6B2840',
    ink: '#F6EFE4',
    muted: 'rgba(246,239,228,0.72)',
    accent: '#C9A96E',
    line: 'rgba(201,169,110,0.55)',
    paper: 'rgba(246,239,228,0.06)',
    light: false,
  },
  {
    id: 'pergament',
    label: 'Pergament',
    bg0: '#EDE6DA',
    bg1: '#F7F2EA',
    ink: '#2C1810',
    muted: 'rgba(44,24,16,0.62)',
    accent: '#8B5A2B',
    line: 'rgba(139,90,43,0.4)',
    paper: 'rgba(139,90,43,0.05)',
    light: true,
  },
  {
    id: 'osmon',
    label: 'Osmon',
    bg0: '#1A2838',
    bg1: '#2F4558',
    ink: '#EEF3F7',
    muted: 'rgba(238,243,247,0.7)',
    accent: '#A8C5D4',
    line: 'rgba(168,197,212,0.45)',
    paper: 'rgba(238,243,247,0.05)',
    light: false,
  },
  {
    id: 'lolazor',
    label: 'Lolazor',
    bg0: '#4A1830',
    bg1: '#7A3050',
    ink: '#FFF4F7',
    muted: 'rgba(255,244,247,0.72)',
    accent: '#E8B4C4',
    line: 'rgba(232,180,196,0.5)',
    paper: 'rgba(255,244,247,0.06)',
    light: false,
  },
]

export const KINDS: Kind[] = [
  {
    id: 'toy',
    label: 'To‘y',
    defaultTitle: 'Baxtnoma',
    defaultBlessing: 'Uyingiz tinch, mehringiz abadiy bo‘lsin',
    hint: 'Kelin-kuyovga',
  },
  {
    id: 'nikoh',
    label: 'Nikoh',
    defaultTitle: 'Nikoh baxtnomasi',
    defaultBlessing: 'Olloh oilangizni baraka qilsin',
    hint: 'Nikoh marosimi',
  },
  {
    id: 'nisbat',
    label: 'Nisbat',
    defaultTitle: 'Nisbat tabrigi',
    defaultBlessing: 'Baxtli kelajak tilaymiz',
    hint: 'Unashuv / nisbat',
  },
  {
    id: 'chaqaloq',
    label: 'Chaqaloq',
    defaultTitle: 'Yangi hayot',
    defaultBlessing: 'Farzandingiz sog‘-salomat o‘ssin',
    hint: 'Tug‘ilish tabrigi',
  },
  {
    id: 'uy',
    label: 'Yangi uy',
    defaultTitle: 'Yangi uyga baxt',
    defaultBlessing: 'Uyingiz baxt va baraka bilan to‘lsin',
    hint: 'Ko‘chish / ochilish',
  },
  {
    id: 'yubiley',
    label: 'Yubiley',
    defaultTitle: 'Yubiley tabrigi',
    defaultBlessing: 'Yillar baxt va omad keltirsin',
    hint: 'Yillar bayrami',
  },
  {
    id: 'umumiy',
    label: 'Boshqa',
    defaultTitle: 'Baxtnoma',
    defaultBlessing: 'Baxt va omad tilaymiz',
    hint: 'Erkin matn',
  },
]

export function themeById(id: ThemeId): Theme {
  return THEMES.find((t) => t.id === id) || THEMES[0]
}

export function kindById(id: KindId): Kind {
  return KINDS.find((k) => k.id === id) || KINDS[0]
}

export function defaultBaxt(): BaxtData {
  const kind = KINDS[0]
  return {
    kindId: kind.id,
    themeId: 'shohona',
    title: kind.defaultTitle,
    recipients: 'Aziza & Jasur',
    from: 'Alievlar oilasi',
    date: '2026-yil 15-may',
    place: 'Bekobod',
    blessing: kind.defaultBlessing,
    seal: 'Hurmat bilan',
  }
}
