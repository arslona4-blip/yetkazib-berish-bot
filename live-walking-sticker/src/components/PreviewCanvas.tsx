import { useEffect, useRef } from 'react'
import { computeWalkPose, drawStickerFrame } from '../lib/animation'
import type { AnimationSettings } from '../types'

interface PreviewCanvasProps {
  sticker: HTMLImageElement | null
  settings: AnimationSettings
}

/**
 * Large live preview with checkerboard transparency and continuous walk loop.
 * Animation logic: see src/lib/animation.ts
 */
export function PreviewCanvas({ sticker, settings }: PreviewCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  const elapsedRef = useRef(0)
  const lastTsRef = useRef<number | null>(null)
  const settingsRef = useRef(settings)
  const stickerRef = useRef(sticker)

  settingsRef.current = settings
  stickerRef.current = sticker

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
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(wrap)

    const tick = (ts: number) => {
      if (!running) return
      const s = settingsRef.current
      const img = stickerRef.current

      if (lastTsRef.current == null) lastTsRef.current = ts
      const dt = ts - lastTsRef.current
      lastTsRef.current = ts

      if (s.playing && img) {
        elapsedRef.current += dt
      }

      const cssW = canvas.clientWidth
      const cssH = canvas.clientHeight
      ctx.clearRect(0, 0, cssW, cssH)

      if (img) {
        const halfTravel = (cssW * s.distance) / 2
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

  // Reset clock when a new sticker arrives
  useEffect(() => {
    elapsedRef.current = 0
    lastTsRef.current = null
  }, [sticker])

  return (
    <section className="panel preview-panel">
      <div className="preview-header">
        <h2>Preview</h2>
        <span className="pill">{settings.loop ? 'Loop on' : 'Loop off'}</span>
      </div>
      <div ref={wrapRef} className="preview-stage checkerboard" aria-label="Sticker preview">
        <canvas ref={canvasRef} className="preview-canvas" />
        {!sticker && (
          <div className="preview-placeholder">
            Upload a photo to see your walking sticker
          </div>
        )}
      </div>
    </section>
  )
}
