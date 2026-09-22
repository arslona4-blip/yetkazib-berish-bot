import { themeById, type BaxtData } from './templates'

export const W = 1080
export const H = 1520

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
): string[] {
  const words = text.trim().split(/\s+/).filter(Boolean)
  if (!words.length) return []
  const lines: string[] = []
  let line = words[0]
  for (let i = 1; i < words.length; i++) {
    const test = `${line} ${words[i]}`
    if (ctx.measureText(test).width <= maxWidth) {
      line = test
    } else {
      lines.push(line)
      line = words[i]
    }
  }
  lines.push(line)
  return lines
}

function drawCorner(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  flipX: number,
  flipY: number,
  color: string,
) {
  ctx.save()
  ctx.translate(x, y)
  ctx.scale(flipX, flipY)
  ctx.strokeStyle = color
  ctx.lineWidth = 2.5
  ctx.beginPath()
  ctx.moveTo(0, 80)
  ctx.quadraticCurveTo(0, 0, 80, 0)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(14, 54)
  ctx.quadraticCurveTo(14, 14, 54, 14)
  ctx.stroke()
  // seal dot
  ctx.beginPath()
  ctx.arc(30, 30, 5, 0, Math.PI * 2)
  ctx.fillStyle = color
  ctx.fill()
  ctx.restore()
}

function drawOrnament(
  ctx: CanvasRenderingContext2D,
  cx: number,
  y: number,
  color: string,
) {
  ctx.save()
  ctx.strokeStyle = color
  ctx.fillStyle = color
  ctx.lineWidth = 1.6
  ctx.beginPath()
  ctx.moveTo(cx - 160, y)
  ctx.lineTo(cx - 36, y)
  ctx.moveTo(cx + 36, y)
  ctx.lineTo(cx + 160, y)
  ctx.stroke()
  // diamond seal
  ctx.beginPath()
  ctx.moveTo(cx, y - 10)
  ctx.lineTo(cx + 10, y)
  ctx.lineTo(cx, y + 10)
  ctx.lineTo(cx - 10, y)
  ctx.closePath()
  ctx.fill()
  // side flourishes
  for (const side of [-1, 1] as const) {
    ctx.beginPath()
    ctx.moveTo(cx + side * 48, y)
    ctx.quadraticCurveTo(cx + side * 62, y - 14, cx + side * 78, y - 2)
    ctx.stroke()
  }
  ctx.restore()
}

