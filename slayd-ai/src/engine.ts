export type ThemeName = 'ocean' | 'sunset' | 'forest' | 'mono' | 'candy'

export type Slide = {
  id: string
  kind: 'title' | 'bullets' | 'quote' | 'outro'
  title: string
  subtitle?: string
  bullets?: string[]
  quote?: string
}

export type Deck = {
  title: string
  theme: ThemeName
  slides: Slide[]
}

export type ChatMsg = {
  id: string
  role: 'user' | 'assistant'
  text: string
}

let seq = 0
function uid() {
  seq += 1
  return `s${Date.now()}_${seq}`
}

export function detectTheme(text: string): ThemeName {
  const t = text.toLowerCase()
  if (/qorong|dark|mono|minimal/.test(t)) return 'mono'
  if (/bolalar|kids|candy|pushti|pink/.test(t)) return 'candy'
  if (/yashil|tabiat|forest|eco/.test(t)) return 'forest'
  if (/olov|sunset|issi|energy/.test(t)) return 'sunset'
  return 'ocean'
}

function extractTitle(prompt: string): string {
  const cleaned = prompt.replace(/\s+/g, ' ').trim()
  const m =
    cleaned.match(/(?:mavzu|tema|title|haqida)[:\s]+["«]?([^"».!?\n]{3,60})/i) ||
    cleaned.match(/^(.{8,48}?)(?:\.|,|!|\n|$)/)
  if (m?.[1]) return capitalize(m[1].trim())
  if (cleaned.length <= 48) return capitalize(cleaned)
  return capitalize(cleaned.slice(0, 42)) + '…'
}

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function topicBullets(topic: string): string[] {
  const base = topic.toLowerCase()
  if (/maktab|dars|talim|ta’lim|ta'lim/.test(base)) {
    return [
      'Maqsadni aniq belgilang',
      'Qisqa va tushunarli misollar',
      'Amaliy topshiriq qo‘shing',
      'Yakunida xulosa va savol',
    ]
  }
  if (/biznes|startap|sotuv|marketing/.test(base)) {
    return [
      'Muammo va imkoniyat',
      'Yechim va qiymat',
      'Bozor va mijoz',
      'Keyingi qadamlar',
    ]
  }
  if (/salomat|sport|sog/.test(base)) {
    return [
      'Kundalik odatlar',
      'Harakat va dam olish',
      'Oziqlanish asoslari',
      'Motivatsiya',
    ]
  }
  return [
    `${capitalize(topic)} nima?`,
    'Nega muhim?',
    'Asosiy qadamlari',
    'Amaliy maslahatlar',
  ]
}

/** Birinchi promptdan to‘liq deck */
export function generateDeck(prompt: string): { deck: Deck; reply: string } {
  const title = extractTitle(prompt)
  const theme = detectTheme(prompt)
  const bullets = topicBullets(title)
  const deck: Deck = {
    title,
    theme,
    slides: [
      {
        id: uid(),
        kind: 'title',
        title,
        subtitle: 'Slayd Studio · chat orqali yaratildi',
      },
      {
        id: uid(),
        kind: 'bullets',
        title: 'Asosiy fikrlar',
        bullets,
      },
      {
        id: uid(),
        kind: 'bullets',
        title: 'Amaliyot',
        bullets: [
          '1-qadam: reja tuzing',
          '2-qadam: oddiy misol',
          '3-qadam: natijani baholang',
        ],
      },
      {
        id: uid(),
        kind: 'quote',
        title: 'Eslatma',
        quote: 'Oddiy tushuntirish — eng kuchli taqdimot.',
      },
      {
        id: uid(),
        kind: 'outro',
        title: 'Rahmat!',
        subtitle: 'Savollaringiz bormi?',
      },
    ],
  }
  return {
    deck,
    reply: `«${title}» bo‘yicha ${deck.slides.length} ta slayd tayyor. Mavzu: ${theme}. Chatda o‘zgartiring: «yana slayd», «qorong‘u tema», «sarlavhani o‘zgartir …».`,
  }
}

