export type ThemeName = 'ocean' | 'sunset' | 'forest' | 'mono' | 'candy'

export type DiagramKind = 'flow' | 'cycle' | 'cards' | 'compare'

export type Slide = {
  id: string
  kind: 'title' | 'bullets' | 'quote' | 'outro' | 'image' | 'diagram' | 'facts'
  title: string
  subtitle?: string
  bullets?: string[]
  quote?: string
  /** Rasm (Unsplash yoki SVG data) */
  imageUrl?: string
  imageCaption?: string
  /** Sxema */
  diagram?: DiagramKind
  nodes?: { label: string; icon?: string }[]
  /** Fact cards */
  facts?: { label: string; value: string; note?: string }[]
}

export type Deck = {
  title: string
  theme: ThemeName
  topicKey: string
  slides: Slide[]
}

export type ChatMsg = {
  id: string
  role: 'user' | 'assistant'
  text: string
}

type TopicPack = {
  key: string
  match: RegExp
  title: string
  theme: ThemeName
  summary: string
  definition: string
  bullets: string[]
  practice: string[]
  facts: { label: string; value: string; note?: string }[]
  flow: string[]
  cycle?: string[]
  compare?: [{ label: string; icon?: string }, { label: string; icon?: string }]
  quote: string
  imageQuery: string
  icons: string[]
}

