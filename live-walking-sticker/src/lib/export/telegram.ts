/**
 * Telegram-compatible video sticker export.
 *
 * Telegram video stickers (as of current Bot API docs) expect:
 * - WEBM container with VP9 video
 * - One side exactly 512 px
 * - Duration ≤ 3 seconds
 * - No audio track
 * - Transparent background when possible (VP9 alpha)
 * - File size ideally under ~256 KB for sticker sets (soft limit; we aim low)
 *
 * This produces a constrained WebM; users can upload it via @Stickers or Bot API.
 */
import { encodeWebm } from './webm'
import type { AnimationSettings } from '../../types'

export interface TelegramExportOptions {
  sticker: HTMLImageElement | HTMLCanvasElement
  settings: Pick<AnimationSettings, 'speed' | 'distance' | 'size'>
  onProgress?: (ratio: number) => void
}

const TELEGRAM_SIDE = 512
const TELEGRAM_MAX_MS = 2900

export async function encodeTelegramWebm(opts: TelegramExportOptions): Promise<Blob> {
  const { sticker, settings, onProgress } = opts

  // Cap duration for Telegram; keep a full walk cycle when speed allows
  const naturalCycle = 2400 / Math.max(0.05, settings.speed)
  const durationMs = Math.min(TELEGRAM_MAX_MS, Math.max(1200, naturalCycle))

  // Slightly smaller sticker size so travel fits in 512²
  const tgSettings = {
    ...settings,
    size: Math.min(settings.size, 0.78),
    distance: Math.min(settings.distance, 0.5),
  }

  let blob = await encodeWebm({
    sticker,
    width: TELEGRAM_SIDE,
    height: TELEGRAM_SIDE,
    settings: tgSettings,
    durationMs,
    fps: 24,
    preferAlpha: true,
    // Lower bitrate to approach sticker size budgets
    bitsPerSecond: 400_000,
    onProgress,
  })

  // If still huge, re-encode at lower bitrate / fps
  if (blob.size > 350_000) {
    blob = await encodeWebm({
      sticker,
      width: TELEGRAM_SIDE,
      height: TELEGRAM_SIDE,
      settings: tgSettings,
      durationMs: Math.min(durationMs, 2400),
      fps: 18,
      preferAlpha: true,
      bitsPerSecond: 220_000,
      onProgress,
    })
  }

  return blob
}
