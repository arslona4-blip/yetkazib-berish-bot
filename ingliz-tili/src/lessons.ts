export type Level = 'boshlangich' | 'ortacha'

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

export type Lesson = {
  id: string
  num: number
  level: Level
  title: string
  summary: string
  minutes: number
  tip: string
  words: Word[]
  phrases: Phrase[]
  quiz: QuizItem[]
}

export const LEVEL_LABEL: Record<Level, string> = {
  boshlangich: 'Boshlang‘ich',
  ortacha: 'O‘rta',
}

export const LESSONS: Lesson[] = [
  {
    id: 'greetings',
    num: 1,
    level: 'boshlangich',
    title: 'Salomlashish',
    summary: 'Hello, Good morning va kundalik salomlar.',
    minutes: 8,
    tip: 'Ingliz tilida salomlashganda odatda tabassum va to‘g‘ri ko‘z bilan qarash muhim.',
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
  },
  {
    id: 'family',
    num: 2,
    level: 'boshlangich',
    title: 'Oila',
    summary: 'Family a’zolari: mother, father, sister…',
    minutes: 8,
    tip: '“My mother” — mening onam. Ingliz tilida “the” odatda ism oldidan qo‘yilmaydi.',
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
        options: [
          'Bu mening ukam',
          'Bu mening oilam',
          'Men yolg‘izman',
          'Ular do‘stim',
        ],
        answer: 1,
      },
      {
        prompt: '“Wife” — tarjimasi?',
        options: ['Er', 'Xotin', 'Ona', 'Opa'],
        answer: 1,
      },
    ],
  },
  {
    id: 'numbers',
    num: 3,
    level: 'boshlangich',
    title: 'Raqamlar',
    summary: '1 dan 20 gacha — one, two, twenty.',
    minutes: 10,
    tip: '13–19: thirteen, fourteen… 20: twenty. “th” tovushini yumshoq ayting.',
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
      {
        prompt: '“Eight” — qancha?',
        options: ['6', '7', '8', '9'],
        answer: 2,
      },
      {
        prompt: '15 — inglizcha?',
        options: ['Fifty', 'Fifteen', 'Five', 'Fourteen'],
        answer: 1,
      },
      {
        prompt: '“How old are you?” — nima?',
        options: [
          'Qayerdansiz?',
          'Yoshingiz nechida?',
          'Ismingiz nima?',
          'Nechta?',
        ],
        answer: 1,
      },
      {
        prompt: '20 — qaysi?',
        options: ['Twelve', 'Two', 'Twenty', 'Thirteen'],
        answer: 2,
      },
    ],
  },
  {
    id: 'colors',
    num: 4,
    level: 'boshlangich',
    title: 'Ranglar',
    summary: 'Red, blue, green va boshqa asosiy ranglar.',
    minutes: 7,
    tip: 'Rang sifat sifatida ot oldida: a red car, a blue bag.',
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
      {
        prompt: '“Yashil” — qaysi?',
        options: ['Green', 'Gray', 'Yellow', 'Brown'],
        answer: 0,
      },
      {
        prompt: '“What color is it?” — tarjimasi?',
        options: [
          'Bu nima?',
          'Bu qanday rang?',
          'Qancha turadi?',
          'Qayerda?',
        ],
        answer: 1,
      },
      {
        prompt: '“White” — nima?',
        options: ['Qora', 'Oq', 'Ko‘k', 'Pushti'],
        answer: 1,
      },
      {
        prompt: '“I like green.” — to‘g‘ri tarjima?',
        options: [
          'Men yashilman',
          'Men yashilni yoqtiraman',
          'Yashil yo‘q',
          'Bu yashil emas',
        ],
        answer: 1,
      },
    ],
  },
  {
    id: 'food',
    num: 5,
    level: 'boshlangich',
    title: 'Ovqat',
    summary: 'Non, suv, meva — cafe va uyda gaplar.',
    minutes: 9,
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
      {
        prompt: '“Bread” — nima?',
        options: ['Suv', 'Non', 'Choy', 'Olma'],
        answer: 1,
      },
      {
        prompt: '“I am hungry.” — tarjimasi?',
        options: ['Men chanqaganman', 'Men ochman', 'Men charchadim', 'Men yaxshiman'],
        answer: 1,
      },
      {
        prompt: 'Cafe da choy so‘rash:',
        options: [
          'Goodbye tea',
          'Can I have tea, please?',
          'Tea is mother',
          'What color tea?',
        ],
        answer: 1,
      },
      {
        prompt: '“Delicious” — yaqin ma’no?',
        options: ['Qimmat', 'Mazali', 'Issiq', 'Katta'],
        answer: 1,
      },
    ],
  },
  {
    id: 'daily',
    num: 6,
    level: 'ortacha',
    title: 'Kunlik gaplar',
    summary: 'Uyda, yo‘lda, do‘konda kerakli iboralar.',
    minutes: 10,
    tip: 'Har kuni 3–5 ta gapni baland ovozda takrorlang — talaffuz tez yaxshilanadi.',
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
        options: [
          'Bu qancha turadi?',
          'Bu nima?',
          'Qayerdansiz?',
          'Yordam kerakmi?',
        ],
        answer: 0,
      },
      {
        prompt: '“I don’t understand.” — tarjimasi?',
        options: [
          'Men bilaman',
          'Men tushunmadim',
          'Men keldim',
          'Men ketaman',
        ],
        answer: 1,
      },
      {
        prompt: '“Tomorrow” — nima?',
        options: ['Bugun', 'Kecha', 'Ertaga', 'Hozir'],
        answer: 2,
      },
      {
        prompt: 'Yordam so‘rash:',
        options: [
          'Can you help me?',
          'I am blue',
          'Good morning money',
          'See you bathroom',
        ],
        answer: 0,
      },
    ],
  },
  {
    id: 'questions',
    num: 7,
    level: 'ortacha',
    title: 'So‘roq so‘zlari',
    summary: 'What, Where, Who, When, Why, How.',
    minutes: 10,
    tip: 'So‘roq gapda yordamchi fe’l oldinga chiqadi: Where are you? What do you do?',
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
      {
        prompt: '“Qayerda” — qaysi?',
        options: ['What', 'Where', 'When', 'Why'],
        answer: 1,
      },
      {
        prompt: '“Who is this?” — tarjimasi?',
        options: ['Bu nima?', 'Bu kim?', 'Qachon?', 'Nima uchun?'],
        answer: 1,
      },
      {
        prompt: '“When” — ma’nosi?',
        options: ['Qachon', 'Qanday', 'Kimniki', 'Qaysi'],
        answer: 0,
      },
      {
        prompt: '“Where do you live?” — to‘g‘ri tarjima?',
        options: [
          'Nima ish qilasiz?',
          'Qayerda yashaysiz?',
          'Kim bilan yashaysiz?',
          'Qachon kelasiz?',
        ],
        answer: 1,
      },
    ],
  },
  {
    id: 'present',
    num: 8,
    level: 'ortacha',
    title: 'Present Simple',
    summary: 'I work, she works — kundalik odatlar.',
    minutes: 12,
    tip: 'He/She/It uchun fe’lga -s: she works, he likes. Inkor: don’t / doesn’t.',
    words: [
      { en: 'I work', uz: 'Men ishlayman' },
      { en: 'She works', uz: 'U ishlaydi' },
      { en: 'We study', uz: 'Biz o‘qiymiz' },
      { en: 'He likes', uz: 'U yoqtiradi' },
      { en: 'They play', uz: 'Ular o‘ynaydi' },
      { en: 'Do you…?', uz: '…misiz?' },
      { en: 'Does she…?', uz: 'U …mi?' },
      { en: 'I don’t', uz: 'Men …mayman' },
      { en: 'She doesn’t', uz: 'U …maydi' },
      { en: 'Every day', uz: 'Har kuni' },
    ],
    phrases: [
      { en: 'I work every day.', uz: 'Men har kuni ishlayman.' },
      { en: 'She likes tea.', uz: 'U choy yoqtiradi.' },
      { en: 'Do you speak English?', uz: 'Inglizcha gapirasizmi?' },
      { en: 'Yes, I do. / No, I don’t.', uz: 'Ha. / Yo‘q.' },
      { en: 'He doesn’t live here.', uz: 'U bu yerda yashamaydi.' },
      { en: 'We study English.', uz: 'Biz ingliz tilini o‘rganamiz.' },
    ],
    quiz: [
      {
        prompt: 'To‘g‘ri variant:',
        options: ['She work', 'She works', 'She working', 'She worked every'],
        answer: 1,
        hint: 'he/she/it → -s',
      },
      {
        prompt: '“Do you speak English?” — javob (ha):',
        options: ['Yes, I am', 'Yes, I do', 'Yes, I speak', 'Yes, does'],
        answer: 1,
      },
      {
        prompt: 'Inkor (u):',
        options: [
          'He don’t live here',
          'He doesn’t live here',
          'He no live here',
          'He not lives',
        ],
        answer: 1,
      },
      {
        prompt: '“We study English.” — tarjimasi?',
        options: [
          'Biz inglizcha gapiramiz',
          'Biz ingliz tilini o‘rganamiz',
          'Ular o‘qiydi',
          'Men ishlayman',
        ],
        answer: 1,
      },
    ],
  },
]