const PACKS: TopicPack[] = [
  {
    key: 'tabiat',
    match: /tabiat|ekolog|muhit|daraxt|chiqindi|iqlim|green|eco/,
    title: 'Tabiatni asrash',
    theme: 'forest',
    summary: 'Atrof-muhitni himoya qilish — kelajak uchun zarur.',
    definition:
      'Tabiatni asrash — havo, suv, tuproq va jonivorlarni ifloslanishdan saqlash va resurslardan oqilona foydalanish.',
    bullets: [
      'Chiqindilarni ajratib tashlash (plastik, qog‘oz, oziq-ovqat)',
      'Suv va elektr energiyasini tejash',
      'Daraxt ekish va yashil zonani kengaytirish',
      'Transport: piyoda / velosiped / jamoat',
    ],
    practice: [
      'Uyda 1 hafta plastikni kamaytiring',
      'Maktabda “yashil burchak” tashkil eting',
      'Oilaviy daraxt ekish kuni',
    ],
    facts: [
      { label: '1 daraxt', value: '~20 kg', note: 'yiliga CO₂ yutishi mumkin' },
      { label: 'Qayta ishlash', value: '70%', note: 'qog‘ozni qayta ishlash suv tejaydi' },
      { label: 'Maqsad', value: '3R', note: 'Reduce · Reuse · Recycle' },
    ],
    flow: ['Muammo', 'Sabab', 'Yechim', 'Natija'],
    cycle: ['Kamaytir', 'Qayta ishlat', 'Qayta ishla', 'Tikla'],
    quote: 'Yerni bolalardan meros qilib olganimiz yo‘q — ulardan qarzga olganmiz.',
    imageQuery: 'nature forest green environment',
    icons: ['🌳', '♻️', '💧', '🌍'],
  },
  {
    key: 'marketing',
    match: /marketing|reklama|brend|sotuv|mijoz|pitch|startap|biznes/,
    title: 'Marketing asoslari',
    theme: 'sunset',
    summary: 'Mahsulotni to‘g‘ri mijozga, to‘g‘ri xabar bilan yetkazish.',
    definition:
      'Marketing — mijoz ehtiyojini tushunib, qiymat yaratish va sotish jarayonidir (4P: Product, Price, Place, Promotion).',
    bullets: [
      'Mijoz kim? (persona)',
      'Muammo qanday? (pain)',
      'Yechim nima? (value proposition)',
      'Qayerda uchrashamiz? (kanal)',
    ],
    practice: [
      '1 jumlalik value proposition yozing',
      '3 ta raqobatchini solishtiring',
      'Bir haftalik kontent rejasi tuzing',
    ],
    facts: [
      { label: '4P', value: 'Asos', note: 'Mahsulot · Narx · Joy · Reklama' },
      { label: 'CTR', value: '1–3%', note: 'oddiy reklama uchun taxmin' },
      { label: 'LTV', value: 'Muhim', note: 'mijoz umrbo‘yi qiymati' },
    ],
    flow: ['Tadqiqot', 'Taklif', 'Kanal', 'O‘lchash'],
    compare: [
      { label: 'Mahsulot markaz', icon: '📦' },
      { label: 'Mijoz markaz', icon: '👤' },
    ],
    quote: 'Odamlar mahsulot sotib olmaydi — yechim sotib oladi.',
    imageQuery: 'marketing business strategy meeting',
    icons: ['📈', '🎯', '💬', '🚀'],
  },
  {
    key: 'salomatlik',
    match: /salomat|sog‘lik|soglik|sport|ovqat|fitness|health/,
    title: 'Sog‘lom turmush',
    theme: 'ocean',
    summary: 'Kichik odatlar — katta salomatlik.',
    definition:
      'Sog‘lom turmush — uyqu, harakat, ovqatlanish va ruhiy holatni muvozanatda saqlash.',
    bullets: [
      'Kuniga 7–8 soat uyqu',
      '30 daqiqa yurish yoki mashq',
      'Suv ichish (1.5–2 litr)',
      'Shirinni kamaytirish',
    ],
    practice: [
      'Ertalab 10 daqiqa cho‘zilish',
      'Telefonni uxlashdan 1 soat oldin qo‘ying',
      'Haftada 3 marta sport',
    ],
    facts: [
      { label: 'Yurish', value: '8000+', note: 'qadam/kun — yaxshi maqsad' },
      { label: 'Suv', value: '2 L', note: 'o‘rtacha kunlik' },
      { label: 'Uyqu', value: '7–9 s', note: 'o‘smirlar uchun' },
    ],
    flow: ['Uyqu', 'Harakat', 'Ovqat', 'Dam'],
    cycle: ['Reja', 'Bajar', 'Bahola', 'Yaxshila'],
    quote: 'Salomatlik — eng yaxshi investitsiya.',
    imageQuery: 'healthy lifestyle running outdoors',
    icons: ['🏃', '🥗', '😴', '❤️'],
  },
  {
    key: 'matem',
    match: /matem|algebra|geometr|son|foiz|formula/,
    title: 'Matematika asoslari',
    theme: 'ocean',
    summary: 'Matematika — mantiqiy fikrlash tili.',
    definition:
      'Matematika miqdor, shakl va bog‘liqliklarni o‘rganadi. Amaliy hayotda hisob, foiz, geometriya kerak.',
    bullets: [
      'Qo‘shish / ayirish — asos',
      'Ko‘paytirish / bo‘lish — tezlik',
      'Foiz — chegirma va foizlar',
      'Geometriya — shakl va maydon',
    ],
    practice: [
      '10 ta foiz masalasi yeching',
      'Xonaning maydonini o‘lchang',
      'Byudjet jadvali tuzing',
    ],
    facts: [
      { label: 'π', value: '3.14', note: 'aylana doimiysi' },
      { label: 'Foiz', value: '/100', note: 'qismning yuzdan biri' },
      { label: 'Pifagor', value: 'a²+b²=c²', note: 'to‘g‘ri burchakli uchburchak' },
    ],
    flow: ['Masala', 'Formula', 'Hisob', 'Tekshir'],
    quote: 'Matematika — aqlning sporti.',
    imageQuery: 'mathematics chalkboard formulas education',
    icons: ['🔢', '📐', '📊', '✏️'],
  },
  {
    key: 'tarix',
    match: /tarix|history|amir|temur|mustaqil|davlat/,
    title: 'Tarixga nazar',
    theme: 'sunset',
    summary: 'O‘tmishni bilish — kelajakni tushunish.',
    definition:
      'Tarix — insoniyat voqealarini o‘rganadi: sabab, jarayon, oqibat.',
    bullets: [
      'Manbalarni tekshirish',
      'Sana va kontekst',
      'Shaxslar va qarorlar',
      'Bugungi dars',
    ],
    practice: [
      'Bir voqeani 5 jumlada bayon qiling',
      'Xarita ustida yo‘nalishni ko‘rsating',
      'Ikki davrni solishtiring',
    ],
    facts: [
      { label: 'Manba', value: '2+', note: 'kamida ikki manba solishtiring' },
      { label: 'Vaqt', value: 'Kronologiya', note: 'voqealar ketma-ketligi' },
      { label: 'Sabab', value: '→', note: 'oqibat zanjiri' },
    ],
    flow: ['Sabab', 'Voqea', 'Oqibat', 'Xulosa'],
    compare: [
      { label: 'Eski davr', icon: '🏛️' },
      { label: 'Yangi davr', icon: '🏙️' },
    ],
    quote: 'Tarixni bilmagan kelajakni qurishda xato qiladi.',
    imageQuery: 'historical architecture uzbekistan silk road',
    icons: ['📜', '🏛️', '🗺️', '⏳'],
  },
  {
    key: 'it',
    match: /it|dastur|kod|python|kompyuter|ai|sun.?iy|algoritm|web/,
    title: 'IT va dasturlash',
    theme: 'mono',
    summary: 'Kod — muammoni bosqichma-bosqich yechish.',
    definition:
      'Dasturlash — kompyuterga aniq ko‘rsatmalar berish. Algoritm → kod → test → yaxshilash.',
    bullets: [
      'Muammoni kichik qismlarga bo‘ling',
      'Algoritm yozing (qadamlar)',
      'Kodni yozing va ishga tushiring',
      'Xatolarni tuzating (debug)',
    ],
    practice: [
      'Kalkulyator funksiyasini yozing',
      'Ro‘yxatni saralang',
      'Oddiy veb sahifa tuzing',
    ],
    facts: [
      { label: 'Loop', value: 'for/while', note: 'takrorlash' },
      { label: 'If', value: 'shart', note: 'qaror daraxti' },
      { label: 'Git', value: 'versiya', note: 'o‘zgarishlarni saqlash' },
    ],
    flow: ['Reja', 'Kod', 'Test', 'Deploy'],
    cycle: ['Yoz', 'Ishlat', 'Xato top', 'Tuzat'],
    quote: 'Birinchi kod chiroyli emas — ishlaydigan bo‘lsin.',
    imageQuery: 'programming laptop code developer',
    icons: ['💻', '⚙️', '🧩', '🛠️'],
  },
  {
    key: 'til',
    match: /til|ingliz|o‘zbek|uzbek|grammar|lug‘at|so‘z/,
    title: 'Til o‘rganish',
    theme: 'candy',
    summary: 'Har kuni biroz — tez o‘sish.',
    definition:
      'Til o‘rganish — tinglash, gapirish, o‘qish, yozish ko‘nikmalarini parallel rivojlantirish.',
    bullets: [
      'Har kuni 15 daqiqa tinglash',
      'Yangi 5–10 so‘z',
      'Ovoz chiqarib o‘qish',
      'Qisqa dialog yozish',
    ],
    practice: [
      '1 daqiqalik audio yozing',
      'Flashcard yasang',
      'Do‘st bilan 5 savol-javob',
    ],
    facts: [
      { label: 'SRS', value: 'Takror', note: 'spaced repetition' },
      { label: 'Input', value: '70%', note: 'tinglash/o‘qish ulushi' },
      { label: 'Output', value: '30%', note: 'gapirish/yozish' },
    ],
    flow: ['Tingla', 'Tushun', 'Takrorla', 'Ishlat'],
    quote: 'Til — eshik. Har kuni biroz oching.',
    imageQuery: 'language learning books study desk',
    icons: ['🗣️', '📖', '🎧', '✍️'],
  },
]

