/** Yangi buyurtma — telefon signal (Web Audio + vibration). */

let unlocked = false
let ctx: AudioContext | null = null
let alarmTimer: number | null = null

function getCtx(): AudioContext | null {
  try {
    const AC =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext
    if (!AC) return null
    if (!ctx || ctx.state === 'closed') ctx = new AC()
    return ctx
  } catch {
    return null
  }
}

function vibratePhone(pattern: number | number[] = [280, 120, 280, 120, 450]): void {
  try {
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      navigator.vibrate(pattern)
    }
  } catch {
    /* ignore */
  }
}

/** Bitta kuchli signal (3 ton). */
function playBeepInternal(c: AudioContext, volume = 0.55): void {
  const now = c.currentTime
  const tones = [
    { f: 980, t: 0, d: 0.16 },
    { f: 1310, t: 0.18, d: 0.2 },
    { f: 980, t: 0.42, d: 0.22 },
    { f: 1480, t: 0.68, d: 0.28 },
  ]
  for (const tone of tones) {
    const osc = c.createOscillator()
    const gain = c.createGain()
    osc.type = 'square'
    osc.frequency.value = tone.f
    gain.gain.setValueAtTime(0.0001, now + tone.t)
    gain.gain.exponentialRampToValueAtTime(volume, now + tone.t + 0.015)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + tone.t + tone.d)
    osc.connect(gain)
    gain.connect(c.destination)
    osc.start(now + tone.t)
    osc.stop(now + tone.t + tone.d + 0.04)
  }
}

/**
 * User gesture ichida chaqiring (button click).
 * confirm=true bo‘lsa test signal chaladi.
 */
export async function unlockAdminSound(opts?: {
  confirm?: boolean
}): Promise<boolean> {
  const c = getCtx()
  if (!c) return false
  try {
    if (c.state === 'suspended') {
      await c.resume()
    }
    if (c.state === 'suspended') {
      await new Promise((r) => setTimeout(r, 50))
      await c.resume()
    }
    if (opts?.confirm !== false) {
      playBeepInternal(c, 0.45)
      vibratePhone([200, 80, 200])
    }
    unlocked = true
    return true
  } catch (e) {
    console.warn('unlockAdminSound', e)
    try {
      unlocked = true
      playBeepInternal(c, 0.45)
      vibratePhone([200, 80, 200])
      return true
    } catch {
      return false
    }
  }
}

function stopAlarmLoop(): void {
  if (alarmTimer != null) {
    window.clearInterval(alarmTimer)
    alarmTimer = null
  }
}

/** Yangi buyurtma: 4 marta qaytariladigan signal (~8 soniya). */
export function alertNewOrder(_opts?: {
  count?: number
  orderId?: number
}): void {
  const c = getCtx()
  if (!c) return

  const ring = () => {
    try {
      playBeepInternal(c, 0.6)
      vibratePhone([300, 100, 300, 100, 500])
      unlocked = true
    } catch (e) {
      console.warn('alertNewOrder', e)
    }
  }

  const start = () => {
    stopAlarmLoop()
    ring()
    let left = 3
    alarmTimer = window.setInterval(() => {
      if (left <= 0) {
        stopAlarmLoop()
        return
      }
      ring()
      left -= 1
    }, 2000)
  }

  if (c.state === 'suspended') {
    void c.resume().then(start).catch(() => start())
  } else {
    start()
  }
}

export function isSoundUnlocked(): boolean {
  return unlocked
}
