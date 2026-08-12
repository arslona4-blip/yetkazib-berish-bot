import {
  cellKey,
  parseClock,
  todayDayId,
  type AlarmSettings,
  type Period,
  type Profile,
} from './model'

export type AlarmEvent = {
  id: string
  period: Period
  subject: string
  kind: 'before' | 'start'
  message: string
}

export function nextLessonsToday(profile: Profile, now = new Date()) {
  const day = todayDayId(now)
  if (!day) return [] as { period: Period; subject: string; start: Date }[]
  const out: { period: Period; subject: string; start: Date }[] = []
  for (const p of profile.periods) {
    const subject = (profile.cells[cellKey(day, p.n)]?.subject || '').trim()
    if (!subject) continue
    out.push({ period: p, subject, start: parseClock(p.start, now) })
  }
  return out
}

export function findDueAlarm(
  profile: Profile,
  settings: AlarmSettings,
  fired: Set<string>,
  now = new Date(),
): AlarmEvent | null {
  if (!settings.enabled) return null
  const day = todayDayId(now)
  if (!day) return null
  const lead = settings.minutesBefore + (profile.commuteMinutes > 0 ? 0 : 0)
  // commute shifts "before" earlier
  const beforeExtra = profile.commuteMinutes || 0
  const windowMs = 25_000

  for (const p of profile.periods) {
    const subject = (profile.cells[cellKey(day, p.n)]?.subject || '').trim()
    if (!subject) continue
    const start = parseClock(p.start, now)
    const beforeAt = new Date(
      start.getTime() - (settings.minutesBefore + beforeExtra) * 60_000,
    )
    const beforeId = `${day}-${p.n}-before`
    if (
      !fired.has(beforeId) &&
      now.getTime() >= beforeAt.getTime() &&
      now.getTime() < beforeAt.getTime() + windowMs
    ) {
      return {
        id: beforeId,
        period: p,
        subject,
        kind: 'before',
        message: profile.alarmMessage || `${lead} daqiqadan keyin dars`,
      }
    }
    const startId = `${day}-${p.n}-start`
    if (
      !fired.has(startId) &&
      now.getTime() >= start.getTime() &&
      now.getTime() < start.getTime() + windowMs
    ) {
      return {
        id: startId,
        period: p,
        subject,
        kind: 'start',
        message: profile.alarmMessage || 'Dars boshlandi!',
      }
    }
  }
  return null
}

let audioCtx: AudioContext | null = null
function ctx() {
  if (!audioCtx) audioCtx = new AudioContext()
  return audioCtx
}

export async function playAlarmSound(times = 4) {
  const ac = ctx()
  if (ac.state === 'suspended') await ac.resume()
  const now = ac.currentTime
  for (let i = 0; i < times; i++) {
    const t0 = now + i * 0.42
    const osc = ac.createOscillator()
    const gain = ac.createGain()
    osc.type = 'square'
    osc.frequency.setValueAtTime(880, t0)
    osc.frequency.setValueAtTime(660, t0 + 0.12)
    gain.gain.setValueAtTime(0.0001, t0)
    gain.gain.exponentialRampToValueAtTime(0.18, t0 + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.28)
    osc.connect(gain)
    gain.connect(ac.destination)
    osc.start(t0)
    osc.stop(t0 + 0.3)
  }
}

export function vibrateAlarm() {
  navigator.vibrate?.([220, 120, 220, 120, 400])
}

export async function ensureNotifyPermission(): Promise<NotificationPermission> {
  if (typeof Notification === 'undefined') return 'denied'
  if (Notification.permission === 'granted') return 'granted'
  if (Notification.permission === 'denied') return 'denied'
  return Notification.requestPermission()
}

export function showSystemNotification(title: string, body: string) {
  if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return
  try {
    const n = new Notification(title, {
      body,
      icon: '/jadval-fedd3d/pwa-192.png',
      tag: 'dars-budilnik',
    })
    n.onclick = () => {
      window.focus()
      n.close()
    }
  } catch {
    /* ignore */
  }
}

export function formatCountdown(ms: number): string {
  if (ms <= 0) return '0:00'
  const total = Math.floor(ms / 1000)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

const FIRED_KEY = 'maktab-jadval-fired-v2'
export function loadFired(): Set<string> {
  try {
    const raw = localStorage.getItem(FIRED_KEY)
    if (!raw) return new Set()
    const parsed = JSON.parse(raw) as { day: string; ids: string[] }
    if (parsed.day !== new Date().toDateString()) return new Set()
    return new Set(parsed.ids || [])
  } catch {
    return new Set()
  }
}
export function saveFired(ids: Set<string>) {
  localStorage.setItem(
    FIRED_KEY,
    JSON.stringify({ day: new Date().toDateString(), ids: [...ids] }),
  )
}