function uid() {
  return `s${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
}

export function detectTheme(text: string): ThemeName {
  const t = text.toLowerCase()
  if (/qorong|dark|mono|minimal/.test(t)) return 'mono'
  if (/bolalar|kids|candy|pushti|pink/.test(t)) return 'candy'
  if (/yashil|tabiat|forest|eco/.test(t)) return 'forest'
  if (/olov|sunset|issi|energy|marketing/.test(t)) return 'sunset'
  return 'ocean'
}

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
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

function findPack(prompt: string): TopicPack | null {
  const t = prompt.toLowerCase()
  return PACKS.find((p) => p.match.test(t)) || null
}

function genericPack(title: string, theme: ThemeName): TopicPack {
  return {
    key: 'generic',
    match: /.*/,
    title,
    theme,
    summary: `${title} bo‘yicha qisqa, tushunarli taqdimot.`,
    definition: `${title} — bu mavzuning asosiy tushunchasi, maqsadi va amaliy ahamiyatini o‘z ichiga oladi.`,
    bullets: [
      `${title} nima ekanini tushuntiring`,
      'Asosiy tushunchalar va atamalar',
      'Hayotiy misollar',
      'Amaliy qadamlar',
    ],
    practice: [
      '3 ta misol yozing',
      'Qisqa xulosa chiqaring',
      'Do‘stga 1 daqiqada tushuntiring',
    ],
    facts: [
      { label: 'Maqsad', value: 'Aniq', note: 'nima uchun kerak?' },
      { label: 'Misollar', value: '2–3', note: 'tushunarli qiladi' },
      { label: 'Amaliyot', value: '1 qadam', note: 'darhol boshlang' },
    ],
    flow: ['Kirish', 'Asos', 'Misol', 'Xulosa'],
    quote: 'Yaxshi taqdimot — oddiy va aniq.',
    imageQuery: encodeURIComponent(title).slice(0, 40) + ' education presentation',
    icons: ['💡', '📚', '🧠', '✨'],
  }
}

function unsplash(query: string) {
  const q = encodeURIComponent(query)
  return `https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1400&q=80#${q}`
}

