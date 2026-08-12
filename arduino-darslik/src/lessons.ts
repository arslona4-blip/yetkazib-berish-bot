export type LessonLevel = 'boshlangich' | 'ortacha' | 'loyiha'

export type SimKind =
  | 'intro'
  | 'blink'
  | 'traffic'
  | 'pwm'
  | 'serial'
  | 'vars'
  | 'ifel'

export type LessonStep = {
  title: string
  detail: string
}

export type Task = {
  n: number
  title: string
  text: string
  code: string
}

export type Lesson = {
  id: string
  num: number
  level: LessonLevel
  title: string
  minutes: number
  summary: string
  goals: string[]
  parts: string[]
  wiring: string[]
  steps: LessonStep[]
  practice: string[]
  code: string
  tip: string
  sim: SimKind
  tasks: Task[]
}

export const LEVEL_LABEL: Record<LessonLevel, string> = {
  boshlangich: 'Boshlang‘ich',
  ortacha: 'O‘rta',
  loyiha: 'Amaliyot',
}

export const LESSONS: Lesson[] = [
  {
    id: 'dars1',
    num: 1,
    level: 'boshlangich',
    title: '1-dars. Arduino, maket, LED',
    minutes: 45,
    summary:
      'Arduino, maket plata va LED komponentlari bilan tanishish. LED ni yoqib-o‘chirish. 7 ta topshiriq.',
    goals: [
      'Arduino Uno/Nano nima ekanini bilish',
      'Maket plata (breadboard) qatorlarini tushunish',
      'LED + 220Ω rezistor ulash',
      'digitalWrite / delay bilan LED boshqarish',
    ],
    parts: [
      'Arduino Uno yoki Nano',
      'USB kabel',
      'Maket plata (breadboard)',
      'LED lar (2–8 dona)',
      '220Ω rezistorlar',
      'Ulanuvchi simlar',
    ],
    wiring: [
      'LED anod (uzun oyoq) → rezistor → Arduino pin',
      'LED katod (qisqa oyoq) → GND',
      'Maketda bir qator — bir ulanish; o‘rtadagi bo‘shliq ikki tomonni ajratadi',
      '5V va GND ni maketning + / − chiziqlariga ulash qulay',
    ],
    steps: [
      {
        title: 'Arduino nima?',
        detail:
          'Arduino — kichik kompyuter-plata. Unda dastur yozib, LED, sensor, motor kabi qismlarni boshqarasiz. Asosiy pinlar: digital (2–13), PWM (~), analog (A0–A5), 5V, GND, VIN.',
      },
      {
        title: 'Maket plata',
        detail:
          'Breadboard — lehimlamasdan ulash. Yon uzun chiziqlar odatda + (qizil) va − (ko‘k/qora). O‘rtada a–e va f–j qatorlari: bir raqamli qator ichida teshiklar bir-biriga ulangan. Markazdagi bo‘shliq ikki yarimni ajratadi.',
      },
      {
        title: 'LED komponenti',
        detail:
          'LED — yorug‘lik diodi. Uzun oyoq = anod (+), qisqa = katod (−). Har doim 220Ω (yoki 150–330Ω) rezistor bilan ulang — aks holda LED yonishi mumkin. Tok yo‘nalishi: pin → rezistor → anod → katod → GND.',
      },
      {
        title: 'Arduino IDE',
        detail:
          'https://www.arduino.cc/en/software dan IDE ni o‘rnating. Tools → Board (Uno/Nano), Tools → Port (COMx / /dev/tty…). File → New → kod yozing → Upload. “Done uploading” — muvaffaqiyat.',
      },
      {
        title: 'LED ni yoqib-o‘chirish (asos)',
        detail:
          'setup() da pinMode(pin, OUTPUT). loop() da digitalWrite(pin, HIGH) — yonadi, digitalWrite(pin, LOW) — o‘chadi, delay(ms) — kutish. Masalan pin 13 ichki LED.',
      },
      {
        title: 'Amaliy: bir LED',
        detail:
          'Pin 13 (yoki 5) ga LED+rezistor ulang. Pastdagi asosiy kodni yuklang. Keyin topshiriqlarga o‘ting — har birida tayyor yechim bor.',
      },
    ],
    practice: [
      'Maketda 1 ta LED ni pin 13 ga ulang va Blink qiling',
      'delay ni 200 va 1000 qilib solishtiring',
      'Topshiriq 1–7 ni ketma-ket bajaring',
    ],
    code: `// Asos: 1 ta LED (masalan pin 13)
void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  digitalWrite(13, HIGH); // yonadi
  delay(1000);            // 1 soniya
  digitalWrite(13, LOW);  // o'chadi
  delay(1000);
}`,
    tip: 'Avval 1 LED ni ishlatib oling, keyin topshiriqlarda ko‘paytiring.',
    sim: 'intro',
    tasks: [
      {
        n: 1,
        title: '2 LED ketma-ket (5 va 6)',
        text: '2 ta LED ni 5 va 6-pinlarga ulang. 1 soniya bilan navbatma-navbat yoqib-o‘chiring.',
        code: `void setup() {
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
}

void loop() {
  digitalWrite(5, HIGH);
  delay(1000);
  digitalWrite(5, LOW);
  digitalWrite(6, HIGH);
  delay(1000);
  digitalWrite(6, LOW);
}`,
      },
      {
        n: 2,
        title: '2 LED parallel (birga)',
        text: 'Pin 5 va 6 dagi LED lar bir vaqtda yonsin va birga o‘chsin (1 soniya).',
        code: `void setup() {
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
}

void loop() {
  digitalWrite(5, HIGH);
  digitalWrite(6, HIGH);
  delay(1000);
  digitalWrite(5, LOW);
  digitalWrite(6, LOW);
  delay(1000);
}`,
      },
      {
        n: 3,
        title: '3 LED parallel (2,3,4)',
        text: 'Pin 2,3,4 — uchala LED 2 soniyadan parallel yonib-o‘chsin.',
        code: `void setup() {
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
}

void loop() {
  digitalWrite(2, HIGH);
  digitalWrite(3, HIGH);
  digitalWrite(4, HIGH);
  delay(2000);
  digitalWrite(2, LOW);
  digitalWrite(3, LOW);
  digitalWrite(4, LOW);
  delay(2000);
}`,
      },
      {
        n: 4,
        title: '4 LED parallel (2–5)',
        text: 'Pin 2,3,4,5 — to‘rtala LED 1 soniyadan parallel yonib-o‘chsin.',
        code: `void setup() {
  for (int p = 2; p <= 5; p++) pinMode(p, OUTPUT);
}

void loop() {
  for (int p = 2; p <= 5; p++) digitalWrite(p, HIGH);
  delay(1000);
  for (int p = 2; p <= 5; p++) digitalWrite(p, LOW);
  delay(1000);
}`,
      },
      {
        n: 5,
        title: '3 LED turli vaqt',
        text: '1-chi: 2s yonib, 1s o‘chadi. 2-chi: 1s yonib, 3s o‘chadi. 3-chi: 0.5s yonib, 2.5s o‘chadi. (Umumiy sikl 3s — moslashtirilgan misol)',
        code: `// Pin: 2, 3, 4 — 3 soniyalik umumiy sikl
void setup() {
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
}

void loop() {
  // t=0..500ms: 1 va 3 yonadi, 2 o'chiq
  digitalWrite(2, HIGH);
  digitalWrite(3, LOW);
  digitalWrite(4, HIGH);
  delay(500);
  // t=500..1000: faqat 1 yonadi
  digitalWrite(4, LOW);
  delay(500);
  // t=1000..2000: 1 o'chadi, 2 yonadi
  digitalWrite(2, LOW);
  digitalWrite(3, HIGH);
  delay(1000);
  // t=2000..3000: hammasi o'chiq (1 qolgan 1s o'chiq, 2 qolgan 2s, 3 qolgan)
  digitalWrite(3, LOW);
  delay(1000);
}`,
      },
      {
        n: 6,
        title: '8 LED — chetdan markazga',
        text: '8 LED tartib bilan. Avval 1, keyin 8, keyin 2, 7, 3, 6, 4, 5 — har biri yonib-o‘chadi.',
        code: `int leds[] = {2, 3, 4, 5, 6, 7, 8, 9}; // 1..8-chi LED
int order[] = {0, 7, 1, 6, 2, 5, 3, 4}; // 1-8,2-7,3-6,4-5

void setup() {
  for (int i = 0; i < 8; i++) pinMode(leds[i], OUTPUT);
}

void loop() {
  for (int i = 0; i < 8; i++) {
    int p = leds[order[i]];
    digitalWrite(p, HIGH);
    delay(300);
    digitalWrite(p, LOW);
    delay(150);
  }
}`,
      },
      {
        n: 7,
        title: '8 LED — n marta miltillash',
        text: '1-LED 1 marta, 2-LED 2 marta, … 8-LED 8 marta yonib-o‘chadi.',
        code: `int leds[] = {2, 3, 4, 5, 6, 7, 8, 9};

void setup() {
  for (int i = 0; i < 8; i++) pinMode(leds[i], OUTPUT);
}

void loop() {
  for (int i = 0; i < 8; i++) {
    for (int k = 0; k <= i; k++) { // i=0 → 1 marta
      digitalWrite(leds[i], HIGH);
      delay(150);
      digitalWrite(leds[i], LOW);
      delay(150);
    }
    delay(400);
  }
}`,
      },
    ],
  },
  {
    id: 'dars2',
    num: 2,
    level: 'boshlangich',
    title: '2-dars. Svetofor (3 LED)',
    minutes: 35,
    summary: '3 ta LED ni svetofor tartibida yoqish — to‘liq kod va simulyator.',
    goals: [
      '3 pinni birga boshqarish',
      'Vaqt ketma-ketligi (qizil → sariq → yashil)',
      'Funksiya yozish (setLights)',
    ],
    parts: ['Arduino', 'Qizil, sariq, yashil LED', '3×220Ω', 'Maket', 'Ulanuvchi simlar'],
    wiring: [
      'Qizil → pin 11 (+rezistor)',
      'Sariq → pin 12',
      'Yashil → pin 13',
      'Har bir katod → GND',
    ],
    steps: [
      {
        title: 'Ulanish',
        detail: '3 LED ni maketga joylang. Har biriga 220Ω. Pin 11/12/13 va umumiy GND.',
      },
      {
        title: 'Holatlar',
        detail:
          '1) Faqat qizil 3s. 2) Qizil+sariq 0.8s. 3) Faqat yashil 3s. 4) Faqat sariq 0.8s. Keyin takror.',
      },
      {
        title: 'Kod yozish',
        detail:
          'setLights(r,y,g) funksiyasi orqali 3 digitalWrite ni bir joyda yozing. loop() da delay lar bilan chaqiring.',
      },
      {
        title: 'Upload va sinov',
        detail: 'Simulyatorda siklni ko‘ring, keyin plataga yuklang.',
      },
    ],
    practice: [
      'Vaqtlarni o‘zgartirib “tez/sekin” svetofor qiling',
      'Piyoda uchun qo‘shimcha LED qo‘shishni o‘ylab ko‘ring',
    ],
    code: `const int R = 11, Y = 12, G = 13;

void setLights(int r, int y, int g) {
  digitalWrite(R, r);
  digitalWrite(Y, y);
  digitalWrite(G, g);
}

void setup() {
  pinMode(R, OUTPUT);
  pinMode(Y, OUTPUT);
  pinMode(G, OUTPUT);
}

void loop() {
  setLights(HIGH, LOW, LOW);  // qizil
  delay(3000);
  setLights(HIGH, HIGH, LOW); // qizil + sariq
  delay(800);
  setLights(LOW, LOW, HIGH);  // yashil
  delay(3000);
  setLights(LOW, HIGH, LOW);  // sariq
  delay(800);
}`,
    tip: 'Haqiqiy svetoforda sariq qisqa bo‘ladi — delay larni shunga moslang.',
    sim: 'traffic',
    tasks: [
      {
        n: 1,
        title: 'Oddiy svetofor',
        text: 'Yuqoridagi asosiy kodni yuklang va ishlatib ko‘ring.',
        code: `// Asosiy dars kodidan foydalaning (R=11,Y=12,G=13)`,
      },
      {
        n: 2,
        title: 'Tez sikl',
        text: 'Barcha delay larni 2 baravar qisqartiring.',
        code: `// delay(3000)→1500, delay(800)→400`,
      },
    ],
  },
  {
    id: 'dars3',
    num: 3,
    level: 'ortacha',
    title: '3-dars. PWM va analog pinlar',
    minutes: 50,
    summary:
      'PWM (~) pinlar va analog (A0–A5) haqida aniq ma’lumot. LED yorqinligini boshqarish — 5 topshiriq.',
    goals: [
      'PWM nima: 0–255 analogWrite',
      'Qaysi pinlar PWM (Uno: 3,5,6,9,10,11)',
      'Analog pinlar A0–A5: analogRead 0–1023',
    ],
    parts: ['Arduino', 'LED lar', '220Ω', 'Maket'],
    wiring: [
      'PWM LED: ~ pin (masalan 9) → rezistor → LED → GND',
      'Analog o‘qish keyinroq (pot) — shu darsda asosan PWM',
    ],
    steps: [
      {
        title: 'PWM nima?',
        detail:
          'PWM — tez yoqib-o‘chirish orqali “o‘rtacha” kuchlanish. Ko‘zga silliq yorqinlik bo‘lib ko‘rinadi. analogWrite(pin, 0..255): 0=o‘chiq, 255=to‘liq.',
      },
      {
        title: 'PWM pinlar (Uno/Nano)',
        detail:
          'Belgisi ~ bo‘lgan pinlar: 3, 5, 6, 9, 10, 11. Boshqa digital pinlarda analogWrite silliq ishlamaydi.',
      },
      {
        title: 'Analog pinlar',
        detail:
          'A0–A5 — analog kirish. analogRead() 0..1023 qaytaradi (0V..5V). Potensiometr, sensor ulanadi. Chiqish uchun emas — o‘qish uchun.',
      },
      {
        title: 'Qo‘lda yozish',
        detail:
          'Topshiriqlarda “ko‘chirmang” deyilgan — birinchi marta o‘zingiz yozing, keyin yechim bilan solishtiring.',
      },
    ],
    practice: [
      'Simulyatorda 0–255 ni kuzating',
      'Topshiriq 1 ni qo‘lda yozib Upload qiling',
    ],
    code: `// Oddiy fade (pin 9)
void setup() {
  pinMode(9, OUTPUT);
}

void loop() {
  for (int v = 0; v <= 255; v++) {
    analogWrite(9, v);
    delay(10);
  }
  for (int v = 255; v >= 0; v--) {
    analogWrite(9, v);
    delay(10);
  }
}`,
    tip: 'analogWrite — PWM pinlarda. digitalWrite — oddiy HIGH/LOW.',
    sim: 'pwm',
    tasks: [
      {
        n: 1,
        title: '1 LED: 5→255, qadam 5, 0.1s',
        text: 'Har 0.1 s da 5 dan ortib 255 gacha. Qo‘lda yozing.',
        code: `void setup() {
  pinMode(9, OUTPUT);
}

void loop() {
  for (int v = 5; v <= 255; v += 5) {
    analogWrite(9, v);
    delay(100);
  }
}`,
      },
      {
        n: 2,
        title: '2 LED birga: 15→135, qadam 15, 0.2s',
        text: 'Ikkala LED bir vaqtda yorqinlashsin.',
        code: `void setup() {
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
}

void loop() {
  for (int v = 15; v <= 135; v += 15) {
    analogWrite(9, v);
    analogWrite(10, v);
    delay(200);
  }
}`,
      },
      {
        n: 3,
        title: 'Teskari fade birga',
        text: '1-LED o‘chiqdan yorqinlashadi, 2-LED yorqinlikdan so‘nadi. Har 0.2s ±25. Bir vaqtda.',
        code: `void setup() {
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
}

void loop() {
  for (int a = 0, b = 255; a <= 255; a += 25, b -= 25) {
    analogWrite(9, a);
    analogWrite(10, b);
    delay(200);
  }
}`,
      },
      {
        n: 4,
        title: 'Avval 1 so‘nsin, keyin 2 yonsin',
        text: '1-LED 255→0 (har 0.2s −25). 0 yaqinlashgach 2-LED 0→255 (+25).',
        code: `void setup() {
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  analogWrite(10, 0);
}

void loop() {
  for (int v = 255; v >= 0; v -= 25) {
    analogWrite(9, v);
    delay(200);
  }
  for (int v = 0; v <= 255; v += 25) {
    analogWrite(10, v);
    delay(200);
  }
  analogWrite(10, 0);
}`,
      },
      {
        n: 5,
        title: '10 LED + alohida PWM LED',
        text: '5 yashil+5 qizil qator. Alohida LED: har keyingi qator LED yonganda +15 yorqinlik (15…150).',
        code: `int row[] = {2,3,4,5,7,8,10,11,12,13}; // 10 ta
int soft = 9; // PWM (~) alohida LED

void setup() {
  for (int i = 0; i < 10; i++) pinMode(row[i], OUTPUT);
  pinMode(soft, OUTPUT);
}

void loop() {
  for (int i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) digitalWrite(row[j], LOW);
    digitalWrite(row[i], HIGH);
    analogWrite(soft, 15 * (i + 1)); // 15..150
    delay(500);
  }
  analogWrite(soft, 0);
}`,
      },
    ],
  },
  {
    id: 'dars4',
    num: 4,
    level: 'ortacha',
    title: '4-dars. Serial Monitor',
    minutes: 40,
    summary:
      'Serial.begin, print, println. Monitor portda matn chiqarish — 12 topshiriq.',
    goals: [
      'Serial.begin(9600)',
      'print vs println',
      'Bo‘sh joy va yangi qator',
      'delay bilan ketma-ket chiqarish',
    ],
    parts: ['Arduino', 'USB (Monitor uchun)', 'IDE Serial Monitor'],
    wiring: ['Qo‘shimcha sim shart emas — USB orqali Serial ishlaydi'],
    steps: [
      {
        title: 'Serial nima?',
        detail:
          'Kompyuter bilan matn almashish. IDE: Tools → Serial Monitor. Baud (tezlik) sketchdagi bilan bir xil bo‘lsin: 9600.',
      },
      {
        title: 'print va println',
        detail:
          'Serial.print("A") — bir qatorda. Serial.println("A") — yozib yangi qatorga o‘tadi. " " — bo‘sh joy.',
      },
      {
        title: 'setup vs loop',
        detail:
          'Bir marta chiqsin desangiz — setup() ichida. Takrorlansin — loop() + delay.',
      },
    ],
    practice: [
      'Serial Monitor ni 9600 da oching',
      'Ismingizni chiqarib ko‘ring',
      'Topshiriqlarni bajarib yechim bilan solishtiring',
    ],
    code: `void setup() {
  Serial.begin(9600);
  Serial.println("Assalomu alaykum");
}

void loop() {
  // bo'sh yoki qo'shimcha xabarlar
}`,
    tip: 'Monitor ochilmasa: Port va 9600 ni tekshiring.',
    sim: 'serial',
    tasks: [
      {
        n: 1,
        title: 'Ism chiqsin',
        text: 'Monitor portda ismingiz ko‘rinsin (masalan: Nozima).',
        code: `void setup() {
  Serial.begin(9600);
  Serial.print("Nozima");
}
void loop() {}`,
      },
      {
        n: 2,
        title: 'Assalomu alaykum',
        text: 'Monitor portda Assalomu alaykum. yozuvi.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.print("Assalomu alaykum.");
}
void loop() {}`,
      },
      {
        n: 3,
        title: 'Mening ismim …',
        text: 'Mening ismim (ismingiz).',
        code: `void setup() {
  Serial.begin(9600);
  Serial.print("Mening ismim Nozima.");
}
void loop() {}`,
      },
      {
        n: 4,
        title: 'Bo‘sh joylar',
        text: 'Assalomu alaykum so‘zlari orasida joy.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.print("Assalomu");
  Serial.print(" ");
  Serial.print("alaykum.");
}
void loop() {}`,
      },
      {
        n: 5,
        title: 'Ism takror',
        text: 'Nozima Nozima Nozima … bir qatorda.',
        code: `void setup() {
  Serial.begin(9600);
}
void loop() {
  Serial.print("Nozima ");
  delay(300);
}`,
      },
      {
        n: 6,
        title: 'Uch gap, joy tashlab',
        text: 'Assalomu alaykum. Mening ismim Nozima. Ramazon oyi Muborak bo‘lsin!!!',
        code: `void setup() {
  Serial.begin(9600);
  Serial.print("Assalomu alaykum. ");
  Serial.print("Mening ismim Nozima. ");
  Serial.print("Ramazon oyi Muborak bo'lsin!!!");
}
void loop() {}`,
      },
      {
        n: 7,
        title: 'println — yangi qator',
        text: 'Ism chiqsin, keyingi ma’lumot yangi satrda.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.println("Nozima");
  Serial.println("Keyingi qator");
}
void loop() {}`,
      },
      {
        n: 8,
        title: 'Mening ismim + yangi qator',
        text: 'Mening ismim … println bilan.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.println("Mening ismim Nozima.");
  Serial.println("Keyingi ma'lumot");
}
void loop() {}`,
      },
      {
        n: 9,
        title: 'Har gap yangi satr',
        text: '3 ta gap — har biri yangi qatordan.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.println("Assalomu alaykum.");
  Serial.println("Mening ismim Nozima.");
  Serial.println("Ramazon oyi Muborak bo'lsin!!!");
}
void loop() {}`,
      },
      {
        n: 10,
        title: 'Mening ismim: / ism',
        text: 'Ikki qator: sarlavha va ism.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.println("Mening ismim:");
  Serial.println("Nozima");
}
void loop() {}`,
      },
      {
        n: 11,
        title: 'Manzil va yosh',
        text: 'Yashash joyi va yosh tagma-tag.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.println("Toshkent");
  Serial.println("30 yosh");
}
void loop() {}`,
      },
      {
        n: 12,
        title: 'Vaqt bilan ketma-ket',
        text: 'Avval Assalomu alaykum; 1s keyin ism; 0.5s keyin kasb; 0.5s keyin yosh yoniga.',
        code: `void setup() {
  Serial.begin(9600);
  Serial.println("Assalomu alaykum.");
  delay(1000);
  Serial.println("Mening ismim Nozima.");
  delay(500);
  Serial.print("Men texnologiya o'qituvchisiman. ");
  delay(500);
  Serial.println("Yoshim 30 da.");
}
void loop() {}`,
      },
    ],
  },
  {
    id: 'dars5',
    num: 5,
    level: 'ortacha',
    title: '5-dars. o‘zgaruvchilar (int)',
    minutes: 45,
    summary: 'int tipi: nomlash, qiymat o‘zgartirish, LED/PWM/Serial bilan — 6 topshiriq.',
    goals: [
      'int x = 0; e’lon qilish',
      'x = x + 1; / x += 2',
      'O‘zgaruvchini pin yoki yorqinlik sifatida ishlatish',
    ],
    parts: ['Arduino', 'LED', 'PWM pin', 'Serial Monitor'],
    wiring: ['LED → PWM pin (5 yoki 9) + rezistor → GND'],
    steps: [
      {
        title: 'int nima?',
        detail:
          'int — butun son (−32768…32767 tipik). int led = 3; — pin raqami yoki qiymat saqlashi mumkin.',
      },
      {
        title: 'Nomlash',
        detail:
          'Ma’noli nom: ledPin, brightness. Ba’zi topshiriqlarda “salom/xayr” kabi nomlar mashq uchun.',
      },
      {
        title: 'Loop ichida o‘zgarish',
        detail: 'Har siklda += yoki -= qilib Serial.println bilan kuzating.',
      },
    ],
    practice: [
      'int hisoblagich yozib Serial da ko‘ring',
      'Topshiriq 1–6 ni bajaring',
    ],
    code: `int count = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println(count);
  count = count + 1;
  delay(1000);
}`,
    tip: 'Pin raqamini const int qilish ham yaxshi odat.',
    sim: 'vars',
    tasks: [
      {
        n: 1,
        title: 'xayr=0, salom=1 — LED',
        text: '0 ni xayr, 1 ni salom deb belgilang. Pin 3 LED ni shu o‘zgaruvchilar bilan yoqib-o‘chiring.',
        code: `int xayr = 0;   // LOW
