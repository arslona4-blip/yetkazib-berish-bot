/**
 * Export façade — renders walk frames / streams and encodes GIF, WebM, APNG,
 * and Telegram-compatible WebM stickers.
 */
import { saveAs } from 'file-saver'
import type { AnimationSettings, ExportFormat } from '../../types'
import { resolveExportSize } from '../animation'
import { renderWalkFrames } from './frames'
import { encodeTransparentGif } from './gif'
import { encodeApng } from './apng'
import { encodeWebm } from './webm'
import { encodeTelegramWebm } from './telegram'

export interface ExportRequest {
  sticker: HTMLImageElement
  format: ExportFormat
  settings: AnimationSettings
  onProgress?: (phase: 'rendering' | 'encoding', ratio: number, message: string) => void
}

function baseName(): string {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  return `live-walking-sticker-${stamp}`
}

export async function exportSticker(req: ExportRequest): Promise<void> {
  const { sticker, format, settings, onProgress } = req
  const { width, height } = resolveExportSize(
    sticker.naturalWidth,
    sticker.naturalHeight,
    settings.size,
    settings.distance,
    format === 'telegram-webm' ? 512 : 480,
  )

  if (format === 'webm') {
    onProgress?.('encoding', 0, 'Recording WebM…')
    const blob = await encodeWebm({
      sticker,
      width,
      height,
      settings,
      preferAlpha: true,
      onProgress: (r) => onProgress?.('encoding', r, 'Recording WebM…'),
    })
    saveAs(blob, `${baseName()}.webm`)
    return
  }

  if (format === 'telegram-webm') {
    onProgress?.('encoding', 0, 'Encoding Telegram WebM sticker…')
    const blob = await encodeTelegramWebm({
      sticker,
      settings,
      onProgress: (r) => onProgress?.('encoding', r, 'Encoding Telegram WebM…'),
    })
    saveAs(blob, `${baseName()}-telegram.webm`)
    return
  }

  onProgress?.('rendering', 0, 'Rendering walk frames…')
  const frames = await renderWalkFrames({
    sticker,
    width,
    height,
    settings,
    fps: format === 'gif' ? 16 : 20,
    onProgress: (r) => onProgress?.('rendering', r, 'Rendering walk frames…'),
  })

  if (format === 'gif') {
    onProgress?.('encoding', 0, 'Encoding transparent GIF…')
    const blob = await encodeTransparentGif(frames, (r) =>
      onProgress?.('encoding', r, 'Encoding transparent GIF…'),
    )
    saveAs(blob, `${baseName()}.gif`)
    return
  }

  if (format === 'apng') {
    onProgress?.('encoding', 0, 'Encoding APNG…')
    const blob = await encodeApng(frames, (r) =>
      onProgress?.('encoding', r, 'Encoding APNG…'),
    )
    // Some browsers treat APNG as image/png; .png extension is widely compatible
    saveAs(blob, `${baseName()}.png`)
    return
  }

  throw new Error(`Unsupported export format: ${format}`)
}
