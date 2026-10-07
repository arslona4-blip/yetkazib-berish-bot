/**
 * Animated PNG (APNG) export via upng-js.
 * Preserves full 8-bit alpha — best quality transparent sticker among raster formats.
 */
import UPNG from 'upng-js'
import type { RenderedFrame } from './frames'

export async function encodeApng(
  frames: RenderedFrame[],
  onProgress?: (ratio: number) => void,
): Promise<Blob> {
  if (frames.length === 0) throw new Error('No frames to encode')

  const { width, height } = frames[0]
  const buffers: ArrayBuffer[] = []
  const delays: number[] = []

  for (let i = 0; i < frames.length; i++) {
    // UPNG expects ArrayBuffer of RGBA for each frame
    const copy = new Uint8Array(frames[i].data).buffer
    buffers.push(copy)
    delays.push(frames[i].delayMs)
    onProgress?.((i + 1) / (frames.length + 1))
    if (i % 4 === 0) await new Promise((r) => setTimeout(r, 0))
  }

  // UPNG.encode(bufs, w, h, cnum, dels) — cnum=0 keeps full color
  const compressed = UPNG.encode(buffers, width, height, 0, delays)
  onProgress?.(1)
  return new Blob([compressed], { type: 'image/apng' })
}
