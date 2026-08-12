export function speak(
  text: string,
  opts: { lang?: string; rate?: number; pitch?: number } = {},
): Promise<void> {
  return new Promise((resolve) => {
    if (!('speechSynthesis' in window)) {
      resolve()
      return
    }
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    const voices = window.speechSynthesis.getVoices()
    const lang = opts.lang || 'en-US'
    const pick =
      voices.find((v) => v.lang.toLowerCase().startsWith(lang.toLowerCase().slice(0, 2) + '-us')) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('en-us')) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('en-gb')) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('en')) ||
      voices[0]
    if (pick) u.voice = pick
    u.lang = pick?.lang || lang
    u.rate = opts.rate ?? 0.9
    u.pitch = opts.pitch ?? 1
    u.onend = () => resolve()
    u.onerror = () => resolve()
    window.speechSynthesis.speak(u)
  })
}

export function stopSpeak() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}

export function warmVoices() {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.getVoices()
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices()
  }
}
