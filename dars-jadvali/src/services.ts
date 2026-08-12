export type ServiceId =
  | 'schedule'
  | 'week'
  | 'bells'
  | 'alarm'
  | 'homework'
  | 'grades'
  | 'attendance'
  | 'events'
  | 'clubs'
  | 'checklist'
  | 'weather'
  | 'voice'
  | 'share'
  | 'print'
  | 'backup'
  | 'calendar'
  | 'templates'
  | 'profiles'
  | 'theme'
  | 'lang'
  | 'parent'
  | 'pin'
  | 'announce'
  | 'stats'
  | 'favorites'
  | 'commute'
  | 'install'
  | 'widget'
  | 'motivation'
  | 'admin'
  | 'substitute'
  | 'notes'
  | 'colors'

export type ServiceDef = {
  id: ServiceId
  titleUz: string
  titleRu: string
  descUz: string
  descRu: string
  tone: 'blue' | 'teal' | 'amber' | 'rose' | 'violet' | 'slate'
  icon: string
  featured?: boolean
}

export const SERVICES: ServiceDef[] = [
  { id: 'schedule', titleUz: 'Bugungi dars', titleRu: 'Уроки сегодня', descUz: '9 dars jadvali', descRu: 'Расписание', tone: 'blue', icon: 'schedule', featured: true },
  { id: 'week', titleUz: 'Haftalik jadval', titleRu: 'Неделя', descUz: '6×9 grid', descRu: 'Сетка недели', tone: 'teal', icon: 'week', featured: true },
  { id: 'alarm', titleUz: 'Budilnik', titleRu: 'Будильник', descUz: 'Dars eslatmasi', descRu: 'Напоминание', tone: 'amber', icon: 'alarm', featured: true },
  { id: 'homework', titleUz: 'Uyga vazifa', titleRu: 'Домашнее задание', descUz: 'Darsdan berilgan DZ', descRu: 'ДЗ по урокам', tone: 'rose', icon: 'homework', featured: true },
  { id: 'bells', titleUz: 'Qo‘ng‘iroq', titleRu: 'Звонки', descUz: '9 dars vaqti', descRu: 'Время уроков', tone: 'violet', icon: 'bells' },
  { id: 'grades', titleUz: 'Baholar', titleRu: 'Оценки', descUz: 'Fan baholari', descRu: 'Оценки', tone: 'blue', icon: 'grades' },
  { id: 'attendance', titleUz: 'Davomat', titleRu: 'Посещаемость', descUz: 'Keldi/kelmadi', descRu: 'Был/не был', tone: 'teal', icon: 'attendance' },
  { id: 'events', titleUz: 'Imtihon/bayram', titleRu: 'Экзамены', descUz: 'Muhim sanalar', descRu: 'Даты', tone: 'amber', icon: 'events' },
  { id: 'checklist', titleUz: 'Shaxsiy vazifa', titleRu: 'Личные задачи', descUz: 'Ertalabki reja, eslatma', descRu: 'Утренний план, напоминания', tone: 'slate', icon: 'checklist' },
  { id: 'clubs', titleUz: 'To‘garak', titleRu: 'Кружки', descUz: 'Qo‘shimcha', descRu: 'Дополнительно', tone: 'violet', icon: 'clubs' },
  { id: 'weather', titleUz: 'Ob-havo', titleRu: 'Погода', descUz: 'Maktab oldidan', descRu: 'Перед школой', tone: 'blue', icon: 'weather' },
  { id: 'voice', titleUz: 'Ovozli yordam', titleRu: 'Голос', descUz: 'Bugun nechinchi dars?', descRu: 'Какой урок?', tone: 'rose', icon: 'voice' },
  { id: 'share', titleUz: 'Ulashish', titleRu: 'Поделиться', descUz: 'Link yuborish', descRu: 'Отправить', tone: 'teal', icon: 'share' },
  { id: 'print', titleUz: 'Chop etish', titleRu: 'Печать', descUz: 'PDF / printer', descRu: 'PDF', tone: 'slate', icon: 'print' },
  { id: 'backup', titleUz: 'Zaxira', titleRu: 'Резерв', descUz: 'Saqlash / tiklash', descRu: 'Бэкап', tone: 'amber', icon: 'backup' },
  { id: 'calendar', titleUz: 'Kalendar', titleRu: 'Календарь', descUz: '.ics fayl', descRu: 'Файл .ics', tone: 'blue', icon: 'calendar' },
  { id: 'templates', titleUz: 'Shablonlar', titleRu: 'Шаблоны', descUz: 'Tayyor jadval', descRu: 'Готовое', tone: 'violet', icon: 'templates' },
  { id: 'profiles', titleUz: 'Profillar', titleRu: 'Профили', descUz: 'Bir necha sinf', descRu: 'Классы', tone: 'teal', icon: 'profiles' },
  { id: 'theme', titleUz: 'Mavzu', titleRu: 'Тема', descUz: 'Yorug‘ / qorong‘u', descRu: 'Тема', tone: 'slate', icon: 'theme' },
  { id: 'lang', titleUz: 'Til', titleRu: 'Язык', descUz: 'O‘zbek / Русский', descRu: 'Язык', tone: 'blue', icon: 'lang' },
  { id: 'parent', titleUz: 'Ota-ona', titleRu: 'Родитель', descUz: 'Faqat ko‘rish', descRu: 'Просмотр', tone: 'rose', icon: 'parent' },
  { id: 'pin', titleUz: 'PIN himoya', titleRu: 'PIN', descUz: 'Parol qo‘yish', descRu: 'Код', tone: 'amber', icon: 'pin' },
  { id: 'announce', titleUz: 'E’lonlar', titleRu: 'Объявления', descUz: 'Sinf xabarlari', descRu: 'Сообщения', tone: 'violet', icon: 'announce' },
  { id: 'stats', titleUz: 'Statistika', titleRu: 'Статистика', descUz: 'Qaysi fan ko‘p', descRu: 'Статистика', tone: 'teal', icon: 'stats' },
  { id: 'favorites', titleUz: 'Sevimli', titleRu: 'Избранное', descUz: 'Muhim fanlar', descRu: 'Избранное', tone: 'rose', icon: 'favorites' },
  { id: 'commute', titleUz: 'Yo‘l vaqti', titleRu: 'Дорога', descUz: 'Eslatmani siljitish', descRu: 'Дорога', tone: 'slate', icon: 'commute' },
  { id: 'install', titleUz: 'O‘rnatish', titleRu: 'Установить', descUz: 'Bosh ekranga', descRu: 'На экран', tone: 'blue', icon: 'install' },
  { id: 'widget', titleUz: 'Vidjet', titleRu: 'Виджет', descUz: 'Bugungi qisqa', descRu: 'Кратко', tone: 'amber', icon: 'widget' },
  { id: 'motivation', titleUz: 'Motivatsiya', titleRu: 'Мотивация', descUz: 'Streak / maqsad', descRu: 'Серия', tone: 'violet', icon: 'motivation' },
  { id: 'admin', titleUz: 'Sinf paketi', titleRu: 'Пакет класса', descUz: 'Export', descRu: 'Экспорт', tone: 'teal', icon: 'admin' },
  { id: 'substitute', titleUz: 'O‘rinbosar', titleRu: 'Замена', descUz: 'Bugungi o‘zgarish', descRu: 'Замена', tone: 'rose', icon: 'substitute' },
  { id: 'notes', titleUz: 'Mavzu/izoh', titleRu: 'Тема', descUz: 'Dars izohi', descRu: 'Заметка', tone: 'slate', icon: 'notes' },
  { id: 'colors', titleUz: 'Fan ranglari', titleRu: 'Цвета', descUz: 'Har fanga rang', descRu: 'Цвета', tone: 'blue', icon: 'colors' },
]

export function serviceTitle(s: ServiceDef, lang: 'uz' | 'ru') {
  return lang === 'ru' ? s.titleRu : s.titleUz
}

export function serviceDesc(s: ServiceDef, lang: 'uz' | 'ru') {
  return lang === 'ru' ? s.descRu : s.descUz
}
