import {
  DEFAULT_PERIODS,
  cellKey,
  todayDayId,
  type DayId,
  type Period,
} from './schedule'

export type AlarmSettings = {
  enabled: boolean
  minutesBefore: number
  sound: boolean
  vibrate: boolean
}

export const DEFAULT_ALARM: AlarmSettings = {
  enabled: true,
  minutesBefore: 5,
  sound: true,
  vibrate: true,
}

export type AlarmEvent = {
  id: string
  period: Period
  subject: string
  kind: 'before' | 'start'
  at: Date
}

function parseTodayTime(hhmm: string, now = new Date()): Date {
  const [h, m] = hhmm.split(':').map(Number)
  const d = new Date(now)
  d.setHours(h, m, 0, 0)
  return d
}

export function nextLessonsToday(
  subjects: Record<string, string>,
  day: DayId | null,
  now = new Date(),
): { period: Period; subject: string; start: Date }[] {
  if (!day) return []
  const out: { period: Period; subject: string; start: Date }[] = []
  for (const p of DEFAULT_PERIODS) {
    const subject = (subjects[cellKey(day, p.n)] || '').trim()
    if (!subject) continue
    out.push({ period: p, subject, start: parseTodayTime(p.start, now) })
  }
  return out
}

export function findDueAlarm(
  subjects: Record<string, string>,
  settings: AlarmSettings,
  fired: Set<string>,
  now = new Date(),
): AlarmEvent | null {
  if (!settings.enabled) return null
  const day = todayDayId(now)
  if (!day) return null

  const windowMs = 25_000 // ~check window
  for (const p of DEFAULT_PERIODS) {
    const subject = (subjects[cellKey(day, p.n)] || '').trim()
    if (!subject) continue
    const start = parseTodayTime(p.start, now)

    const beforeAt = new Date(start.getTime() - settings.minutesBefore * 60_000)
    const beforeId = `${day}-${p.n}-before-${settings.minutesBefore}`
    if (
      !fired.has(beforeId) &&
      now.getTime() >= beforeAt.getTime() &&
      now.getTime() < beforeAt.getTime() + windowMs
    ) {
      return { id: beforeId, period: p, subject, kind: 'before', at: beforeAt }
    }

    const startId = `${day}-${p.n}-start`
    if (
      !fired.has(startId) &&
      now.getTime() >= start.getTime() &&
      now.getTime() < start.getTime() + windowMs
    ) {
      return { id: startId, period: p, subject, kind: 'start', at: start }
    }
  }
  return null
}

let audioCtx: AudioContext | null = null

function ctx(): AudioContext {
  if (!audioCtx) audioCtx = new AudioContext()
  return audioCtx
}

/** Budilnik ohangi — qisqa signal */
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
  if (typeof navigator !== 'undefined' && navigator.vibrate) {
    navigator.vibrate([220, 120, 220, 120, 400])
  }
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
      icon: '/jadval/pwa-192.png',
      badge: '/jadval/pwa-192.png',
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