int salom = 1; // HIGH
int led = 3;

void setup() {
  pinMode(led, OUTPUT);
}

void loop() {
  digitalWrite(led, salom);
  delay(500);
  digitalWrite(led, xayr);
  delay(500);
}`,
      },
      {
        n: 2,
        title: 'Harflar = yorqinlik',
        text: 'M=255,N=200,Z=150,X=100,Y=50,W=0. Pin 5 da ketma-ket analogWrite, orada 500ms.',
        code: `int M = 255, N = 200, Z = 150, X = 100, Y = 50, W = 0;
int led = 5;

void setup() {
  pinMode(led, OUTPUT);
}

void loop() {
  int vals[] = {M, N, Z, X, Y, W};
  for (int i = 0; i < 6; i++) {
    analogWrite(led, vals[i]);
    delay(500);
  }
}`,
      },
      {
        n: 3,
        title: 'c += 2 har soniya',
        text: 'c=0 dan boshlab har 1s da +2, Serial da ko‘rsatilsin.',
        code: `int c = 0;
void setup() { Serial.begin(9600); }
void loop() {
  Serial.println(c);
  c = c + 2;
  delay(1000);
}`,
      },
      {
        n: 4,
        title: 'g kamayadi, d ortadi',
        text: 'g=100 (−1), d=1 (+1) har soniya, Serial.',
        code: `int g = 100;
