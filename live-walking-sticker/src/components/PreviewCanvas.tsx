import { useEffect, useRef } from 'react'
import { computeWalkPose, drawStickerFrame } from '../lib/animation'
import type { AnimationSettings } from '../types'

interface PreviewCanvasProps {
  /** Object URL or data URL of the transparent cutout PNG. */
  stickerUrl: string | null
  settings: AnimationSettings
}

/**
 * Large live preview with checkerboard transparency and continuous walk loop.
 * Animation logic: see src/lib/animation.ts
 *
 * Loads the cutout from a URL (not a detached HTMLImageElement) so decoding
 * stays reliable across React Strict Mode remounts.
 */
export function PreviewCanvas({ stickerUrl, settings }: PreviewCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  const elapsedRef = useRef(0)
  const lastTsRef = useRef<number | null>(null)
  const settingsRef = useRef(settings)
  const imageRef = useRef<HTMLImageElement | null>(null)

  settingsRef.current = settings

  // Decode sticker whenever the cutout URL changes
  useEffect(() => {
    imageRef.current = null
    elapsedRef.current = 0
    lastTsRef.current = null
    if (!stickerUrl) return

    let cancelled = false
    const img = new Image()
    img.decoding = 'async'
    img.onload = () => {
      if (!cancelled) imageRef.current = img
    }
    img.onerror = () => {
      if (!cancelled) imageRef.current = null
    }
    img.src = stickerUrl

    return () => {
      cancelled = true
    }
  }, [stickerUrl])

  // Animation loop — translation only, never warps the bitmap
  useEffect(() => {
    const canvas = canvasRef.current
    const wrap = wrapRef.current
    if (!canvas || !wrap) return

    const ctx = canvas.getContext('2d', { alpha: true })
    if (!ctx) return

    let raf = 0
    let running = true

    const resize = () => {
      const rect = wrap.getBoundingClientRect()
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const cssW = Math.max(280, Math.floor(rect.width))
      const cssH = Math.max(280, Math.floor(rect.height))
      canvas.width = Math.floor(cssW * dpr)
      canvas.height = Math.floor(cssH * dpr)
      canvas.style.width = `${cssW}px`
      canvas.style.height = `${cssH}px`
      // Reset transform after buffer resize
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(wrap)

    const tick = (ts: number) => {
      if (!running) return
      const s = settingsRef.current
      const img = imageRef.current

      if (lastTsRef.current == null) lastTsRef.current = ts
      const dt = ts - lastTsRef.current
      lastTsRef.current = ts

      if (s.playing && s.loop && img) {
        elapsedRef.current += dt
      } else if (s.playing && img && !s.loop) {
        // Single cycle then stop
        const cycleMs = 2400 / Math.max(0.05, s.speed)
        if (elapsedRef.current < cycleMs) {
          elapsedRef.current = Math.min(cycleMs, elapsedRef.current + dt)
        }
      }

      const cssW = canvas.clientWidth || 280
      const cssH = canvas.clientHeight || 280
      ctx.clearRect(0, 0, cssW, cssH)

      if (img && img.naturalWidth > 0 && img.naturalHeight > 0) {
        // Clamp travel so the sticker stays mostly on-screen
        const maxH = cssH * s.size
        const maxW = cssW * 0.9
        const scale = Math.min(maxH / img.naturalHeight, maxW / img.naturalWidth)
        const drawW = img.naturalWidth * scale
        const maxHalfTravel = Math.max(0, (cssW - drawW) / 2 - 4)
        const halfTravel = Math.min((cssW * s.distance) / 2, maxHalfTravel)
        const bob = Math.max(4, cssH * 0.012)
        const pose = computeWalkPose(elapsedRef.current, s.speed, halfTravel, bob)
        drawStickerFrame(
          ctx,
          img,
          cssW,
          cssH,
          pose,
          s.size,
          img.naturalWidth,
          img.naturalHeight,
        )
      }

      raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)

    return () => {
      running = false
      cancelAnimationFrame(raf)
      ro.disconnect()
    }
  }, [])

  return (
    <section className="panel preview-panel">
      <div className="preview-header">
        <h2>Preview</h2>
        <span className="pill">{settings.loop ? 'Loop on' : 'Loop off'}</span>
      </div>
      <div ref={wrapRef} className="preview-stage checkerboard" aria-label="Sticker preview">
        <canvas ref={canvasRef} className="preview-canvas" />
        {!stickerUrl && (
          <div className="preview-placeholder">
            Upload a photo to see your walking sticker
          </div>
        )}
      </div>
    </section>
  )
}
