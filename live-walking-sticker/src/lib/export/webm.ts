/**
 * Transparent WebM export using Canvas + MediaRecorder (VP9/VP8 with alpha when supported).
 * Falls back to opaque WebM if the browser cannot encode alpha.
 *
 * Telegram video stickers prefer VP9 WebM with alpha, ≤512px on the long side,
 * short duration, and no audio — see telegram.ts for the constrained variant.
 */
import { computeWalkPose, drawStickerFrame } from '../animation'
import type { AnimationSettings } from '../../types'

export interface WebmExportOptions {
  sticker: HTMLImageElement | HTMLCanvasElement
  width: number
  height: number
  settings: Pick<AnimationSettings, 'speed' | 'distance' | 'size'>
  /** Total duration in ms (default one cycle ≈ 2400/speed). */
  durationMs?: number
  fps?: number
  /** Prefer codecs that support alpha. */
  preferAlpha?: boolean
  /** Bitrate hint. */
  bitsPerSecond?: number
  onProgress?: (ratio: number) => void
}

function pickMimeType(preferAlpha: boolean): string {
  const candidates = preferAlpha
    ? [
        'video/webm;codecs=vp9',
        'video/webm;codecs=vp8',
        'video/webm',
      ]
    : ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm']

  for (const type of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(type)) {
      return type
    }
  }
  throw new Error('WebM encoding is not supported in this browser')
}

export async function encodeWebm(opts: WebmExportOptions): Promise<Blob> {
  const {
    sticker,
    width,
    height,
    settings,
    fps = 24,
    preferAlpha = true,
    bitsPerSecond = 2_500_000,
    onProgress,
  } = opts

  const durationMs = opts.durationMs ?? 2400 / Math.max(0.05, settings.speed)

  const naturalWidth =
    'naturalWidth' in sticker ? sticker.naturalWidth || sticker.width : sticker.width
  const naturalHeight =
    'naturalHeight' in sticker ? sticker.naturalHeight || sticker.height : sticker.height

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d', { alpha: true })
  if (!ctx) throw new Error('Could not create WebM canvas context')

  const mimeType = pickMimeType(preferAlpha)
  const stream = canvas.captureStream(fps)
  const recorder = new MediaRecorder(stream, { mimeType, bitsPerSecond })
  const chunks: BlobPart[] = []

  recorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data)
  }

  const done = new Promise<Blob>((resolve, reject) => {
    recorder.onerror = () => reject(new Error('MediaRecorder failed'))
    recorder.onstop = () => {
      resolve(new Blob(chunks, { type: mimeType.split(';')[0] }))
    }
  })

  recorder.start(100)

  const halfTravel = (width * settings.distance) / 2
  const bob = Math.max(4, height * 0.015)
  const frameInterval = 1000 / fps
  const frameCount = Math.max(8, Math.round(durationMs / frameInterval))
  const start = performance.now()

  for (let i = 0; i < frameCount; i++) {
    const t = (i / frameCount) * durationMs
    // Speed already baked into durationMs; use speed=1 for pose sampling
    const pose = computeWalkPose(t, 1, halfTravel, bob)
    drawStickerFrame(
      ctx,
      sticker,
      width,
      height,
      pose,
      settings.size,
      naturalWidth,
      naturalHeight,
    )
    onProgress?.(i / frameCount)
    // Pace roughly real-time so captureStream grabs distinct frames
    const target = start + (i + 1) * frameInterval
    const wait = target - performance.now()
    if (wait > 0) await new Promise((r) => setTimeout(r, wait))
    else await new Promise((r) => requestAnimationFrame(() => r(undefined)))
  }

  // Final clear frame helps some decoders close alpha cleanly
  onProgress?.(0.98)
  await new Promise((r) => setTimeout(r, frameInterval))
  recorder.stop()
  stream.getTracks().forEach((t) => t.stop())

  const blob = await done
  onProgress?.(1)
  return blob
}