function fillBackground(
  ctx: CanvasRenderingContext2D,
  theme: ReturnType<typeof themeById>,
) {
  const g = ctx.createLinearGradient(0, 0, W, H)
  g.addColorStop(0, theme.bg0)
  g.addColorStop(0.5, theme.bg1)
  g.addColorStop(1, theme.bg0)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, W, H)

  const vg = ctx.createRadialGradient(
    W * 0.5,
    H * 0.32,
    30,
    W * 0.5,
    H * 0.48,
    H * 0.7,
  )
  vg.addColorStop(0, theme.paper)
  vg.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = vg
  ctx.fillRect(0, 0, W, H)

  // subtle cross-hatch dots
  ctx.fillStyle = theme.line
  for (let y = 90; y < H - 90; y += 52) {
    for (let x = 90; x < W - 90; x += 52) {
      if ((x + y) % 104 === 0) {
        ctx.beginPath()
        ctx.arc(x, y, 1.1, 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }
}

export function drawBaxt(ctx: CanvasRenderingContext2D, data: BaxtData, t = 0) {
  const theme = themeById(data.themeId)
  fillBackground(ctx, theme)

  const m = 52
  ctx.strokeStyle = theme.line
  ctx.lineWidth = 2
  ctx.strokeRect(m, m, W - m * 2, H - m * 2)
  ctx.strokeRect(m + 16, m + 16, W - (m + 16) * 2, H - (m + 16) * 2)

  drawCorner(ctx, m + 30, m + 30, 1, 1, theme.accent)
  drawCorner(ctx, W - m - 30, m + 30, -1, 1, theme.accent)
  drawCorner(ctx, m + 30, H - m - 30, 1, -1, theme.accent)
  drawCorner(ctx, W - m - 30, H - m - 30, -1, -1, theme.accent)

  const cx = W / 2
  let y = 168

  ctx.fillStyle = theme.accent
  ctx.font = '700 26px Outfit, sans-serif'
  ctx.textAlign = 'center'
  ctx.globalAlpha = 0.88 + Math.sin(t * 1.3) * 0.06
  ctx.fillText('B A X T N O M A', cx, y)
  ctx.globalAlpha = 1

  y += 40
  drawOrnament(ctx, cx, y, theme.accent)

  y += 100
  ctx.fillStyle = theme.ink
  ctx.font = 'italic 700 88px "Instrument Serif", Georgia, serif'
  const titleLines = wrapText(ctx, data.title || 'Baxtnoma', W - 220)
  for (const line of titleLines.slice(0, 3)) {
    ctx.fillText(line, cx, y)
    y += 94
  }

  y += 8
  drawOrnament(ctx, cx, y, theme.line)

  y += 72
  if (data.recipients.trim()) {
    ctx.fillStyle = theme.muted
    ctx.font = '600 28px Outfit, sans-serif'
    ctx.fillText('Hurmatli', cx, y)
    y += 56
    ctx.fillStyle = theme.ink
    ctx.font = '600 52px "Instrument Serif", Georgia, serif'
    for (const line of wrapText(ctx, data.recipients, W - 240).slice(0, 2)) {
      ctx.fillText(line, cx, y)
      y += 60
    }
  }

  if (data.blessing.trim()) {
    y += 36
    ctx.fillStyle = theme.muted
    ctx.font = 'italic 500 36px "Instrument Serif", Georgia, serif'
    for (const line of wrapText(ctx, data.blessing, W - 260).slice(0, 4)) {
      ctx.fillText(line, cx, y)
      y += 48
    }
  }

  const blockTop = Math.max(y + 40, 980)
  let dy = blockTop

  const details = [
    data.date.trim() ? { k: 'Sana', v: data.date.trim() } : null,
    data.place.trim() ? { k: 'Joy', v: data.place.trim() } : null,
  ].filter(Boolean) as { k: string; v: string }[]

  for (const d of details) {
    ctx.fillStyle = theme.accent
    ctx.font = '700 22px Outfit, sans-serif'
    ctx.fillText(d.k.toUpperCase(), cx, dy)
    dy += 40
    ctx.fillStyle = theme.ink
    ctx.font = '600 38px "Instrument Serif", Georgia, serif'
    for (const line of wrapText(ctx, d.v, W - 260).slice(0, 2)) {
      ctx.fillText(line, cx, dy)
      dy += 46
    }
    dy += 16
  }

  if (data.from.trim()) {
    dy += 12
    ctx.fillStyle = theme.muted
    ctx.font = '600 24px Outfit, sans-serif'
    ctx.fillText('Tabrik etuvchi', cx, dy)
    dy += 42
    ctx.fillStyle = theme.ink
    ctx.font = '600 40px "Instrument Serif", Georgia, serif'
    for (const line of wrapText(ctx, data.from, W - 240).slice(0, 2)) {
      ctx.fillText(line, cx, dy)
      dy += 48
    }
  }

  if (data.seal.trim()) {
    dy += 36
    ctx.fillStyle = theme.accent
    ctx.font = 'italic 500 30px "Instrument Serif", Georgia, serif'
    ctx.fillText(data.seal.trim(), cx, dy)
  }

  // bottom seal mark
  ctx.fillStyle = theme.line
  ctx.beginPath()
  ctx.moveTo(cx, H - 92)
  ctx.lineTo(cx + 8, H - 84)
  ctx.lineTo(cx, H - 76)
  ctx.lineTo(cx - 8, H - 84)
  ctx.closePath()
  ctx.fill()
}
