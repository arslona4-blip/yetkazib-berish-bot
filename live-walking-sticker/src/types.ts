/** Animation + preview controls shared across the app. */
export interface AnimationSettings {
  /** Playback speed multiplier (0.25–3). */
  speed: number
  /** Horizontal travel as a fraction of preview width (0.1–0.9). */
  distance: number
  /** Sticker display size as a fraction of preview height (0.2–0.95). */
  size: number
  /** Whether the walking loop is playing. */
  playing: boolean
  /** Loop is always intended; kept for UI clarity. */
  loop: boolean
}

export type ExportFormat = 'gif' | 'webm' | 'apng' | 'telegram-webm'

export interface ExportProgress {
  format: ExportFormat
  phase: 'rendering' | 'encoding' | 'done' | 'error'
  progress: number
  message: string
}

export const DEFAULT_SETTINGS: AnimationSettings = {
  speed: 1,
  distance: 0.55,
  size: 0.72,
  playing: true,
  loop: true,
}
