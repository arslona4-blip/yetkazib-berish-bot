import * as faceapi from '@vladmandic/face-api'

let ready = false

/** Electron query ?models=file:///.../ yoki web dagi ./models */
export function resolveModelsBase(): string {
  try {
    const fromQuery = new URLSearchParams(window.location.search).get('models')
    if (fromQuery) {
      return decodeURIComponent(fromQuery).replace(/\/?$/, '')
    }
  } catch {
    // ignore
  }
  try {
    return new URL('models', window.location.href).href.replace(/\/?$/, '')
  } catch {
    return './models'
  }
}

export async function loadFaceModels(baseUrl = resolveModelsBase()) {
  if (ready) return
  const base = baseUrl.replace(/\/?$/, '')
  await Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri(base),
    faceapi.nets.faceLandmark68TinyNet.loadFromUri(base),
    faceapi.nets.faceRecognitionNet.loadFromUri(base),
  ])
  ready = true
}

export function isFaceReady() {
  return ready
}

const detectorOpts = new faceapi.TinyFaceDetectorOptions({
  inputSize: 320,
  scoreThreshold: 0.5,
})

export async function detectDescriptor(
  input: HTMLVideoElement | HTMLCanvasElement | HTMLImageElement,
): Promise<Float32Array | null> {
  const result = await faceapi
    .detectSingleFace(input, detectorOpts)
    .withFaceLandmarks(true)
    .withFaceDescriptor()
  return result?.descriptor ?? null
}

export async function detectAll(
  input: HTMLVideoElement | HTMLCanvasElement,
) {
  return faceapi
    .detectAllFaces(input, detectorOpts)
    .withFaceLandmarks(true)
    .withFaceDescriptors()
}

export function matchPerson(
  descriptor: Float32Array,
  people: { id: string; name: string; descriptor: number[] }[],
  threshold = 0.48,
): { id: string; name: string; distance: number } | null {
  let best: { id: string; name: string; distance: number } | null = null
  for (const p of people) {
    const dist = faceapi.euclideanDistance(
      descriptor,
      Float32Array.from(p.descriptor),
    )
    if (dist < threshold && (!best || dist < best.distance)) {
      best = { id: p.id, name: p.name, distance: dist }
    }
  }
  return best
}

export function captureThumb(video: HTMLVideoElement, size = 96): string {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''
  const vw = video.videoWidth
  const vh = video.videoHeight
  const side = Math.min(vw, vh)
  const sx = (vw - side) / 2
  const sy = (vh - side) / 2
  ctx.drawImage(video, sx, sy, side, side, 0, 0, size, size)
  return canvas.toDataURL('image/jpeg', 0.7)
}
