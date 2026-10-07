/**
 * Walking sticker animation math.
 *
 * Movement: LEFT → RIGHT → LEFT (continuous ping-pong).
 * Bobbing: subtle vertical sine for a natural walk feel.
 * Easing: smoothstep / cosine ease — no face/body distortion, only translation.
 */

export interface WalkPose {
  /** Horizontal offset from center, in pixels. */
  x: number
  /** Vertical bob offset in pixels (downward positive). */
  y: number
  /** 0–1 progress through one full left→right→left cycle. */
  cycle: number
}

/** Cosine ease for smooth direction changes (ease-in-out). */
export function easeInOutCosine(t: number): number {
  return 0.5 - 0.5 * Math.cos(Math.PI * clamp01(t))
}

function clamp01(t: number): number {
  return Math.min(1, Math.max(0, t))
}

/**
 * Compute sticker pose for a given elapsed time.
 *
 * @param elapsedMs - milliseconds since animation start (or resume)
 * @param speed - multiplier (1 = ~2.4s for a full round trip)
 * @param halfTravelPx - max |x| offset from center
 * @param bobAmplitudePx - peak vertical bob
 */
export function computeWalkPose(
  elapsedMs: number,
  speed: number,
  halfTravelPx: number,
  bobAmplitudePx = 6,
): WalkPose {
  // Full cycle duration at speed=1 (left→right→left)
  const cycleMs = 2400 / Math.max(0.05, speed)
  const cycle = (elapsedMs % cycleMs) / cycleMs

  // Ping-pong: 0→0.5 goes left→right, 0.5→1 goes right→left
  const goingRight = cycle < 0.5
  const local = goingRight ? cycle * 2 : (cycle - 0.5) * 2
  const eased = easeInOutCosine(local)
  const x = goingRight
    ? -halfTravelPx + eased * (2 * halfTravelPx)
    : halfTravelPx - eased * (2 * halfTravelPx)

  // Two bob cycles per half-trip ≈ four steps per round trip
  const bob = Math.sin(cycle * Math.PI * 4) * bobAmplitudePx

  return { x, y: bob, cycle }
}

/**
 * Draw the sticker onto a canvas with transparent clear + translational walk pose.
 * Does not scale non-uniformly or warp the bitmap — only uniform scale + translate.
 */
export function drawStickerFrame(
  ctx: CanvasRenderingContext2D,
  sticker: CanvasImageSource,
  canvasW: number,
  canvasH: number,
  pose: WalkPose,
  sizeFraction: number,
  naturalWidth: number,
  naturalHeight: number,
): void {
  ctx.clearRect(0, 0, canvasW, canvasH)

  const maxH = canvasH * sizeFraction
  const maxW = canvasW * 0.9
  const scale = Math.min(maxH / naturalHeight, maxW / naturalWidth)
  const drawW = naturalWidth * scale
  const drawH = naturalHeight * scale

  const cx = canvasW / 2 + pose.x
  const cy = canvasH / 2 + pose.y

  ctx.drawImage(sticker, cx - drawW / 2, cy - drawH / 2, drawW, drawH)
}

/** Fit export canvas dimensions to a square (Telegram-friendly) or free aspect. */
export function resolveExportSize(
  naturalWidth: number,
  naturalHeight: number,
  sizeFraction: number,
  distance: number,
  maxSide = 512,
): { width: number; height: number } {
  const aspect = naturalWidth / naturalHeight
  const stickerH = maxSide * sizeFraction
  const stickerW = stickerH * aspect
  const travel = maxSide * distance
  const neededW = Math.ceil(stickerW + travel + 16)
  const neededH = Math.ceil(stickerH + 24)
  const side = Math.min(maxSide, Math.max(neededW, neededH, 128))
  return { width: side, height: side }
}
