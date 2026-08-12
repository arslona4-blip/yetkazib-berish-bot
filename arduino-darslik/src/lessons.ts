export type Lesson = {
  id: string
  level: 'boshlangich' | 'ortacha' | 'loyiha'
  title: string
  minutes: number
  summary: string
  goals: string[]
  parts: string[]
  wiring: string[]
  code: string
  tip: string
}

export const LESSONS: Lesson[] = [
  {
    id: 'intro',
    level: 'boshlangich',
    title: 'Arduino nima?',
    minutes: 8,
    summary:
      'Plata, USB kabel, IDE va “sketch” tushunchasi. Birinchi dastur yuklash.',
    goals: [
      'Arduino Uno / Nano ni tanish',
      'Arduino IDE o‘rnatish',
      'Board va Port tanlash',
    ],
    parts: ['Arduino Uno/Nano', 'USB kabel', 'Kompyuter'],
    wiring: [
      'Hozircha sim kerak emas — faqat USB orqali ulang',
      'IDE: Tools → Board → Arduino Uno',
      'Tools → Port → COMx / /dev/tty…',
    ],
    code: `void setup() {
  Serial.begin(9600);
  Serial.println("Salom, Arduino!");
}

void loop() {
  // bo'sh
}`,
    tip: 'Upload tugmasi yashil ✓ bo‘lsa — hammasi joyida.',
  },
  {
    id: 'led-blink',
    level: 'boshlangich',
    title: 'LED miltillashi',
    minutes: 12,
    summary: 'Pin 13 dagi LED ni yoqib-o‘chirish. digitalWrite va delay.',
    goals: [
      'OUTPUT pin rejimini tushunish',
      'HIGH / LOW farqi',
      'delay() bilan vaqt',
    ],
    parts: ['Arduino', 'LED (ixtiyoriy tashqi)', '220Ω rezistor'],
    wiring: [
      'Ichki LED: pin 13 (simsiz ham ishlaydi)',
      'Tashqi LED: anod → 220Ω → pin 13, katod → GND',
    ],
    code: `void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  digitalWrite(13, HIGH);
  delay(500);
  digitalWrite(13, LOW);
  delay(500);
}`,
    tip: 'LED qutblangan: uzun oyoq — anod (+).',
  },
  {
    id: 'button',
    level: 'boshlangich',
    title: 'Tugma bilan boshqarish',
    minutes: 15,
    summary: 'digitalRead orqali tugmani o‘qish va LED ni yoqish.',
    goals: [
      'INPUT_PULLUP ishlatish',
      'Tugma bosilganda mantiqni o‘zgartirish',
    ],
    parts: ['Arduino', 'Tugma', 'LED', '220Ω'],
    wiring: [
      'Tugma: bir tomon → pin 2, ikkinchi → GND',
      'LED: pin 13 → 220Ω → LED → GND',
      'INPUT_PULLUP: bosilganda pin LOW bo‘ladi',
    ],
    code: `const int BTN = 2;
const int LED = 13;

void setup() {
  pinMode(BTN, INPUT_PULLUP);
  pinMode(LED, OUTPUT);
}

void loop() {
  int pressed = digitalRead(BTN) == LOW;
  digitalWrite(LED, pressed ? HIGH : LOW);
}`,
    tip: 'Tashqi 10k pull-up o‘rniga INPUT_PULLUP qulay.',
  },
  {
    id: 'pwm',
    level: 'ortacha',
    title: 'PWM — yorug‘lik boshqaruvi',
    minutes: 14,
    summary: 'analogWrite bilan LED yorqinligini silliq o‘zgartirish.',
    goals: ['PWM pinlarni bilish (~)', '0–255 oralig‘i'],
    parts: ['Arduino', 'LED', '220Ω'],
    wiring: [
      'LED → PWM pin (masalan 9) + 220Ω',
      'Uno PWM: 3, 5, 6, 9, 10, 11',
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
    tip: 'analogWrite faqat PWM pinlarda “silliq” ishlaydi.',
  },
  {
    id: 'pot',
    level: 'ortacha',
    title: 'Potensiometr',
    minutes: 16,
    summary: 'analogRead (0–1023) qiymatini o‘qib LED yorqinligiga bog‘lash.',
    goals: ['A0 analog pin', 'map() funksiyasi'],
    parts: ['Arduino', '10k potensiometr', 'LED', '220Ω'],
    wiring: [
      'Pot: chap → 5V, o‘ng → GND, o‘rta → A0',
      'LED → pin 9 + 220Ω',
    ],
    code: `void setup() {
  pinMode(9, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int raw = analogRead(A0);          // 0..1023
  int pwm = map(raw, 0, 1023, 0, 255);
  analogWrite(9, pwm);
  Serial.println(raw);
  delay(20);
}`,
    tip: 'Serial Monitor (9600) da qiymatlarni ko‘ring.',
  },
  {
    id: 'buzzer',
    level: 'ortacha',
    title: 'Piezo buzzer — ohang',
    minutes: 12,
    summary: 'tone() bilan oddiy melodiya chiqarish.',
    goals: ['tone / noTone', 'Chastota (Hz)'],
    parts: ['Arduino', 'Piezo buzzer'],
    wiring: ['Buzzer + → pin 8, − → GND (passiv piezo yaxshi)'],
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
    tip: 'Aktiv buzzer odatda oddiy HIGH/LOW bilan “piip” qiladi.',
  },
  {
    id: 'servo',
    level: 'ortacha',
    title: 'Servo motor',
    minutes: 18,
    summary: 'Servo.h kutubxonasi bilan 0–180° burchak.',
    goals: ['Servo ulash', 'write(angle)'],
    parts: ['Arduino', 'SG90 servo', 'Tashqi 5V (tavsiya)'],
    wiring: [
      'Servo signal (sariq/oq) → pin 9',
      'Qizil → 5V, qora/jigarrang → GND',
      'Katta yukda alohida quvvat bering',
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
  },
  {
    id: 'ultrasonic',
    level: 'ortacha',
    title: 'Ultrasonik masofa',
    minutes: 20,
    summary: 'HC-SR04 bilan sm da masofa o‘lchash.',
    goals: ['TRIG/ECHO', 'pulseIn', 'sm hisoblash'],
    parts: ['Arduino', 'HC-SR04'],
    wiring: [
      'VCC → 5V, GND → GND',
      'TRIG → pin 7, ECHO → pin 6',
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
    tip: 'Sensor oldini to‘sgan narsalar o‘qishni buzadi.',
  },
  {
    id: 'traffic',
    level: 'loyiha',
    title: 'Loyiha: Svetofor',
    minutes: 25,
    summary: '3 ta LED bilan svetofor sikli — mustaqil mini-loyiha.',
    goals: [
      'Bir nechta pinni boshqarish',
      'Vaqt ketma-ketligi',
      'Kodni funksiyalarga bo‘lish',
    ],
    parts: ['Arduino', 'Qizil/Sariq/Yashil LED', '3×220Ω'],
    wiring: [
      'Qizil → pin 11, Sariq → 12, Yashil → 13',
      'Har bir LED katodi → GND (rezistor orqali)',
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
  setLights(HIGH, LOW, LOW);   // qizil
  delay(3000);
  setLights(HIGH, HIGH, LOW);  // qizil+sariq
  delay(800);
  setLights(LOW, LOW, HIGH);   // yashil
  delay(3000);
  setLights(LOW, HIGH, LOW);   // sariq
  delay(800);
}`,
    tip: 'Vaqtlarni o‘zingizga moslab “shahar” svetoforiga aylantiring.',
  },
]

export const LEVEL_LABEL: Record<Lesson['level'], string> = {
  boshlangich: 'Boshlang‘ich',
  ortacha: 'O‘rta',
  loyiha: 'Loyiha',
}