int d = 1;
void setup() { Serial.begin(9600); }
void loop() {
  Serial.print("g=");
  Serial.print(g);
  Serial.print(" d=");
  Serial.println(d);
  g = g - 1;
  d = d + 1;
  delay(1000);
}`,
      },
      {
        n: 5,
        title: 'Led 0→… +15 PWM',
        text: 'Led=0, har 500ms +15, analogWrite shu qiymat bilan.',
        code: `int Led = 0;
int pin = 9;
void setup() { pinMode(pin, OUTPUT); }
void loop() {
  analogWrite(pin, Led);
  Led = Led + 15;
  if (Led > 255) Led = 0;
  delay(500);
}`,
      },
      {
        n: 6,
        title: 'Led 255→… −5 PWM',
        text: 'Led=255, har 500ms −5.',
        code: `int Led = 255;
int pin = 9;
void setup() { pinMode(pin, OUTPUT); }
void loop() {
  analogWrite(pin, Led);
  Led = Led - 5;
  if (Led < 0) Led = 255;
  delay(500);
}`,
      },
    ],
  },
  {
    id: 'dars6',
    num: 6,
    level: 'loyiha',
    title: '6-dars. if / else',
    minutes: 55,
    summary: 'Shart operatori: if, else if, else. Hisoblagich + LED + Serial — 10 topshiriq.',
    goals: [
      'if (shart) { ... }',
      'else if / else',
      '==, >, < solishtirish',
      'Hisoblagichni 0 ga qaytarish',
    ],
    parts: ['Arduino', '3–5 rangli LED', 'Rezistorlar', 'Serial Monitor'],
    wiring: [
      'Masalan: qizil=11, ko‘k=12, yashil=13 (yoki o‘zingiz tanlang)',
      'PWM mashqlar uchun ~ pin',
    ],
    steps: [
      {
        title: 'if nima?',
        detail:
          'if (x == 5) { digitalWrite(led, HIGH); } — shart rost bo‘lsa bajariladi. else — aks holda.',
      },
      {
        title: 'else if zanjiri',
        detail:
          'Bir nechta holat: if / else if / else. Faqat birinchi rost shart ishlaydi.',
      },
      {
        title: 'Hisoblagich + reset',
        detail: 'n++ ; if (n > 30) n = 0; — siklni qayta boshlash.',
      },
    ],
    practice: [
      '1–10 sanashni Serial da yozing',
      '5 da LED yoqishni qo‘shing',
      'Qolgan topshiriqlarga o‘ting',
    ],
    code: `int n = 0;