/** Mavzuga mos Unsplash (barqaror photo id lar + query hash) */
const IMAGE_MAP: Record<string, string> = {
  tabiat:
    'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1400&q=80',
  marketing:
    'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1400&q=80',
  salomatlik:
    'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?auto=format&fit=crop&w=1400&q=80',
  matem:
    'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?auto=format&fit=crop&w=1400&q=80',
  tarix:
    'https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1400&q=80',
  it: 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?auto=format&fit=crop&w=1400&q=80',
  til: 'https://images.unsplash.com/photo-1456513080800-7d93d8e9f5b5?auto=format&fit=crop&w=1400&q=80',
  generic:
    'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=1400&q=80',
}

function imageFor(pack: TopicPack) {
  return IMAGE_MAP[pack.key] || unsplash(pack.imageQuery)
}

export function generateDeck(prompt: string): { deck: Deck; reply: string } {
  const found = findPack(prompt)
  const titleHint = extractTitle(prompt)
  const forced = detectTheme(prompt)
  const themeWord =
    /qorong|dark|mono|candy|pushti|sunset|olov|forest|yashil|ocean|ko‘k/.test(
      prompt.toLowerCase(),
    )
  const theme = themeWord ? forced : found?.theme || forced
  const title = found ? found.title : titleHint
  const active = found || genericPack(title, theme)

  const slides: Slide[] = [
    {
      id: uid(),
      kind: 'title',
      title,
      subtitle: active.summary,
    },
    {
      id: uid(),
      kind: 'bullets',
      title: 'Bu nima?',
      bullets: [active.definition, ...active.bullets.slice(0, 2)],
    },
    {
      id: uid(),
      kind: 'image',
      title: 'Mavzu rasmi',
      imageUrl: imageFor(active),
      imageCaption: `${title} — vizual kontekst`,
      subtitle: active.icons.join('  '),
    },
    {
      id: uid(),
      kind: 'diagram',
      title: 'Jarayon sxemasi',
      diagram: 'flow',
      nodes: active.flow.map((label, i) => ({
        label,
        icon: active.icons[i % active.icons.length],
      })),
    },
    {
      id: uid(),
      kind: 'facts',
      title: 'Muhim raqamlar',
      facts: active.facts,
    },
    {
      id: uid(),
      kind: 'bullets',
      title: 'Asosiy fikrlar',
      bullets: active.bullets,
    },
    {
      id: uid(),
      kind: 'diagram',
      title: active.cycle ? 'Sikl sxemasi' : active.compare ? 'Taqqoslash' : 'Kartalar',
      diagram: active.cycle ? 'cycle' : active.compare ? 'compare' : 'cards',
      nodes: active.cycle
        ? active.cycle.map((label, i) => ({
            label,
            icon: active.icons[i % active.icons.length],
          }))
        : active.compare
          ? active.compare
          : active.bullets.slice(0, 4).map((label, i) => ({
              label,
              icon: active.icons[i % active.icons.length],
            })),
    },
    {
      id: uid(),
      kind: 'bullets',
      title: 'Amaliy topshiriqlar',
      bullets: active.practice,
    },
    {
      id: uid(),
      kind: 'quote',
      title: 'Eslatma',
      quote: active.quote,
    },
    {
      id: uid(),
      kind: 'outro',
      title: 'Rahmat!',
      subtitle: 'Savol-javob va muhokama',
    },
  ]

  const deck: Deck = { title, theme, topicKey: active.key, slides }
  return {
    deck,
    reply: `«${title}» bo‘yicha tayyor paket: ${slides.length} slayd · ta’rif · rasm · sxema · raqamlar · amaliyot. Yana: «yana sxema», «qorong‘u tema», «rasm qo‘sh».`,
  }
}

