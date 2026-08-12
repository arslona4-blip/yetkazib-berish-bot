export type ThemeId = 'yulduz' | 'bog' | 'maktab' | 'ranglar'

export type Scene = {
  id: string
  title: string
  narrate: string
  mood: 'dawn' | 'garden' | 'magic' | 'play' | 'sunset' | 'school'
  emoji: string
}

export const THEMES: { id: ThemeId; title: string; desc: string; emoji: string }[] = [
  { id: 'yulduz', title: 'Yulduzchi', desc: 'Do‘stlik haqida', emoji: '⭐' },
  { id: 'bog', title: 'Sehrli bog‘', desc: 'Tabiat sarguzashti', emoji: '🌸' },
  { id: 'maktab', title: 'Birinchi dars', desc: 'Maktabga tayyorlik', emoji: '📚' },
  { id: 'ranglar', title: 'Ranglar', desc: 'O‘rganamiz', emoji: '🎨' },
]

export function buildStory(name: string, theme: ThemeId): Scene[] {
  const n = (name.trim() || 'Oybola').replace(/[<>]/g, '')
  switch (theme) {
    case 'bog':
      return [
        {
          id: '1',
          title: 'Ertalab',
          narrate: `${n} ertalab uyg‘ondi va sehrli bog‘ga chiqmoqchi bo‘ldi.`,
          mood: 'dawn',
          emoji: '🐰',
        },
        {
          id: '2',
          title: 'Gullar',
          narrate: `Bog‘da rang-barang gullar ochilgan edi. ${n} hidi bilan nafas oldi.`,
          mood: 'garden',
          emoji: '🌷',
        },
        {
          id: '3',
          title: 'Kapalak',
          narrate: `Kichkina kapalak ${n} yoniga qo‘ndi va birga uchib ketdi.`,
          mood: 'play',
          emoji: '🦋',
        },
        {
          id: '4',
          title: 'Do‘stlik',
          narrate: `${n} tushundi: tabiatni asrash — eng yaxshi do‘stlik.`,
          mood: 'sunset',
          emoji: '💛',
        },
      ]
    case 'maktab':
      return [
        {
          id: '1',
          title: 'Sumka',
          narrate: `${n} sumkasini tayyorladi. Bugun birinchi dars kuni!`,
          mood: 'dawn',
          emoji: '🎒',
        },
        {
          id: '2',
          title: 'Yo‘l',
          narrate: `${n} maktab sari yurdi. Quyosh ham tabassum qildi.`,
          mood: 'school',
          emoji: '🏫',
        },
        {
          id: '3',
          title: 'Sinf',
          narrate: `Sinfda yangi do‘stlar kutardi. ${n} salom berdi.`,
          mood: 'play',
          emoji: '👋',
        },
        {
          id: '4',
          title: 'Bilim',
          narrate: `O‘qish — sehr! ${n} bugun yangi so‘z o‘rgandi.`,
          mood: 'magic',
          emoji: '✨',
        },
      ]
    case 'ranglar':
      return [
        {
          id: '1',
          title: 'Qizil',
          narrate: `${n}, mana qizil olma! Qizil — issiq va baxtli rang.`,
          mood: 'dawn',
          emoji: '🍎',
        },
        {
          id: '2',
          title: 'Ko‘k',
          narrate: `Ko‘k osmon kabi. ${n} chuqur nafas oldi.`,
          mood: 'magic',
          emoji: '🔵',
        },
        {
          id: '3',
          title: 'Yashil',
          narrate: `Yashil barglar. ${n} bog‘da sakradi.`,
          mood: 'garden',
          emoji: '🌿',
        },
        {
          id: '4',
          title: 'Aralash',
          narrate: `Barcha ranglar birga — dunyo go‘zal! ${n} kuldi.`,
          mood: 'play',
          emoji: '🌈',
        },
      ]
    default:
      return [
        {
          id: '1',
          title: 'Uyg‘onish',
          narrate: `Ertalab ${n} uyg‘ondi. Bugun u do‘sti Yulduzchini topmoqchi!`,
          mood: 'dawn',
          emoji: '🐰',
        },
        {
          id: '2',
          title: 'Deraza',
          narrate: `Derazadan osmonda kichkina yulduz miltillardi.`,
          mood: 'magic',
          emoji: '⭐',
        },
        {
          id: '3',
          title: 'Uchrashuv',
          narrate: `Mana! Yulduzchi gul ustida o‘tiribdi. ${n} xursand bo‘ldi.`,
          mood: 'garden',
          emoji: '🌸',
        },
        {
          id: '4',
          title: 'O‘yin',
          narrate: `Ular birga o‘ynashdi: sakrash, kulish, raqsga tushish!`,
          mood: 'play',
          emoji: '💃',
        },
        {
          id: '5',
          title: 'Yakun',
          narrate: `Do‘stlik — eng yorqin yulduz. Xayr, kichkintoylar!`,
          mood: 'sunset',
          emoji: '🌙',
        },
      ]
  }
}