int led = 13;

void setup() {
  Serial.begin(9600);
  pinMode(led, OUTPUT);
}

void loop() {
  n = n + 1;
  Serial.println(n);
  if (n == 5) digitalWrite(led, HIGH);
  if (n == 10) {
    digitalWrite(led, LOW);
    n = 0;
  }
  delay(500);
}`,
    tip: '== solishtirish, = qiymat berish. Adashtirmang!',
    sim: 'ifel',
    tasks: [
      {
        n: 1,
        title: '1 dan 10 gacha',
        text: 'O‘zgaruvchi bilan Monitor da 1…10.',
        code: `int n = 0;
void setup() { Serial.begin(9600); }
void loop() {
  n++;
  Serial.println(n);
  if (n >= 10) n = 0;
  delay(500);
}`,
      },
      {
        n: 2,
        title: '5 da yon, 10 da o‘ch',
        text: '1-topshiriq + LED.',
        code: `int n = 0; int led = 13;
void setup() {
  Serial.begin(9600);
  pinMode(led, OUTPUT);
}
void loop() {
  n++;
  Serial.println(n);
  if (n == 5) digitalWrite(led, HIGH);
  if (n == 10) { digitalWrite(led, LOW); n = 0; }
  delay(500);
}`,
      },
      {
        n: 3,
        title: '10 da xabar',
        text: '15 gacha sanang; 10 da "10 soni hosil bo\'ldi".',
        code: `int n = 0;
