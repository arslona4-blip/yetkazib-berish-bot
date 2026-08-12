export type LessonLevel = 'boshlangich' | 'ortacha' | 'loyiha'

export type SimKind =
  | 'install'
  | 'blink'
  | 'button'
  | 'pwm'
  | 'pot'
  | 'buzzer'
  | 'servo'
  | 'ultrasonic'
  | 'traffic'

export type LessonStep = {
  title: string
  detail: string
}

export type Lesson = {
  id: string
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
}

export const LEVEL_LABEL: Record<LessonLevel, string> = {
  boshlangich: 'Boshlang‘ich',
  ortacha: 'O‘rta',
  loyiha: 'Loyiha',
}

export const LESSONS: Lesson[] = [
  {
    id: 'install',
    level: 'boshlangich',
    title: '1. Arduino dasturini o‘rnatish',
    minutes: 20,
    summary:
      'Arduino IDE ni Windows / macOS / Linux ga xatosiz o‘rnatish, plata va portni tanlash, birinchi sketch yuklash.',
    goals: [
      'Rasmiy Arduino IDE ni to‘g‘ri yuklab olish',
      'Board (Uno/Nano) va Port ni tanlash',
      'Blink misolini yuklab, LED miltillashini ko‘rish',
    ],
    parts: [
      'Kompyuter (Windows / macOS / Linux)',
      'Internet',
      'Arduino Uno yoki Nano',
      'USB kabel (data uzatadigan — faqat quvvatli bo‘lmasin)',
    ],
    wiring: [
      'Hozircha breadboard kerak emas',
      'Arduino ni USB orqali kompyuterga ulang',
      'Plata yashil/qizil power LED yonishi kerak',
    ],
    steps: [
      {
        title: '1) Rasmiy saytdan yuklab oling',
        detail:
          'Brauzerda https://www.arduino.cc/en/software oching. “Download Options” dan o‘z OS ingizni tanlang: Windows Win 10 and newer, macOS, yoki Linux. Installer (.exe / .dmg / .AppImage) ni yuklang. Noto‘g‘ri saytlardan o‘rnatmang.',
      },
      {
        title: '2) Windows o‘rnatish',
        detail:
          'Yuklangan .exe ni ishga tushiring → “I agree” → “Only for me” yoki “Anyone” → Next. Driver so‘ralsa “Install” bosing (USB chip uchun kerak). O‘rnatish tugagach Arduino IDE ni oching.',
      },
      {
        title: '3) macOS o‘rnatish',
        detail:
          '.dmg ni oching → Arduino IDE ni Applications papkasiga torting. Birinchi ochishda: Control+click → Open (Gatekeeper). Kerak bo‘lsa System Settings → Privacy & Security dan ruxsat bering.',
      },
      {
        title: '4) Linux o‘rnatish',
        detail:
          'AppImage ga chmod +x bering va ishga tushiring. Yoki paket menejeri orqali. Foydalanuvchini dialout guruhiga qo‘shing: sudo usermod -a -G dialout $USER — keyin qayta kiring. Aks holda Port ko‘rinmasligi mumkin.',
      },
      {
        title: '5) Arduino ni ulang va Board tanlang',
        detail:
          'USB ulang. IDE da: Tools → Board → Arduino AVR Boards → Arduino Uno (Nano bo‘lsa Arduino Nano). Noto‘g‘ri board tanlansa upload xato beradi.',
      },
      {
        title: '6) Port tanlang',
        detail:
          'Tools → Port: Windows da odatda COMx (masalan COM3), macOS da /dev/cu.usbserial… yoki /dev/cu.usbmodem…, Linux da /dev/ttyUSB0 yoki /dev/ttyACM0. Port bo‘sh bo‘lsa: kabel, driver yoki dialout guruhini tekshiring.',
      },
      {
        title: '7) Birinchi dastur (Blink)',
        detail:
          'File → Examples → 01.Basics → Blink. Keyin → (Upload) tugmasini bosing. Pastki qismda “Done uploading” chiqishi kerak. Pin 13 LED miltillaydi — o‘rnatish muvaffaqiyatli.',
      },
      {
        title: '8) Tez-tez uchraydigan xatolar',
        detail:
          '“Port not found” — kabel/driver. “avrdude: stk500” — noto‘g‘ri board/port yoki bootloader. Nano CH340 bo‘lsa Windows ga CH340 driver kerak bo‘lishi mumkin. IDE ni yopib-ochib qayta urinib ko‘ring.',
      },
    ],
    practice: [
      'IDE ni oching va Tools → Board / Port ni tekshiring',
      'Examples → Blink ni Upload qiling',
      'LED miltillashini ko‘ring — shu dars tugadi',
      'Serial Monitor (Tools) ni 9600 da ochib, keyingi darslarga tayyorlaning',
    ],
    code: `// File → Examples → 01.Basics → Blink
// Yoki shu kodni yangi sketchga joylang

void setup() {
  pinMode(LED_BUILTIN, OUTPUT); // odatda pin 13
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}`,
    tip: 'Upload dan oldin sketch saqlang. “Done uploading” — eng muhim tasdiq.',
    sim: 'install',
  },
  {
    id: 'led-blink',
    level: 'boshlangich',
    title: '2. LED miltillashi',
    minutes: 15,
    summary:
      'digitalWrite va delay bilan LED yoqib-o‘chirish. Simulyatorda miltillashni ko‘ring.',
    goals: [
      'pinMode(OUTPUT) ni tushunish',
      'HIGH / LOW farqi',
      'delay() bilan vaqt berish',
    ],
    parts: ['Arduino', 'LED (ixtiyoriy tashqi)', '220Ω rezistor', 'Simlar'],
    wiring: [
      'Ichki LED: pin 13 — simsiz ham ishlaydi',
      'Tashqi: pin 13 → 220Ω → LED anod (uzun oyoq), katod → GND',
    ],
    steps: [
      {
        title: 'Yangi sketch oching',
        detail: 'Arduino IDE: File → New. Bo‘sh setup() va loop() chiqadi.',
      },
      {
        title: 'setup() da pinni chiqish qiling',
        detail: 'pinMode(13, OUTPUT); — pin 13 endi LED uchun chiqish.',
      },
      {
        title: 'loop() da yoqish-o‘chirish',
        detail:
          'digitalWrite(13, HIGH); delay(500); digitalWrite(13, LOW); delay(500);',
      },
      {
        title: 'Upload qiling',
        detail: 'Board/Port to‘g‘ri ekanini tekshirib Upload bosing. LED miltillaydi.',
      },
    ],
    practice: [
      'delay(500) ni 200 qilib tezlashtiring',
      'delay ni 1000 qilib sekinlashtiring',
      'Simulyatorda tezlikni solishtiring',
    ],
    code: `void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  digitalWrite(13, HIGH); // yonadi
  delay(500);             // 0.5 soniya
  digitalWrite(13, LOW);  // o'chadi
  delay(500);
}`,
    tip: 'LED qutbli: uzun oyoq — anod (+). Rezistorsiz LED yonishi mumkin.',
    sim: 'blink',
  },
  {
    id: 'button',
    level: 'boshlangich',
    title: '3. Tugma bilan boshqarish',
    minutes: 18,
    summary: 'digitalRead + INPUT_PULLUP. Tugmani bosib LED yoqing.',
    goals: ['INPUT_PULLUP', 'Tugma bosilganda LOW', 'LED ni shart bilan yoqish'],
    parts: ['Arduino', 'Tugma', 'LED', '220Ω', 'Simlar'],
    wiring: [
      'Tugma: bir tomon → pin 2, ikkinchi → GND',
      'LED: pin 13 → 220Ω → LED → GND',
      'INPUT_PULLUP: bosilganda pin LOW bo‘ladi',
    ],
    steps: [
      {
        title: 'Pinlarni belgilang',
        detail: 'const int BTN = 2; const int LED = 13;',
      },
      {
        title: 'Rejimlar',
        detail: 'pinMode(BTN, INPUT_PULLUP); pinMode(LED, OUTPUT);',
      },
      {
        title: 'O‘qish va yoqish',
        detail:
          'Agar digitalRead(BTN) == LOW bo‘lsa LED HIGH, aks holda LOW.',
      },
      {
        title: 'Sinab ko‘ring',
        detail: 'Upload → tugmani bosing → LED yonadi. Simulyatorda ham shu mantiq.',
      },
    ],
    practice: [
      'Tugmani bosib-turib LED yonishini tekshiring',
      'Mantiqni teskari qilib “bosilganda o‘chsın” qiling',
    ],
    code: `const int BTN = 2;
const int LED = 13;

void setup() {
  pinMode(BTN, INPUT_PULLUP);
  pinMode(LED, OUTPUT);
}

void loop() {
  bool pressed = digitalRead(BTN) == LOW;
  digitalWrite(LED, pressed ? HIGH : LOW);
}`,
    tip: 'Tashqi 10k pull-up o‘rniga INPUT_PULLUP qulay va kam sim.',
    sim: 'button',
  },
  {
    id: 'pwm',
    level: 'ortacha',
    title: '4. PWM — yorug‘lik',
    minutes: 16,
    summary: 'analogWrite(0–255) bilan LED yorqinligini silliq o‘zgartirish.',
    goals: ['PWM pinlar (~)', 'analogWrite', 'for sikli bilan fade'],
    parts: ['Arduino', 'LED', '220Ω'],
    wiring: [
      'LED → PWM pin 9 + 220Ω → GND',
      'Uno PWM: 3, 5, 6, 9, 10, 11',
    ],
    steps: [
      {
        title: 'PWM pin tanlang',
        detail: 'Pin 9 da ~ belgisi bor — analogWrite ishlaydi.',
      },
      {
        title: '0 dan 255 gacha oshiring',
        detail: 'for siklida analogWrite(9, v); delay(8);',
      },
      {
        title: '255 dan 0 gacha kamaytiring',
        detail: 'Fade out — yorug‘lik sekin so‘nadi.',
      },
    ],
    practice: [
      'Simulyator slideri bilan yorqinlikni qo‘lda boshqaring',
      'delay ni o‘zgartirib fade tezligini sozlang',
    ],
    code: `void setup() {
  pinMode(9, OUTPUT);
}

void loop() {
  for (int v = 0; v <= 255; v++) {
    analogWrite(9, v);
    delay(8);
  }
  for (int v = 255; v >= 0; v--) {
    analogWrite(9, v);
    delay(8);
  }
}`,
    tip: 'Oddiy digital pinlarda analogWrite “silliq” emas.',
    sim: 'pwm',
  },
  {
    id: 'pot',
    level: 'ortacha',
    title: '5. Potensiometr',
    minutes: 18,
    summary: 'analogRead (0–1023) → map → LED yorqinligi.',
    goals: ['A0 analog', 'map()', 'Serial Monitor'],
    parts: ['Arduino', '10k potensiometr', 'LED', '220Ω'],
    wiring: [
      'Pot: chap → 5V, o‘ng → GND, o‘rta → A0',
      'LED → pin 9 + 220Ω',
    ],
    steps: [
      {
        title: 'analogRead(A0)',
        detail: '0…1023 oralig‘ida qiymat qaytadi.',
      },
      {
        title: 'map qiling',
        detail: 'map(raw, 0, 1023, 0, 255) — PWM uchun.',
      },
      {
        title: 'Serial Monitor',
        detail: '9600 baud da raw qiymatni kuzating.',
      },
    ],
    practice: [
      'Potni aylantirib LED ni boshqaring',
      'Simulyatorda A0 qiymatini kuzating',
    ],
    code: `void setup() {
  pinMode(9, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int raw = analogRead(A0);
  int pwm = map(raw, 0, 1023, 0, 255);
  analogWrite(9, pwm);
  Serial.println(raw);
  delay(20);
}`,
    tip: 'Serial Monitor tezligi sketchdagi 9600 bilan bir xil bo‘lsin.',
    sim: 'pot',
  },
  {
    id: 'buzzer',
    level: 'ortacha',
    title: '6. Piezo buzzer',
    minutes: 14,
    summary: 'tone() bilan nota chalish. Simulyatorda ohangni eshiting.',
    goals: ['tone / noTone', 'Chastota (Hz)'],
    parts: ['Arduino', 'Piezo buzzer'],
    wiring: ['Buzzer + → pin 8, − → GND'],
    steps: [
      {
        title: 'tone(pin, freq, ms)',
        detail: 'Masalan tone(8, 523, 200) — Do notasi.',
      },
      {
        title: 'Ketma-ket notalar',
        detail: 'delay bilan notalar orasida pauza qoldiring.',
      },
    ],
    practice: [
      'Simulyatorda Play bosing',
      'O‘z melodiyangizni chastotalar bilan yozing',
    ],
    code: `void setup() {
  pinMode(8, OUTPUT);
}

void loop() {
  tone(8, 523, 200); // Do
  delay(250);
  tone(8, 659, 200); // Mi
  delay(250);
  tone(8, 784, 300); // Sol
  delay(600);
  noTone(8);
}`,
    tip: 'Passiv piezo tone() bilan yaxshi ishlaydi.',
    sim: 'buzzer',
  },
  {
    id: 'servo',
    level: 'ortacha',
    title: '7. Servo motor',
    minutes: 20,
    summary: 'Servo.h bilan 0–180°. Simulyatorda burchakni aylantiring.',
    goals: ['Servo ulash', 'attach / write'],
    parts: ['Arduino', 'SG90 servo'],
    wiring: [
      'Signal → pin 9, qizil → 5V, qora → GND',
      'Katta yukda alohida quvvat tavsiya etiladi',
    ],
    steps: [
      {
        title: 'Kutubxona',
        detail: '#include <Servo.h> va Servo s;',
      },
      {
        title: 'attach(9)',
        detail: 'setup() ichida s.attach(9);',
      },
      {
        title: 'write(burchak)',
        detail: '0, 90, 180 — asosiy holatlar.',
      },
    ],
    practice: [
      'Simulyator slideri bilan burchakni o‘zgartiring',
      'Sketchda o‘z ketma-ketligingizni yozing',
    ],
    code: `#include <Servo.h>
Servo s;

void setup() {
  s.attach(9);
}

void loop() {
  s.write(0);
  delay(800);
  s.write(90);
  delay(800);
  s.write(180);
  delay(800);
}`,
    tip: 'Sketch → Include Library → Servo.',
    sim: 'servo',
  },
  {
    id: 'ultrasonic',
    level: 'ortacha',
    title: '8. Ultrasonik masofa',
    minutes: 22,
    summary: 'HC-SR04 bilan sm o‘lchash. Simulyatorda masofani o‘zgartiring.',
    goals: ['TRIG/ECHO', 'pulseIn', 'sm formulasi'],
    parts: ['Arduino', 'HC-SR04'],
    wiring: ['VCC→5V, GND→GND, TRIG→7, ECHO→6'],
    steps: [
      {
        title: '10 µs impuls',
        detail: 'TRIG ni qisqa HIGH qilib o‘lchashni boshlang.',
      },
      {
        title: 'pulseIn(ECHO, HIGH)',
        detail: 'Mikrosoniyalarda vaqt — masofa shundan.',
      },
      {
        title: 'sm ga aylantirish',
        detail: 'cm = us * 0.0343 / 2.0;',
      },
    ],
    practice: [
      'Simulyatorda “obyekt”ni yaqinlashtiring',
      'Serial Monitor da cm ni kuzating (haqiqiy platada)',
    ],
    code: `const int TRIG = 7;
const int ECHO = 6;

void setup() {
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  Serial.begin(9600);
}

void loop() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long us = pulseIn(ECHO, HIGH);
  float cm = us * 0.0343 / 2.0;
  Serial.print(cm);
  Serial.println(" cm");
  delay(200);
}`,
    tip: 'Sensor oldi toza bo‘lsin — aks holda o‘qish noto‘g‘ri.',
    sim: 'ultrasonic',
  },
  {
    id: 'traffic',
    level: 'loyiha',
    title: '9. Loyiha: Svetofor',
    minutes: 25,
    summary:
      '3 LED bilan svetofor sikli. Amaliy mini-loyiha + to‘liq simulyator.',
    goals: [
      'Bir nechta pin',
      'Vaqt ketma-ketligi',
      'Funksiyaga ajratish',
    ],
    parts: ['Arduino', 'Qizil/Sariq/Yashil LED', '3×220Ω'],
    wiring: [
      'Qizil→11, Sariq→12, Yashil→13',
      'Har bir LED → rezistor → GND',
    ],
    steps: [
      {
        title: '3 pin OUTPUT',
        detail: 'R=11, Y=12, G=13.',
      },
      {
        title: 'setLights() yozing',
        detail: 'Bitta funksiya bilan 3 LED holatini bering.',
      },
      {
        title: 'Sikl',
        detail: 'Qizil → qizil+sariq → yashil → sariq → takror.',
      },
    ],
    practice: [
      'Simulyatorda siklni kuzating',
      'Vaqtlarni o‘z shahringiz svetoforiga moslang',
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
  setLights(HIGH, LOW, LOW);
  delay(3000);
  setLights(HIGH, HIGH, LOW);
  delay(800);
  setLights(LOW, LOW, HIGH);
  delay(3000);
  setLights(LOW, HIGH, LOW);
  delay(800);
}`,
    tip: 'Bu loyihani quti ichiga joylab “mini svetofor” qiling.',
    sim: 'traffic',
  },
]
