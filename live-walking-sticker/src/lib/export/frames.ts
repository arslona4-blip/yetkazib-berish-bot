/**
 * Shared frame renderer for all export formats.
 * Renders the walking sticker onto an offscreen canvas with a transparent background.
 * Only translates the original cutout pixels — no facial alteration.
 */
import { computeWalkPose, drawStickerFrame } from '../animation'
import type { AnimationSettings } from '../../types'

export interface FrameRenderOptions {
  sticker: HTMLImageElement | HTMLCanvasElement
  width: number
  height: number
  settings: Pick<AnimationSettings, 'speed' | 'distance' | 'size'>
  /** Frames per second for the export. */
  fps?: number
  /** Duration of one full left→right→left cycle in ms (before speed). */
  cycleMsAtSpeed1?: number
  /** How many full cycles to capture (default 1). */
  cycles?: number
  onProgress?: (ratio: number) => void
}

export interface RenderedFrame {
  /** RGBA pixel buffer. */
  data: Uint8ClampedArray
  width: number
  height: number
  /** Delay for this frame in milliseconds. */
  delayMs: number
}

/**
 * Render a closed loop of walking frames into ImageData buffers.
 */
export async function renderWalkFrames(opts: FrameRenderOptions): Promise<RenderedFrame[]> {
  const {
    sticker,
    width,
    height,
    settings,
    fps = 20,
    cycleMsAtSpeed1 = 2400,
    cycles = 1,
    onProgress,
  } = opts

  const naturalWidth =
    'naturalWidth' in sticker ? sticker.naturalWidth || sticker.width : sticker.width
  const naturalHeight =
    'naturalHeight' in sticker ? sticker.naturalHeight || sticker.height : sticker.height

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d', { willReadFrequently: true, alpha: true })
  if (!ctx) throw new Error('Could not create export canvas context')

  // Speed is baked into total duration so pose sampling uses speed=1
  const cycleMs = cycleMsAtSpeed1 / Math.max(0.05, settings.speed)
  const totalMs = cycleMs * cycles
  const frameCount = Math.max(8, Math.round((totalMs / 1000) * fps))
  const delayMs = Math.round(1000 / fps)
  const halfTravel = (width * settings.distance) / 2
  const bob = Math.max(4, height * 0.015)

  const frames: RenderedFrame[] = []

  for (let i = 0; i < frameCount; i++) {
    const t = (i / frameCount) * totalMs
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

    const imageData = ctx.getImageData(0, 0, width, height)
    frames.push({
      data: imageData.data,
      width,
      height,
      delayMs,
    })

    onProgress?.(i / frameCount)

    if (i % 3 === 0) {
      await new Promise((r) => setTimeout(r, 0))
    }
  }

  onProgress?.(1)
  return frames
}