void setup() { Serial.begin(9600); }
void loop() {
  n++;
  Serial.println(n);
  if (n == 10) Serial.println("10 soni hosil bo'ldi");
  if (n >= 15) n = 0;
  delay(400);
}`,
      },
      {
        n: 4,
        title: 'RGB 5/10/15/20/25/30',
        text: '0…30; 5 qizil, 10 ko‘k, 15 yashil yon; 20 yashil o‘ch, 25 ko‘k o‘ch, 30 qizil o‘ch.',
        code: `int n = 0;
int R = 11, B = 12, G = 13;
void setup() {
  pinMode(R, OUTPUT); pinMode(B, OUTPUT); pinMode(G, OUTPUT);
}
void loop() {
  n++;
  if (n == 5) digitalWrite(R, HIGH);
  if (n == 10) digitalWrite(B, HIGH);
  if (n == 15) digitalWrite(G, HIGH);
  if (n == 20) digitalWrite(G, LOW);
  if (n == 25) digitalWrite(B, LOW);
  if (n == 30) { digitalWrite(R, LOW); n = 0; }
  delay(300);
}`,
      },
      {
        n: 5,
        title: 'RGB + Serial rang nomi',
        text: '4-topshiriq + RED/BLUE/GREEN yozuvlari.',
        code: `int n = 0;
