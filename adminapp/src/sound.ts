/** Yangi buyurtma — kuchli signal + kuchli vibratsiya. */

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

/** Uzoq, qaytariluvchi vibratsiya (telefon qo‘lda bo‘lmasa ham seziladi). */
function vibratePhone(
  pattern: number | number[] = [450, 150, 450, 150, 450, 200, 700],
): void {
  try {
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      navigator.vibrate(pattern)
    }
  } catch {
    /* ignore */
  }
}

/** Kuchli signal: baland square + ikkinchi ohang. */
function playBeepInternal(c: AudioContext, volume = 0.85): void {
  const now = c.currentTime
  const tones = [
    { f: 880, t: 0, d: 0.18 },
    { f: 1320, t: 0.2, d: 0.22 },
    { f: 880, t: 0.46, d: 0.18 },
    { f: 1480, t: 0.7, d: 0.28 },
    { f: 990, t: 1.05, d: 0.35 },
    { f: 1600, t: 1.45, d: 0.4 },
  ]
  for (const tone of tones) {
    const osc = c.createOscillator()
    const gain = c.createGain()
    osc.type = 'square'
    osc.frequency.value = tone.f
    gain.gain.setValueAtTime(0.0001, now + tone.t)
    gain.gain.exponentialRampToValueAtTime(volume, now + tone.t + 0.012)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + tone.t + tone.d)
    osc.connect(gain)
    gain.connect(c.destination)
    osc.start(now + tone.t)
    osc.stop(now + tone.t + tone.d + 0.05)

    // Parallel sawtooth — yanada «qattiq» eshitiladi
    const osc2 = c.createOscillator()
    const gain2 = c.createGain()
    osc2.type = 'sawtooth'
    osc2.frequency.value = tone.f * 0.5
    gain2.gain.setValueAtTime(0.0001, now + tone.t)
    gain2.gain.exponentialRampToValueAtTime(
      volume * 0.35,
      now + tone.t + 0.012,
    )
    gain2.gain.exponentialRampToValueAtTime(0.0001, now + tone.t + tone.d)
    osc2.connect(gain2)
    gain2.connect(c.destination)
    osc2.start(now + tone.t)
    osc2.stop(now + tone.t + tone.d + 0.05)
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
      playBeepInternal(c, 0.8)
      vibratePhone([400, 120, 400, 120, 600])
    }
    unlocked = true
    return true
  } catch (e) {
    console.warn('unlockAdminSound', e)
    try {
      unlocked = true
      playBeepInternal(c, 0.8)
      vibratePhone([400, 120, 400, 120, 600])
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

/** Yangi buyurtma: ~12 soniya kuchli signal + vibratsiya. */
export function alertNewOrder(_opts?: {
  count?: number
  orderId?: number
}): void {
  const c = getCtx()
  if (!c) {
    vibratePhone([500, 150, 500, 150, 500, 200, 800, 200, 500])
    return
  }

  const ring = () => {
    try {
      playBeepInternal(c, 0.9)
      vibratePhone([500, 120, 500, 120, 500, 160, 800])
      unlocked = true
    } catch (e) {
      console.warn('alertNewOrder', e)
      vibratePhone([500, 120, 500, 120, 800])
    }
  }

  const start = () => {
    stopAlarmLoop()
    ring()
    let left = 5
    alarmTimer = window.setInterval(() => {
      if (left <= 0) {
        stopAlarmLoop()
        return
      }
      ring()
      left -= 1
    }, 2200)
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