/** Keyingi chat buyruqlari */
export function applyChat(
  deck: Deck,
  message: string,
): { deck: Deck; reply: string } {
  const raw = message.trim()
  const t = raw.toLowerCase()
  const next: Deck = {
    ...deck,
    slides: deck.slides.map((s) => ({ ...s, bullets: s.bullets ? [...s.bullets] : undefined })),
  }

  if (/^(yangi|qayta|boshl|create|generate)/.test(t) || t.length > 40) {
    if (/slayd|prezent|taqdim|deck|mavzu/.test(t) || t.length > 40) {
      return generateDeck(raw)
    }
  }

  if (/qorong|dark|mono/.test(t)) {
    next.theme = 'mono'
    return { deck: next, reply: 'Tema: mono (qorong‘u minimal).' }
  }
  if (/ocean|ko‘k|kok|blue/.test(t)) {
    next.theme = 'ocean'
    return { deck: next, reply: 'Tema: ocean.' }
  }
  if (/sunset|olov|qizil/.test(t)) {
    next.theme = 'sunset'
    return { deck: next, reply: 'Tema: sunset.' }
  }
  if (/forest|yashil|eco/.test(t)) {
    next.theme = 'forest'
    return { deck: next, reply: 'Tema: forest.' }
  }
  if (/candy|pushti|bolalar/.test(t)) {
    next.theme = 'candy'
    return { deck: next, reply: 'Tema: candy.' }
  }

  if (/yana slayd|slayd qo‘sh|slayd qosh|add slide|yangi slayd/.test(t)) {
    const titleMatch = raw.match(/(?:sarlavha|title)[:\s]+(.+)$/i)
    next.slides.splice(next.slides.length - 1, 0, {
      id: uid(),
      kind: 'bullets',
      title: titleMatch?.[1]?.trim() || 'Yangi slayd',
      bullets: ['Punkt 1', 'Punkt 2', 'Punkt 3'],
    })
    return { deck: next, reply: 'Yangi slayd qo‘shildi (yakundan oldin).' }
  }

  if (/o‘chir|ochir|delete|remove/.test(t)) {
    if (next.slides.length <= 2) {
      return { deck: next, reply: 'Kamida 2 ta slayd qolishi kerak.' }
    }
    const num = Number((t.match(/\d+/) || [])[0])
    const i = Number.isFinite(num) && num >= 1 ? num - 1 : next.slides.length - 2
    if (i >= 0 && i < next.slides.length) {
      const gone = next.slides[i].title
      next.slides.splice(i, 1)
      return { deck: next, reply: `«${gone}» o‘chirildi.` }
    }
  }

  const rename = raw.match(/(?:sarlavha|title|nomini)\s*(?:o‘zgartir|ozgartir|qil)?[:\s]+(.+)/i)
  if (rename?.[1]) {
    next.title = rename[1].trim()
    if (next.slides[0]) next.slides[0] = { ...next.slides[0], title: next.title }
    return { deck: next, reply: `Sarlavha: «${next.title}».` }
  }

  if (/punkt|bullet|band/.test(t)) {
    const add = raw.match(/(?:qo‘sh|qosh|add)[:\s]+(.+)/i)
    const target = next.slides.find((s) => s.kind === 'bullets')
    if (target && add?.[1]) {
      target.bullets = [...(target.bullets || []), add[1].trim()]
      return { deck: next, reply: `Punkt qo‘shildi: «${add[1].trim()}».` }
    }
  }

  if (/qisqa|kamaytir|3 slayd|2 slayd/.test(t)) {
    next.slides = [
      next.slides[0],
      {
        id: uid(),
        kind: 'bullets',
        title: 'Asosiy',
        bullets: topicBullets(next.title).slice(0, 3),
      },
      next.slides[next.slides.length - 1],
    ]
    return { deck: next, reply: 'Deck qisqartirildi: 3 ta slayd.' }
  }

  return {
    deck: next,
    reply:
      'Tushunmadim. Masalan: «yana slayd», «qorong‘u tema», «sarlavhani o‘zgartir Marketing», «punkt qo‘sh: Yangi g‘oya».',
  }
}

export const THEME_CSS: Record<
  ThemeName,
  { bg: string; accent: string; text: string; muted: string; card: string }
> = {
  ocean: {
    bg: 'linear-gradient(145deg,#0b3d5c,#147a9c 55%,#1ec8c8)',
    accent: '#7ef0e8',
    text: '#ffffff',
    muted: 'rgba(255,255,255,0.78)',
    card: 'rgba(255,255,255,0.12)',
  },
  sunset: {
    bg: 'linear-gradient(145deg,#3b1020,#c43c2e 50%,#f0a33a)',
    accent: '#ffd28a',
    text: '#fff7ef',
    muted: 'rgba(255,247,239,0.8)',
    card: 'rgba(0,0,0,0.18)',
  },
  forest: {
    bg: 'linear-gradient(145deg,#0f2a1d,#1f6a45 50%,#8fd18a)',
    accent: '#d4ff9a',
    text: '#f4fff0',
    muted: 'rgba(244,255,240,0.8)',
    card: 'rgba(255,255,255,0.12)',
  },
  mono: {
    bg: 'linear-gradient(160deg,#0b0d12,#1a1f2b)',
    accent: '#9ae6b4',
    text: '#f3f4f6',
    muted: 'rgba(243,244,246,0.7)',
    card: 'rgba(255,255,255,0.06)',
  },
  candy: {
    bg: 'linear-gradient(145deg,#ff7eb6,#b794f6 50%,#7dd3fc)',
    accent: '#fff1a8',
    text: '#2a1840',
    muted: 'rgba(42,24,64,0.7)',
    card: 'rgba(255,255,255,0.45)',
  },
}
