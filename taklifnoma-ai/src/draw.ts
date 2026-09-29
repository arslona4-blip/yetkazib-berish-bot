import { themeById, type InviteData } from './templates'

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
  ctx.moveTo(0, 72)
  ctx.quadraticCurveTo(0, 0, 72, 0)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(12, 48)
  ctx.quadraticCurveTo(12, 12, 48, 12)
  ctx.stroke()
  ctx.beginPath()
  ctx.arc(28, 28, 4, 0, Math.PI * 2)
  ctx.fillStyle = color
  ctx.fill()
  ctx.restore()
}

function drawLeafRow(
  ctx: CanvasRenderingContext2D,
  cx: number,
  y: number,
  color: string,
) {
  ctx.save()
  ctx.strokeStyle = color
  ctx.fillStyle = color
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(cx - 140, y)
  ctx.lineTo(cx - 28, y)
  ctx.moveTo(cx + 28, y)
  ctx.lineTo(cx + 140, y)
  ctx.stroke()
  // center diamond
  ctx.beginPath()
  ctx.moveTo(cx, y - 8)
  ctx.lineTo(cx + 8, y)
  ctx.lineTo(cx, y + 8)
  ctx.lineTo(cx - 8, y)
  ctx.closePath()
  ctx.fill()
  // tiny leaves
  for (const side of [-1, 1] as const) {
    ctx.beginPath()
    ctx.ellipse(cx + side * 56, y, 14, 6, side * 0.5, 0, Math.PI * 2)
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
  g.addColorStop(0.55, theme.bg1)
  g.addColorStop(1, theme.bg0)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, W, H)

  // soft vignette / atmosphere
  const vg = ctx.createRadialGradient(W * 0.5, H * 0.35, 40, W * 0.5, H * 0.5, H * 0.72)
  vg.addColorStop(0, theme.paper)
  vg.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = vg
  ctx.fillRect(0, 0, W, H)

  // subtle pattern dots
  ctx.fillStyle = theme.line
  for (let y = 80; y < H - 80; y += 56) {
    for (let x = 80; x < W - 80; x += 56) {
      if ((x + y) % 112 === 0) {
        ctx.beginPath()
        ctx.arc(x, y, 1.2, 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }
}

export function drawInvite(
  ctx: CanvasRenderingContext2D,
  data: InviteData,
  t = 0,
) {
  const theme = themeById(data.themeId)
  fillBackground(ctx, theme)

  // outer frame
  const m = 48
  ctx.strokeStyle = theme.line
  ctx.lineWidth = 2
  ctx.strokeRect(m, m, W - m * 2, H - m * 2)
  ctx.strokeRect(m + 14, m + 14, W - (m + 14) * 2, H - (m + 14) * 2)

  drawCorner(ctx, m + 28, m + 28, 1, 1, theme.accent)
  drawCorner(ctx, W - m - 28, m + 28, -1, 1, theme.accent)
  drawCorner(ctx, m + 28, H - m - 28, 1, -1, theme.accent)
  drawCorner(ctx, W - m - 28, H - m - 28, -1, -1, theme.accent)

  const cx = W / 2
  let y = 160

  // brand whisper
  ctx.fillStyle = theme.accent
  ctx.font = '600 28px Figtree, sans-serif'
  ctx.textAlign = 'center'
  ctx.globalAlpha = 0.9 + Math.sin(t * 1.4) * 0.05
  ctx.fillText('TAKLIFNOMA', cx, y)
  ctx.globalAlpha = 1

  y += 36
  drawLeafRow(ctx, cx, y, theme.accent)

  y += 90
  // main title
  ctx.fillStyle = theme.ink
  ctx.font = 'italic 700 92px Cormorant, serif'
  const titleLines = wrapText(ctx, data.title || 'Taklifnoma', W - 220)
  for (const line of titleLines.slice(0, 3)) {
    ctx.fillText(line, cx, y)
    y += 96
  }

  y += 10
  drawLeafRow(ctx, cx, y, theme.line)

  y += 70
  if (data.guest.trim()) {
    ctx.fillStyle = theme.muted
    ctx.font = '500 30px Figtree, sans-serif'
    ctx.fillText('Hurmatli', cx, y)
    y += 52
    ctx.fillStyle = theme.ink
    ctx.font = '600 48px Cormorant, serif'
    for (const line of wrapText(ctx, data.guest, W - 240).slice(0, 2)) {
      ctx.fillText(line, cx, y)
      y += 56
    }
    y += 18
  }

  if (data.hosts.trim()) {
    ctx.fillStyle = theme.muted
    ctx.font = '500 28px Figtree, sans-serif'
    ctx.fillText('Taklif etuvchilar', cx, y)
    y += 48
    ctx.fillStyle = theme.ink
    ctx.font = '600 44px Cormorant, serif'
    for (const line of wrapText(ctx, data.hosts, W - 240).slice(0, 2)) {
      ctx.fillText(line, cx, y)
      y += 52
    }
  }

  y += 36
  // details block
  const blockTop = Math.max(y, 920)
  const details = [
    data.date.trim() ? { k: 'Sana', v: data.date.trim() } : null,
    data.time.trim() ? { k: 'Vaqt', v: data.time.trim() } : null,
    data.place.trim() ? { k: 'Manzil', v: data.place.trim() } : null,
  ].filter(Boolean) as { k: string; v: string }[]

  let dy = blockTop
  for (const d of details) {
    ctx.fillStyle = theme.accent
    ctx.font = '700 24px Figtree, sans-serif'
    ctx.fillText(d.k.toUpperCase(), cx, dy)
    dy += 42
    ctx.fillStyle = theme.ink
    ctx.font = '600 40px Cormorant, serif'
    for (const line of wrapText(ctx, d.v, W - 260).slice(0, 2)) {
      ctx.fillText(line, cx, dy)
      dy += 48
    }
    dy += 18
  }

  if (data.note.trim()) {
    dy += 8
    ctx.fillStyle = theme.muted
    ctx.font = 'italic 500 32px Cormorant, serif'
    for (const line of wrapText(ctx, data.note, W - 280).slice(0, 3)) {
      ctx.fillText(line, cx, dy)
      dy += 42
    }
  }

  if (data.phone.trim()) {
    dy += 28
    ctx.fillStyle = theme.accent
    ctx.font = '600 28px Figtree, sans-serif'
    ctx.fillText(`Bog‘lanish: ${data.phone.trim()}`, cx, dy)
  }

  // bottom mark
  ctx.fillStyle = theme.line
  ctx.font = '500 22px Figtree, sans-serif'
  ctx.fillText('•', cx, H - 78)
}
