export function speak(text: string, lang = 'uz-UZ'): Promise<void> {
  return new Promise((resolve) => {
    if (!('speechSynthesis' in window)) {
      resolve()
      return
    }
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    const voices = window.speechSynthesis.getVoices()
    const pick =
      voices.find((v) => v.lang.toLowerCase().startsWith('uz')) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('ru')) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('tr')) ||
      voices[0]
    if (pick) u.voice = pick
    u.lang = pick?.lang || lang
    u.rate = 0.92
    u.pitch = 1.15
    u.onend = () => resolve()
    u.onerror = () => resolve()
    window.speechSynthesis.speak(u)
  })
}

export function stopSpeak() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}
