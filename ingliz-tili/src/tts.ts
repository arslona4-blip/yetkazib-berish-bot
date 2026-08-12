export function speak(text: string, lang = 'en-US'): Promise<void> {
  return new Promise((resolve) => {
    if (!('speechSynthesis' in window)) {
      resolve()
      return
    }
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    const voices = window.speechSynthesis.getVoices()
    const pick =
      voices.find((v) => v.lang.toLowerCase().startsWith('en-us')) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('en-gb')) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('en')) ||
      voices[0]
    if (pick) u.voice = pick
    u.lang = pick?.lang || lang
    u.rate = 0.88
    u.pitch = 1
    u.onend = () => resolve()
    u.onerror = () => resolve()
    window.speechSynthesis.speak(u)
  })
}

export function stopSpeak() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}

/** Brauzerda ovozlar kech yuklanishi mumkin */
export function warmVoices() {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.getVoices()
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices()
  }
}