int R = 11, B = 12, G = 13;
void setup() {
  Serial.begin(9600);
  pinMode(R, OUTPUT); pinMode(B, OUTPUT); pinMode(G, OUTPUT);
}
void loop() {
  n++;
  if (n == 5) { digitalWrite(R, HIGH); Serial.println("RED"); }
  if (n == 10) { digitalWrite(B, HIGH); Serial.println("BLUE"); }
  if (n == 15) { digitalWrite(G, HIGH); Serial.println("GREEN"); }
  if (n == 20) { digitalWrite(G, LOW); Serial.println("GREEN"); }
  if (n == 25) { digitalWrite(B, LOW); Serial.println("BLUE"); }
  if (n == 30) { digitalWrite(R, LOW); Serial.println("RED"); n = 0; }
  delay(300);
}`,
      },
      {
        n: 6,
        title: 'PWM +50, 250 da reset',
        text: 'Har soniya +50; 250 da 0.',
        code: `int v = 0; int pin = 9;
void setup() { pinMode(pin, OUTPUT); }
void loop() {
  analogWrite(pin, v);
  v = v + 50;
  if (v >= 250) v = 0;
  delay(1000);
}`,
      },
      {
        n: 7,
        title: '2 LED: biri ↑ biri ↓',
        text: 'a: 0→250 (+10), b: 250→0 (−10), sikl.',
        code: `int a = 0, b = 250;
