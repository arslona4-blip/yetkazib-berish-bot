/**
 * Background removal — identity-preserving.
 *
 * IMPORTANT: This module only removes the background via alpha matting.
 * It never regenerates, redraws, beautifies, or alters facial pixels.
 * The returned PNG keeps the original subject RGB values intact.
 */
import { preload, removeBackground as imglyRemoveBackground } from '@imgly/background-removal'

export type RemovalProgress = (message: string, ratio?: number) => void

let preloadPromise: Promise<void> | null = null

/** Warm up ONNX / WASM assets so the first removal is faster. */
export function preloadBackgroundRemoval(onProgress?: RemovalProgress): Promise<void> {
  if (!preloadPromise) {
    preloadPromise = preload({
      debug: false,
      model: 'isnet_fp16',
      progress: (key, current, total) => {
        const ratio = total > 0 ? current / total : undefined
        onProgress?.(`Loading model (${key})…`, ratio)
      },
    }).then(() => undefined)
  }
  return preloadPromise
}

/**
 * Remove the background from an uploaded image Blob.
 * Returns a PNG Blob with a transparent background and unchanged subject pixels.
 */
export async function removeBackground(
  imageBlob: Blob,
  onProgress?: RemovalProgress,
): Promise<Blob> {
  onProgress?.('Preparing image…', 0)

  await preloadBackgroundRemoval(onProgress)

  onProgress?.('Removing background (original face preserved)…', 0.35)

  const result = await imglyRemoveBackground(imageBlob, {
    debug: false,
    model: 'isnet_fp16',
    output: {
      format: 'image/png',
      quality: 1,
    },
    progress: (key: string, current: number, total: number) => {
      const ratio = total > 0 ? 0.35 + (current / total) * 0.6 : 0.5
      onProgress?.(`Processing (${key})…`, ratio)
    },
  })

  onProgress?.('Background removed', 1)
  return result
}

/** Load a Blob into an HTMLImageElement (decoded). Keeps the object URL alive on the image. */
export function blobToImage(blob: Blob): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob)
    const img = new Image()
    img.onload = () => {
      // Retain URL for the lifetime of the image so canvas drawImage stays valid
      ;(img as HTMLImageElement & { __objectUrl?: string }).__objectUrl = url
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to decode image'))
    }
    img.src = url
  })
}

/** Validate that a File is a PNG or JPEG. */
export function isSupportedImageFile(file: File): boolean {
  const type = file.type.toLowerCase()
  if (type === 'image/png' || type === 'image/jpeg' || type === 'image/jpg') {
    return true
  }
  const name = file.name.toLowerCase()
  return name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg')
}
