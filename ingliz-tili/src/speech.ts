type SR = {
  lang: string
  interimResults: boolean
  maxAlternatives: number
  continuous: boolean
  start: () => void
  stop: () => void
  onresult: ((ev: SpeechRecognitionEventLike) => void) | null
  onerror: ((ev: { error: string }) => void) | null
  onend: (() => void) | null
}

type SpeechRecognitionEventLike = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>
}

function getRecognitionCtor(): (new () => SR) | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SR
    webkitSpeechRecognition?: new () => SR
  }
  return w.SpeechRecognition || w.webkitSpeechRecognition || null
}

export function speechSupported() {
  return Boolean(getRecognitionCtor())
}

export function listenOnce(
  lang = 'en-US',
  ms = 6000,
): Promise<{ ok: boolean; text: string; error?: string }> {
  const Ctor = getRecognitionCtor()
  if (!Ctor) {
    return Promise.resolve({ ok: false, text: '', error: 'supported_emas' })
  }

  return new Promise((resolve) => {
    const rec = new Ctor()
    rec.lang = lang
    rec.interimResults = false
    rec.maxAlternatives = 3
    rec.continuous = false
    let done = false
    const finish = (r: { ok: boolean; text: string; error?: string }) => {
      if (done) return
      done = true
      try {
        rec.stop()
      } catch {
        /* ignore */
      }
      resolve(r)
    }

    const t = window.setTimeout(() => finish({ ok: false, text: '', error: 'timeout' }), ms)

    rec.onresult = (ev) => {
      window.clearTimeout(t)
      const text = ev.results?.[0]?.[0]?.transcript?.trim() || ''
      finish({ ok: Boolean(text), text })
    }
    rec.onerror = (ev) => {
      window.clearTimeout(t)
      finish({ ok: false, text: '', error: ev.error || 'error' })
    }
    rec.onend = () => {
      window.clearTimeout(t)
      if (!done) finish({ ok: false, text: '', error: 'end' })
    }

    try {
      rec.start()
    } catch {
      window.clearTimeout(t)
      finish({ ok: false, text: '', error: 'start_fail' })
    }
  })
}

export function scorePronunciation(target: string, heard: string) {
  const a = target
    .toLowerCase()
    .replace(/[’']/g, "'")
    .replace(/[^\w\s']/g, '')
    .trim()
    .split(/\s+/)
  const b = heard
    .toLowerCase()
    .replace(/[’']/g, "'")
    .replace(/[^\w\s']/g, '')
    .trim()
    .split(/\s+/)
  if (!a.length || !b.length || (b.length === 1 && !b[0])) return 0
  let hit = 0
  for (const w of a) {
    if (b.some((x) => x === w || x.includes(w) || w.includes(x))) hit += 1
  }
  return Math.round((hit / a.length) * 100)
}
