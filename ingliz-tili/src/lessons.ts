import { TENSE_LESSONS } from './tenses'

export type Level = 'boshlangich' | 'ortacha' | 'ilgor'

export type Topic = 'mavzu' | 'zamon'

export type Word = {
  en: string
  uz: string
  tip?: string
}

export type Phrase = {
  en: string
  uz: string
}

export type QuizItem = {
  prompt: string
  options: string[]
  answer: number
  hint?: string
}

export type Reading = {
  title: string
  text: string
  questions: QuizItem[]
}

export type WritingItem = {
  promptUz: string
  answer: string
  accept?: string[]
}

export type ListeningItem = {
  audioText: string
  options: string[]
  answer: number
}

export type PronounceItem = {
  text: string
  tip: string
}

export type Lesson = {
  id: string
  num: number
  level: Level
  topic: Topic
  title: string
  summary: string
  minutes: number
  tip: string
  formula?: string
  signals?: string[]
  words: Word[]
  phrases: Phrase[]
  quiz: QuizItem[]
  reading: Reading
  writing: WritingItem[]
  listening: ListeningItem[]
  pronounce: PronounceItem[]
}

export const LEVEL_LABEL: Record<Level, string> = {
  boshlangich: 'Boshlang‘ich',
  ortacha: 'O‘rta',
  ilgor: 'Ilg‘or',
}

export const TOPIC_LABEL: Record<Topic, string> = {
  mavzu: 'Mavzu',
  zamon: 'Zamon',
}

export const SKILL_META = [
  { id: 'vocab', title: 'Lug‘at', blurb: 'So‘z va gaplar' },
  { id: 'listening', title: 'Listening', blurb: 'Eshitib tanlash' },
  { id: 'reading', title: 'Reading', blurb: 'O‘qib tushunish' },
  { id: 'writing', title: 'Writing', blurb: 'Yozib mashq' },
  { id: 'speaking', title: 'Speaking', blurb: 'Gapirish' },
  { id: 'pronounce', title: 'Talaffuz', blurb: 'Aniq ayting' },
  { id: 'quiz', title: 'Quiz', blurb: 'Bilim testi' },
] as const

export type SkillId = (typeof SKILL_META)[number]['id']