int p1 = 9, p2 = 10;
void setup() { pinMode(p1, OUTPUT); pinMode(p2, OUTPUT); }
void loop() {
  analogWrite(p1, a);
  analogWrite(p2, b);
  a += 10; if (a >= 250) a = 0;
  b -= 10; if (b <= 0) b = 250;
  delay(1000);
}`,
      },
      {
        n: 8,
        title: '5 rang, n=2,4,6,8,10',
        text: 'n har 0.5s +2; 12 da 0. Mos LED yonadi.',
        code: `int n = 0;
int green=2, blue=3, white=4, yellow=5, red=6;
void setup() {
  pinMode(green, OUTPUT); pinMode(blue, OUTPUT);
  pinMode(white, OUTPUT); pinMode(yellow, OUTPUT); pinMode(red, OUTPUT);
}
void allOff() {
  digitalWrite(green, LOW); digitalWrite(blue, LOW);
  digitalWrite(white, LOW); digitalWrite(yellow, LOW); digitalWrite(red, LOW);
}
void loop() {
  allOff();
  if (n == 2) digitalWrite(green, HIGH);
  else if (n == 4) digitalWrite(blue, HIGH);
  else if (n == 6) digitalWrite(white, HIGH);
  else if (n == 8) digitalWrite(yellow, HIGH);
  else if (n == 10) digitalWrite(red, HIGH);
  n += 2;
  if (n >= 12) n = 0;
  delay(500);
}`,
      },
      {
        n: 9,
        title: '8 + Serial rang nomi',
        text: 'Qaysi rang yonsa — nomi Monitor da.',
        code: `int n = 0;
