/**
 * Transparent animated GIF export via gifenc.
 * Uses RGBA quantization so the checkerboard-free transparent background is preserved.
 */
import { GIFEncoder, quantize, applyPalette } from 'gifenc'
import type { RenderedFrame } from './frames'

// gifenc ships without complete TS types in some builds
type Palette = number[][]

export async function encodeTransparentGif(
  frames: RenderedFrame[],
  onProgress?: (ratio: number) => void,
): Promise<Blob> {
  if (frames.length === 0) throw new Error('No frames to encode')

  const gif = GIFEncoder()
  const { width, height } = frames[0]

  for (let i = 0; i < frames.length; i++) {
    const frame = frames[i]
    const rgba = frame.data

    // Quantize with alpha so transparent pixels map to a clear palette entry
    const palette = quantize(rgba, 256, {
      format: 'rgba4444',
      oneBitAlpha: true,
      clearAlpha: true,
      clearAlphaThreshold: 0x80,
      clearAlphaColor: 0x00,
    }) as Palette

    const index = applyPalette(rgba, palette, 'rgba4444')

    // Find a fully transparent palette index (alpha channel = 0)
    let transparentIndex = palette.findIndex((c) => (c.length > 3 ? c[3] === 0 : false))
    if (transparentIndex < 0) transparentIndex = 0

    gif.writeFrame(index, width, height, {
      palette,
      delay: frame.delayMs,
      transparent: true,
      transparentIndex,
      dispose: 2,
    })

    onProgress?.((i + 1) / frames.length)
    if (i % 4 === 0) await new Promise((r) => setTimeout(r, 0))
  }

  gif.finish()
  const bytes = gif.bytes()
  // Copy into a plain ArrayBuffer for BlobPart typing compatibility
  const buffer = new ArrayBuffer(bytes.byteLength)
  new Uint8Array(buffer).set(bytes)
  return new Blob([buffer], { type: 'image/gif' })
}