function norm(s: string) {
  return s
    .toLowerCase()
    .replace(/[’']/g, "'")
    .replace(/[^\w\s']/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export function answersMatch(input: string, answer: string, accept: string[] = []) {
  const n = norm(input)
  const list = [answer, ...accept].map(norm)
  return list.some((a) => a === n)
}

export const THEME_LESSONS: Lesson[] = [
  {
    id: 'greetings',
    num: 1,
    level: 'boshlangich',
    topic: 'mavzu',
    title: 'Salomlashish',
    summary: 'Hello, Good morning va kundalik salomlar.',
    minutes: 18,
    tip: 'Salomlashganda tabassum + aniq talaffuz — birinchi taassurot.',
    words: [
      { en: 'Hello', uz: 'Salom', tip: 'rasmiy va norasmiy' },
      { en: 'Hi', uz: 'Salom (do‘stona)' },
      { en: 'Good morning', uz: 'Xayrli tong' },
      { en: 'Good afternoon', uz: 'Xayrli kun' },
      { en: 'Good evening', uz: 'Xayrli kech' },
      { en: 'Goodbye', uz: 'Xayr' },
      { en: 'See you', uz: 'Ko‘rishguncha' },
      { en: 'Thank you', uz: 'Rahmat' },
      { en: 'Please', uz: 'Iltimos' },
      { en: 'Sorry', uz: 'Kechirasiz' },
    ],
    phrases: [
      { en: 'How are you?', uz: 'Qalaysiz?' },
      { en: 'I am fine, thank you.', uz: 'Yaxshi, rahmat.' },
      { en: 'Nice to meet you.', uz: 'Tanishganimdan xursandman.' },
      { en: 'What is your name?', uz: 'Ismingiz nima?' },
      { en: 'My name is Ali.', uz: 'Mening ismim Ali.' },
    ],
    quiz: [
      {
        prompt: '“Salom” (do‘stona) — qaysi?',
        options: ['Goodbye', 'Hi', 'Sorry', 'Please'],
        answer: 1,
      },
      {
        prompt: '“How are you?” nima degani?',
        options: ['Ismingiz nima?', 'Qalaysiz?', 'Rahmat', 'Xayr'],
        answer: 1,
      },
      {
        prompt: '“Nice to meet you.” — tarjimasi?',
        options: [
          'Yaxshi uxlang',
          'Tanishganimdan xursandman',
          'Qayerdansiz?',
          'Kechirasiz',
        ],
        answer: 1,
      },
      {
        prompt: 'Ertalab salomlashish:',
        options: ['Good night', 'Good morning', 'See you', 'Sorry'],
        answer: 1,
      },
    ],
    reading: {
      title: 'At school',
      text: 'Good morning! My name is Sara. I meet my friend Tom. “Hi, Tom! How are you?” “I am fine, thank you. Nice to meet your sister!” “See you later!”',
      questions: [
        {
          prompt: 'Sara kimni uchratadi?',
          options: ['O‘qituvchini', 'Tomni', 'Onasini', 'Haydovchini'],
          answer: 1,
        },
        {
          prompt: 'Tom nima deb javob beradi?',
          options: ['Sorry', 'I am fine, thank you', 'Goodbye', 'Please'],
          answer: 1,
        },
        {
          prompt: 'Oxirida Sara nima deydi?',
          options: ['Good morning', 'See you later', 'What is your name', 'Hello'],
          answer: 1,
        },
      ],
    },
    writing: [
      { promptUz: '“Salom” (do‘stona) ni yozing', answer: 'Hi', accept: ['hi', 'hello'] },
      { promptUz: '“Qalaysiz?” ni inglizcha yozing', answer: 'How are you?' },
      { promptUz: '“Rahmat” ni yozing', answer: 'Thank you', accept: ['Thanks', 'Thank you'] },
      { promptUz: '“Xayrli tong” ni yozing', answer: 'Good morning' },
    ],
    listening: [
      {
        audioText: 'Good morning',
        options: ['Good night', 'Good morning', 'Goodbye', 'See you'],
        answer: 1,
      },
      {
        audioText: 'How are you?',
        options: ['Who are you?', 'How are you?', 'Where are you?', 'How old are you?'],
        answer: 1,
      },
      {
        audioText: 'Nice to meet you',
        options: ['Nice to meet you', 'Need to meet you', 'Next to me too', 'Night to meet you'],
        answer: 0,
      },
      {
        audioText: 'See you later',
        options: ['See you later', 'Say you later', 'Sea you later', 'Sorry later'],
        answer: 0,
      },
    ],
    pronounce: [
      { text: 'Hello', tip: 'He-LOU — ikkinchi bo‘g‘in kuchliroq' },
      { text: 'Thank you', tip: 'th — til tish orasida' },
      { text: 'Please', tip: 'pliiz — uzun “ee”' },
      { text: 'How are you?', tip: 'How / are / you — oqimli ayting' },
      { text: 'Nice to meet you', tip: 'meet = miit' },
    ],
  },
  {
    id: 'family',
    num: 2,
    level: 'boshlangich',
    topic: 'mavzu',
    title: 'Oila',
    summary: 'Family a’zolari: mother, father, sister…',
    minutes: 18,
    tip: '“My mother” — mening onam. Ism oldidan “the” kerak emas.',
    words: [
      { en: 'Family', uz: 'Oila' },
      { en: 'Mother', uz: 'Ona', tip: 'Mom / Mum — norasmiy' },
      { en: 'Father', uz: 'Ota', tip: 'Dad — norasmiy' },
      { en: 'Sister', uz: 'Opa / singil' },
      { en: 'Brother', uz: 'Aka / uka' },
      { en: 'Parents', uz: 'Ota-ona' },
      { en: 'Child', uz: 'Bola' },
      { en: 'Children', uz: 'Bolalar' },
      { en: 'Husband', uz: 'Er' },
      { en: 'Wife', uz: 'Xotin' },
    ],
    phrases: [
      { en: 'This is my family.', uz: 'Bu mening oilam.' },
      { en: 'I have two sisters.', uz: 'Mening ikkita singlim/opam bor.' },
      { en: 'She is my mother.', uz: 'U mening onam.' },
      { en: 'He is my brother.', uz: 'U mening akam/ukam.' },
      { en: 'We live together.', uz: 'Biz birga yashaymiz.' },
    ],
    quiz: [
      {
        prompt: '“Ona” — qaysi so‘z?',
        options: ['Father', 'Sister', 'Mother', 'Brother'],
        answer: 2,
      },
      {
        prompt: '“Children” nima?',
        options: ['Bolalar', 'Ota-ona', 'Er', 'Oila'],
        answer: 0,
      },
      {
        prompt: '“This is my family.” — tarjimasi?',
        options: ['Bu mening ukam', 'Bu mening oilam', 'Men yolg‘izman', 'Ular do‘stim'],
        answer: 1,
      },
      {
        prompt: '“Wife” — tarjimasi?',
        options: ['Er', 'Xotin', 'Ona', 'Opa'],
        answer: 1,
      },
    ],
    reading: {
      title: 'My family photo',
      text: 'This is my family. My father is kind. My mother cooks dinner. I have one brother and one sister. We live together in a small house.',
      questions: [
        {
          prompt: 'Kim kechki ovqat pishiradi?',
          options: ['Father', 'Mother', 'Brother', 'Sister'],
          answer: 1,
        },
        {
          prompt: 'Nechta aka/uka bor?',
          options: ['0', '1', '2', '3'],
          answer: 1,
        },
        {
          prompt: 'Ular qayerda yashaydi?',
          options: ['Katta mehmonxonada', 'Kichik uyda', 'Maktabda', 'Avtobusda'],
          answer: 1,
        },
      ],
    },
    writing: [
      { promptUz: '“Ona” ni yozing', answer: 'Mother', accept: ['Mom', 'Mum'] },
      { promptUz: '“Bu mening oilam.” ni yozing', answer: 'This is my family.' },
      { promptUz: '“Bolalar” ni yozing', answer: 'Children' },
      { promptUz: '“U mening onam.” ni yozing', answer: 'She is my mother.' },
    ],
    listening: [
      {
        audioText: 'Mother',
        options: ['Brother', 'Mother', 'Father', 'Sister'],
        answer: 1,
      },
      {
        audioText: 'This is my family',
        options: ['This is my family', 'This is my funny', 'These are my bags', 'This is my father'],
        answer: 0,
      },
      {
        audioText: 'I have two sisters',
        options: ['I have two sisters', 'I have two cities', 'I hate two sisters', 'I have too sisters'],
        answer: 0,
      },
      {
        audioText: 'We live together',
        options: ['We leave together', 'We live together', 'We like together', 'We lift together'],
        answer: 1,
      },
    ],
    pronounce: [
      { text: 'Family', tip: 'FA-mi-li — birinchi bo‘g‘in' },
      { text: 'Mother', tip: 'th yumshoq' },
      { text: 'Brother', tip: 'bro-ther' },
      { text: 'Children', tip: 'CHIL-dren' },
      { text: 'This is my family', tip: 'This / is / my — bir tekis' },
    ],
  },
  {
    id: 'numbers',
    num: 3,
    level: 'boshlangich',
    topic: 'mavzu',
    title: 'Raqamlar',
    summary: '1 dan 20 gacha — one, two, twenty.',
    minutes: 20,
    tip: '13–19: thirteen… 20: twenty. “th” ni yumshoq ayting.',
    words: [
      { en: 'One', uz: '1' },
      { en: 'Two', uz: '2' },
      { en: 'Three', uz: '3' },
      { en: 'Four', uz: '4' },
      { en: 'Five', uz: '5' },
      { en: 'Six', uz: '6' },
      { en: 'Seven', uz: '7' },
      { en: 'Eight', uz: '8' },
      { en: 'Nine', uz: '9' },
      { en: 'Ten', uz: '10' },
      { en: 'Eleven', uz: '11' },
      { en: 'Twelve', uz: '12' },
      { en: 'Thirteen', uz: '13' },
      { en: 'Fifteen', uz: '15' },
      { en: 'Twenty', uz: '20' },
    ],
    phrases: [
      { en: 'How old are you?', uz: 'Yoshingiz nechida?' },
      { en: 'I am twenty.', uz: 'Men yigirma yoshdaman.' },
      { en: 'I have three apples.', uz: 'Menda uchta olma bor.' },
      { en: 'What time is it?', uz: 'Soat necha?' },
      { en: 'It is five o’clock.', uz: 'Soat besh.' },
    ],
    quiz: [
      { prompt: '“Eight” — qancha?', options: ['6', '7', '8', '9'], answer: 2 },
      { prompt: '15 — inglizcha?', options: ['Fifty', 'Fifteen', 'Five', 'Fourteen'], answer: 1 },
      {
        prompt: '“How old are you?” — nima?',
        options: ['Qayerdansiz?', 'Yoshingiz nechida?', 'Ismingiz nima?', 'Nechta?'],
        answer: 1,
      },
      { prompt: '20 — qaysi?', options: ['Twelve', 'Two', 'Twenty', 'Thirteen'], answer: 2 },
    ],
    reading: {
      title: 'At the shop',
      text: 'I buy five apples and two bottles of water. The shop opens at eight o’clock. I am twenty years old. Today I need fifteen minutes.',
      questions: [
        {
          prompt: 'Nechta olma?',
          options: ['2', '5', '8', '15'],
          answer: 1,
        },
        {
          prompt: 'Do‘kon soat nechida ochiladi?',
          options: ['Five', 'Eight', 'Twenty', 'Fifteen'],
          answer: 1,
        },
        {
          prompt: '“fifteen minutes” nima?',
          options: ['15 daqiqa', '50 daqiqa', '5 soat', '15 yosh'],
          answer: 0,
        },
      ],
    },
    writing: [
      { promptUz: '8 ni so‘z bilan yozing', answer: 'Eight' },
      { promptUz: '“Yoshingiz nechida?” ni yozing', answer: 'How old are you?' },
      { promptUz: '20 ni so‘z bilan yozing', answer: 'Twenty' },
      { promptUz: '“Soat besh.” ni yozing', answer: "It is five o'clock.", accept: ['It is five oclock', 'It is five o’clock.'] },
    ],
    listening: [
      { audioText: 'Fifteen', options: ['Fifty', 'Fifteen', 'Five', 'Fourteen'], answer: 1 },
      { audioText: 'Twenty', options: ['Twelve', 'Twenty', 'Two', 'Thirty'], answer: 1 },
      {
        audioText: 'How old are you?',
        options: ['How old are you?', 'How are you?', 'Who are you?', 'How far are you?'],
        answer: 0,
      },
      {
        audioText: 'I have three apples',
        options: ['I have free apples', 'I have three apples', 'I hate three apples', 'I have tree apples'],
        answer: 1,
      },
    ],
    pronounce: [
      { text: 'Three', tip: 'th — til tishda' },
      { text: 'Eight', tip: 'eit — “gh” o‘qilmaydi' },
      { text: 'Thirteen', tip: 'thir-TEEN' },
      { text: 'Fifteen', tip: 'fif-TEEN' },
      { text: 'Twenty', tip: 'TWEN-ti' },
    ],
  },
  {
    id: 'colors',
    num: 4,
    level: 'boshlangich',
    topic: 'mavzu',
    title: 'Ranglar',
    summary: 'Red, blue, green va boshqa asosiy ranglar.',
    minutes: 16,
    tip: 'Rang ot oldida: a red car, a blue bag.',
    words: [
      { en: 'Red', uz: 'Qizil' },
      { en: 'Blue', uz: 'Ko‘k' },
      { en: 'Green', uz: 'Yashil' },
      { en: 'Yellow', uz: 'Sariq' },
      { en: 'Black', uz: 'Qora' },
      { en: 'White', uz: 'Oq' },
      { en: 'Orange', uz: 'To‘q sariq / apelsin' },
      { en: 'Brown', uz: 'Jigarrang' },
      { en: 'Pink', uz: 'Pushti' },
      { en: 'Gray', uz: 'Kulrang', tip: 'UK: grey' },
    ],
    phrases: [
      { en: 'What color is it?', uz: 'Bu qanday rang?' },
      { en: 'It is blue.', uz: 'Bu ko‘k.' },
      { en: 'I like green.', uz: 'Men yashilni yoqtiraman.' },
      { en: 'My favorite color is red.', uz: 'Sevimli rangim — qizil.' },
      { en: 'A black cat.', uz: 'Qora mushuk.' },
    ],
    quiz: [
      { prompt: '“Yashil” — qaysi?', options: ['Green', 'Gray', 'Yellow', 'Brown'], answer: 0 },
      {
        prompt: '“What color is it?” — tarjimasi?',
        options: ['Bu nima?', 'Bu qanday rang?', 'Qancha turadi?', 'Qayerda?'],
        answer: 1,
      },
      { prompt: '“White” — nima?', options: ['Qora', 'Oq', 'Ko‘k', 'Pushti'], answer: 1 },
      {
        prompt: '“I like green.” — to‘g‘ri tarjima?',
        options: ['Men yashilman', 'Men yashilni yoqtiraman', 'Yashil yo‘q', 'Bu yashil emas'],
        answer: 1,
      },
    ],
    reading: {
      title: 'Color day',
      text: 'Today is color day at school. Anna wears a red dress. Tom has a blue bag. The teacher asks, “What color is it?” The class says, “It is yellow!”',
      questions: [
        {
          prompt: 'Anna nima kiygan?',
          options: ['Blue bag', 'Red dress', 'Yellow hat', 'Black shoes'],
          answer: 1,
        },
        {
          prompt: 'O‘qituvchi nima so‘raydi?',
          options: ['How are you?', 'What color is it?', 'Where is it?', 'Who is it?'],
          answer: 1,
        },
        {
          prompt: 'Sinf nima deb javob beradi?',
          options: ['It is yellow', 'It is green', 'It is black', 'It is pink'],
          answer: 0,
        },
      ],
    },
    writing: [
      { promptUz: '“Qizil” ni yozing', answer: 'Red' },
      { promptUz: '“Bu qanday rang?” ni yozing', answer: 'What color is it?' },
      { promptUz: '“Men yashilni yoqtiraman.” ni yozing', answer: 'I like green.' },
      { promptUz: '“Qora mushuk.” ni yozing', answer: 'A black cat.' },
    ],
    listening: [
      { audioText: 'Green', options: ['Gray', 'Green', 'Brown', 'Cream'], answer: 1 },
      {
        audioText: 'What color is it?',
        options: ['What color is it?', 'What collar is it?', 'What cooler is it?', 'What color sit?'],
        answer: 0,
      },
      {
        audioText: 'My favorite color is red',
        options: [
          'My favorite color is red',
          'My favorite collar is red',
          'My family color is red',
          'My favorite color is read',
        ],
        answer: 0,
      },
      { audioText: 'A black cat', options: ['A black cat', 'A back cat', 'A black car', 'A blue cat'], answer: 0 },
    ],
    pronounce: [
      { text: 'Yellow', tip: 'YE-low' },
      { text: 'Orange', tip: 'O-rinj' },
      { text: 'Purple', tip: 'PUR-pl (bonus)' },
      { text: 'What color is it?', tip: 'color = KA-ler' },
      { text: 'Favorite', tip: 'FAY-vrit' },
    ],
  },
  {
    id: 'food',
    num: 5,
    level: 'boshlangich',
    topic: 'mavzu',
    title: 'Ovqat',
    summary: 'Non, suv, meva — cafe va uyda gaplar.',
    minutes: 18,
    tip: 'Buyurtma: “I’d like …” yoki “Can I have …, please?”',
    words: [
      { en: 'Water', uz: 'Suv' },
      { en: 'Bread', uz: 'Non' },
      { en: 'Tea', uz: 'Choy' },
      { en: 'Coffee', uz: 'Qahva' },
      { en: 'Apple', uz: 'Olma' },
      { en: 'Rice', uz: 'Guruch' },
      { en: 'Meat', uz: 'Go‘sht' },
      { en: 'Soup', uz: 'Sho‘rva' },
      { en: 'Breakfast', uz: 'Nonushta' },
      { en: 'Dinner', uz: 'Kechki ovqat' },
    ],
    phrases: [
      { en: 'I am hungry.', uz: 'Men ochman.' },
      { en: 'I am thirsty.', uz: 'Men chanqaganman.' },
      { en: 'Can I have tea, please?', uz: 'Choy olsam bo‘ladimi?' },
      { en: 'This is delicious.', uz: 'Bu juda mazali.' },
      { en: 'I don’t eat meat.', uz: 'Men go‘sht yemayman.' },
    ],
    quiz: [
      { prompt: '“Bread” — nima?', options: ['Suv', 'Non', 'Choy', 'Olma'], answer: 1 },
      {
        prompt: '“I am hungry.” — tarjimasi?',
        options: ['Men chanqaganman', 'Men ochman', 'Men charchadim', 'Men yaxshiman'],
        answer: 1,
      },
      {
        prompt: 'Cafe da choy so‘rash:',
        options: ['Goodbye tea', 'Can I have tea, please?', 'Tea is mother', 'What color tea?'],
        answer: 1,
      },
      { prompt: '“Delicious” — yaqin ma’no?', options: ['Qimmat', 'Mazali', 'Issiq', 'Katta'], answer: 1 },
    ],
    reading: {
      title: 'Lunch time',
      text: 'I am hungry. For lunch I eat rice and soup. I drink water. “Can I have tea, please?” asks my friend. “This is delicious!” she says.',
      questions: [
        {
          prompt: 'Ovqatlanishda nima ichadi?',
          options: ['Coffee', 'Water', 'Milk', 'Juice'],
          answer: 1,
        },
        {
          prompt: 'Do‘st nima so‘raydi?',
          options: ['Meat', 'Tea', 'Bread', 'Apple'],
          answer: 1,
        },
        {
          prompt: '“Delicious” bu yerda nima?',
          options: ['Yomon', 'Mazali', 'Qimmat', 'Sovuq'],
          answer: 1,
        },
      ],
    },
    writing: [
      { promptUz: '“Suv” ni yozing', answer: 'Water' },
      { promptUz: '“Men ochman.” ni yozing', answer: 'I am hungry.' },
      {
        promptUz: '“Choy olsam bo‘ladimi?” ni yozing',
        answer: 'Can I have tea, please?',
      },
      { promptUz: '“Bu juda mazali.” ni yozing', answer: 'This is delicious.' },
    ],
    listening: [
      { audioText: 'Breakfast', options: ['Breakfast', 'Basket', 'Break fast', 'Brother'], answer: 0 },
      {
        audioText: 'I am thirsty',
        options: ['I am thirsty', 'I am thirty', 'I am Thursday', 'I am dirty'],
        answer: 0,
      },
      {
        audioText: 'Can I have tea, please?',
        options: [
          'Can I have tea, please?',
          'Can I have tree, please?',
          'Can I hate tea, please?',
          'Can I have key, please?',
        ],
        answer: 0,
      },
      {
        audioText: 'This is delicious',
        options: ['This is delicious', 'This is the dishes', 'This is decision', 'This is delusion'],
        answer: 0,
      },
    ],
    pronounce: [
      { text: 'Water', tip: 'WO-ter (US)' },
      { text: 'Hungry', tip: 'HUNG-gri' },
      { text: 'Thirsty', tip: 'THUR-sti' },
      { text: 'Delicious', tip: 'di-LI-shus' },
      { text: 'Can I have tea, please?', tip: 'please oxirida yumshoq' },
    ],
  },
  {
    id: 'daily',
    num: 6,
    level: 'ortacha',
    topic: 'mavzu',
    title: 'Kunlik gaplar',
    summary: 'Uyda, yo‘lda, do‘konda kerakli iboralar.',
    minutes: 20,
    tip: 'Har kuni 3–5 ta gapni baland ovozda takrorlang.',
    words: [
      { en: 'Home', uz: 'Uy' },
      { en: 'Work', uz: 'Ish' },
      { en: 'School', uz: 'Maktab' },
      { en: 'Today', uz: 'Bugun' },
      { en: 'Tomorrow', uz: 'Ertaga' },
      { en: 'Yesterday', uz: 'Kecha' },
      { en: 'Now', uz: 'Hozir' },
      { en: 'Later', uz: 'Keyinroq' },
      { en: 'Help', uz: 'Yordam' },
      { en: 'Money', uz: 'Pul' },
    ],
    phrases: [
      { en: 'Where is the bathroom?', uz: 'Hojatxona qayerda?' },
      { en: 'How much is this?', uz: 'Bu qancha turadi?' },
      { en: 'I don’t understand.', uz: 'Men tushunmadim.' },
      { en: 'Can you help me?', uz: 'Yordam bera olasizmi?' },
      { en: 'I need a taxi.', uz: 'Menga taksi kerak.' },
      { en: 'See you tomorrow.', uz: 'Ertaga ko‘rishamiz.' },
    ],
    quiz: [
      {
        prompt: '“How much is this?” — nima?',
        options: ['Bu qancha turadi?', 'Bu nima?', 'Qayerdansiz?', 'Yordam kerakmi?'],
        answer: 0,
      },
      {
        prompt: '“I don’t understand.” — tarjimasi?',
        options: ['Men bilaman', 'Men tushunmadim', 'Men keldim', 'Men ketaman'],
        answer: 1,
      },
      { prompt: '“Tomorrow” — nima?', options: ['Bugun', 'Kecha', 'Ertaga', 'Hozir'], answer: 2 },
      {
        prompt: 'Yordam so‘rash:',
        options: ['Can you help me?', 'I am blue', 'Good morning money', 'See you bathroom'],
        answer: 0,
      },
    ],
    reading: {
      title: 'In the city',
      text: 'I need a taxi now. “How much is this?” I ask in a shop. I don’t understand the answer. “Can you help me?” A kind man says, “See you tomorrow at school.”',
      questions: [
        {
          prompt: 'Hozir nima kerak?',
          options: ['Taxi', 'School', 'Money only', 'Bathroom'],
          answer: 0,
        },
        {
          prompt: 'Do‘konda qanday savol?',
          options: ['Where is home?', 'How much is this?', 'Who are you?', 'What time?'],
          answer: 1,
        },
        {
          prompt: 'Erkak nima deydi?',
          options: ['Goodbye forever', 'See you tomorrow at school', 'I need a taxi', 'I don’t understand'],
          answer: 1,
        },
      ],
    },
    writing: [
      { promptUz: '“Ertaga” ni yozing', answer: 'Tomorrow' },
      { promptUz: '“Bu qancha turadi?” ni yozing', answer: 'How much is this?' },
      { promptUz: '“Men tushunmadim.” ni yozing', answer: "I don't understand.", accept: ['I do not understand.'] },
      { promptUz: '“Yordam bera olasizmi?” ni yozing', answer: 'Can you help me?' },
    ],
    listening: [
      {
        audioText: 'Where is the bathroom?',
        options: [
          'Where is the bathroom?',
          'Where is the bedroom?',
          'Wear is the bathroom?',
          'Where is the bath room now?',
        ],
        answer: 0,
      },
      {
        audioText: 'How much is this?',
        options: ['How much is this?', 'How many is this?', 'How match is this?', 'How much it is?'],
        answer: 0,
      },
      {
        audioText: "I don't understand",
        options: ["I don't understand", 'I do under stand', 'I won’t understand', 'I don’t stand under'],
        answer: 0,
      },
      {
        audioText: 'See you tomorrow',
        options: ['See you tomorrow', 'Sea you tomorrow', 'See your tomorrow', 'Say you tomorrow'],
        answer: 0,
      },
    ],
    pronounce: [
      { text: 'Tomorrow', tip: 'to-MO-row' },
      { text: 'Bathroom', tip: 'BATH-room' },
      { text: "I don't understand", tip: "don't = dont" },
      { text: 'Can you help me?', tip: 'help — aniq “p”' },
      { text: 'How much is this?', tip: 'much — “ch”' },
    ],
  },
  {
    id: 'questions',
    num: 7,
    level: 'ortacha',
    topic: 'mavzu',
    title: 'So‘roq so‘zlari',
    summary: 'What, Where, Who, When, Why, How.',
    minutes: 20,
    tip: 'So‘roqda yordamchi fe’l oldinga: Where are you?',
    words: [
      { en: 'What', uz: 'Nima' },
      { en: 'Where', uz: 'Qayerda' },
      { en: 'Who', uz: 'Kim' },
      { en: 'When', uz: 'Qachon' },
      { en: 'Why', uz: 'Nima uchun' },
      { en: 'How', uz: 'Qanday' },
      { en: 'Which', uz: 'Qaysi' },
      { en: 'Whose', uz: 'Kimniki' },
    ],
    phrases: [
      { en: 'Where do you live?', uz: 'Qayerda yashaysiz?' },
      { en: 'What do you do?', uz: 'Nima ish qilasiz?' },
      { en: 'When is the meeting?', uz: 'Uchrashuv qachon?' },
      { en: 'Why are you late?', uz: 'Nima uchun kechikdingiz?' },
      { en: 'How do you go to work?', uz: 'Ishga qanday borasiz?' },
      { en: 'Who is this?', uz: 'Bu kim?' },
    ],
    quiz: [
      { prompt: '“Qayerda” — qaysi?', options: ['What', 'Where', 'When', 'Why'], answer: 1 },
      {
        prompt: '“Who is this?” — tarjimasi?',
        options: ['Bu nima?', 'Bu kim?', 'Qachon?', 'Nima uchun?'],
        answer: 1,
      },
      { prompt: '“When” — ma’nosi?', options: ['Qachon', 'Qanday', 'Kimniki', 'Qaysi'], answer: 0 },
      {
        prompt: '“Where do you live?” — to‘g‘ri tarjima?',
        options: ['Nima ish qilasiz?', 'Qayerda yashaysiz?', 'Kim bilan yashaysiz?', 'Qachon kelasiz?'],
        answer: 1,
      },
    ],
    reading: {
      title: 'Interview',
      text: '“What do you do?” “I am a teacher.” “Where do you live?” “In Tashkent.” “When is the meeting?” “At five.” “Why are you late?” “The bus was slow.”',
      questions: [
        {
          prompt: 'U nima ish qiladi?',
          options: ['Driver', 'Teacher', 'Doctor', 'Student'],
          answer: 1,
        },
        {
          prompt: 'Qayerda yashaydi?',
          options: ['Samarkand', 'Tashkent', 'Bukhara', 'London'],
          answer: 1,
        },
        {
          prompt: 'Nima uchun kechikkan?',
          options: ['Taxi yo‘q', 'Avtobus sekin edi', 'Uchrashuv yo‘q', 'Uy uzoq'],
          answer: 1,
        },
      ],
    },
    writing: [
      { promptUz: '“Qayerda” ni yozing', answer: 'Where' },
      { promptUz: '“Bu kim?” ni yozing', answer: 'Who is this?' },
      { promptUz: '“Qayerda yashaysiz?” ni yozing', answer: 'Where do you live?' },
      { promptUz: '“Nima uchun kechikdingiz?” ni yozing', answer: 'Why are you late?' },
    ],
    listening: [
      { audioText: 'Where', options: ['Wear', 'Where', 'Were', 'Wire'], answer: 1 },
      {
        audioText: 'What do you do?',
        options: ['What do you do?', 'What did you do?', 'What do you dual?', 'Watch do you do?'],
        answer: 0,
      },
      {
        audioText: 'Why are you late?',
        options: ['Why are you late?', 'Why are you light?', 'Where are you late?', 'Who are you late?'],
        answer: 0,
      },
      {
        audioText: 'Who is this?',
        options: ['Who is this?', 'How is this?', 'Whose is this?', 'Who is these?'],
        answer: 0,
      },
    ],
    pronounce: [
      { text: 'What', tip: 'wot (qisqa a)' },
      { text: 'Where', tip: 'weir — “h” yo‘q' },
      { text: 'Why', tip: 'way' },
      { text: 'Where do you live?', tip: 'do you — birga' },
      { text: 'Why are you late?', tip: 'late — uzun “ay”' },
    ],
  },
]

export const LESSONS: Lesson[] = [...THEME_LESSONS, ...TENSE_LESSONS]