export function applyChat(
  deck: Deck,
  message: string,
): { deck: Deck; reply: string } {
  const raw = message.trim()
  const t = raw.toLowerCase()
  const next: Deck = {
    ...deck,
    slides: deck.slides.map((s) => ({
      ...s,
      bullets: s.bullets ? [...s.bullets] : undefined,
      nodes: s.nodes ? s.nodes.map((n) => ({ ...n })) : undefined,
      facts: s.facts ? s.facts.map((f) => ({ ...f })) : undefined,
    })),
  }

  if (
    /^(yangi|qayta|boshl|create|generate)/.test(t) ||
    ((/slayd|prezent|taqdim|deck|mavzu|haqida/.test(t) || t.length > 35) &&
      !/tema|theme|slayd qo|yana slayd|o‘chir|ochir|sarlavha|punkt|rasm|sxema/.test(t))
  ) {
    return generateDeck(raw)
  }

  if (/qorong|dark|mono/.test(t)) {
    next.theme = 'mono'
    return { deck: next, reply: 'Tema: mono.' }
  }
  if (/ocean|ko‘k|kok|blue/.test(t)) {
    next.theme = 'ocean'
    return { deck: next, reply: 'Tema: ocean.' }
  }
  if (/sunset|olov|qizil|marketing/.test(t)) {
    next.theme = 'sunset'
    return { deck: next, reply: 'Tema: sunset.' }
  }
  if (/forest|yashil|eco|tabiat/.test(t)) {
    next.theme = 'forest'
    return { deck: next, reply: 'Tema: forest.' }
  }
  if (/candy|pushti|bolalar/.test(t)) {
    next.theme = 'candy'
    return { deck: next, reply: 'Tema: candy.' }
  }

  if (/yana sxema|sxema qo|diagram|flow/.test(t)) {
    next.slides.splice(next.slides.length - 1, 0, {
      id: uid(),
      kind: 'diagram',
      title: 'Qo‘shimcha sxema',
      diagram: 'flow',
      nodes: [
        { label: 'Kirish', icon: '1️⃣' },
        { label: 'Tahlil', icon: '2️⃣' },
        { label: 'Yechim', icon: '3️⃣' },
        { label: 'Natija', icon: '4️⃣' },
      ],
    })
    return { deck: next, reply: 'Yangi sxema slaydi qo‘shildi.' }
  }

  if (/rasm|image|foto/.test(t)) {
    const pack = PACKS.find((p) => p.key === deck.topicKey)
    const url = pack ? imageFor(pack) : IMAGE_MAP.generic
    next.slides.splice(Math.min(2, next.slides.length - 1), 0, {
      id: uid(),
      kind: 'image',
      title: 'Qo‘shimcha rasm',
      imageUrl: url,
      imageCaption: deck.title,
    })
    return { deck: next, reply: 'Yangi rasm slaydi qo‘shildi.' }
  }

  if (/yana slayd|slayd qo‘sh|slayd qosh|add slide|yangi slayd/.test(t)) {
    next.slides.splice(next.slides.length - 1, 0, {
      id: uid(),
      kind: 'bullets',
      title: 'Yangi slayd',
      bullets: ['Punkt 1', 'Punkt 2', 'Punkt 3'],
    })
    return { deck: next, reply: 'Yangi slayd qo‘shildi.' }
  }

  if (/o‘chir|ochir|delete|remove/.test(t)) {
    if (next.slides.length <= 3) {
      return { deck: next, reply: 'Kamida 3 ta slayd qolishi kerak.' }
    }
    const num = Number((t.match(/\d+/) || [])[0])
    const i = Number.isFinite(num) && num >= 1 ? num - 1 : next.slides.length - 2
    if (i >= 0 && i < next.slides.length) {
      const gone = next.slides[i].title
      next.slides.splice(i, 1)
      return { deck: next, reply: `«${gone}» o‘chirildi.` }
    }
  }

  const rename = raw.match(
    /(?:sarlavha|title|nomini)\s*(?:o‘zgartir|ozgartir|qil)?[:\s]+(.+)/i,
  )
  if (rename?.[1]) {
    next.title = rename[1].trim()
    if (next.slides[0]) next.slides[0] = { ...next.slides[0], title: next.title }
    return { deck: next, reply: `Sarlavha: «${next.title}».` }
  }

  return {
    deck: next,
    reply:
      'Masalan: yangi mavzu yozing, «yana sxema», «rasm qo‘sh», «qorong‘u tema», «sarlavhani o‘zgartir …».',
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