int green=2, blue=3, white=4, yellow=5, red=6;
void setup() {
  Serial.begin(9600);
  pinMode(green, OUTPUT); pinMode(blue, OUTPUT);
  pinMode(white, OUTPUT); pinMode(yellow, OUTPUT); pinMode(red, OUTPUT);
}
void allOff() {
  digitalWrite(green, LOW); digitalWrite(blue, LOW);
  digitalWrite(white, LOW); digitalWrite(yellow, LOW); digitalWrite(red, LOW);
}
void loop() {
  allOff();
  if (n == 2) { digitalWrite(green, HIGH); Serial.println("YASHIL"); }
  else if (n == 4) { digitalWrite(blue, HIGH); Serial.println("KO'K"); }
  else if (n == 6) { digitalWrite(white, HIGH); Serial.println("OQ"); }
  else if (n == 8) { digitalWrite(yellow, HIGH); Serial.println("SARIQ"); }
  else if (n == 10) { digitalWrite(red, HIGH); Serial.println("QIZIL"); }
  n += 2;
  if (n >= 12) n = 0;
  delay(500);
}`,
      },
      {
        n: 10,
        title: '3 LED maxsus sikl',
        text: 'n=1..7 holatlar; 8 da n=0. Chetki/o‘rta/ miltillash.',
        code: `int n = 0;
int L1=2, L2=3, L3=4;
void setup() {
  pinMode(L1, OUTPUT); pinMode(L2, OUTPUT); pinMode(L3, OUTPUT);
}
void off() {
  digitalWrite(L1, LOW); digitalWrite(L2, LOW); digitalWrite(L3, LOW);
}
void loop() {
  n++;
  off();
  if (n == 1) digitalWrite(L1, HIGH);
  else if (n == 2) digitalWrite(L2, HIGH);
  else if (n == 3) digitalWrite(L3, HIGH);
  else if (n == 4) { /* hammasi o'chiq */ }
  else if (n == 5) { digitalWrite(L1, HIGH); digitalWrite(L3, HIGH); }
  else if (n == 6) digitalWrite(L2, HIGH);
  else if (n == 7) {
    digitalWrite(L1, HIGH); digitalWrite(L2, HIGH); digitalWrite(L3, HIGH);
    delay(500);
    off();
  } else if (n >= 8) n = 0;
  delay(1000);
}`,
      },
    ],
  },
]
