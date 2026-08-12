import type { Scene } from './stories'

const W = 720
const H = 1280

function moodColors(mood: Scene['mood']): [string, string, string] {
  switch (mood) {
    case 'dawn':
      return ['#ffe8c8', '#ffb4d9', '#9ecbff']
    case 'garden':
      return ['#d8ffe8', '#b4f0c8', '#fff3a8']
    case 'magic':
      return ['#1a1440', '#4a2d8a', '#ffd56a']
    case 'play':
      return ['#ffe0f0', '#c4b5ff', '#9ef0ff']
    case 'school':
      return ['#e8f4ff', '#b8d4ff', '#ffe6a8']
    case 'sunset':
      return ['#ffd1a8', '#ff8fab', '#6b5b95']
  }
}

export function drawScene(
  ctx: CanvasRenderingContext2D,
  scene: Scene,
  t: number,
  name: string,
) {
  const [c1, c2, c3] = moodColors(scene.mood)
  const g = ctx.createLinearGradient(0, 0, 0, H)
  g.addColorStop(0, c1)
  g.addColorStop(0.55, c2)
  g.addColorStop(1, c3)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, W, H)

  // ken burns zoom
  const zoom = 1 + Math.sin(t * 0.4) * 0.03 + t * 0.01
  ctx.save()
  ctx.translate(W / 2, H / 2)
  ctx.scale(zoom, zoom)
  ctx.translate(-W / 2, -H / 2)

  // soft blobs
  for (let i = 0; i < 6; i++) {
    const x = 80 + ((i * 137) % (W - 160))
    const y = 160 + ((i * 211) % (H - 400))
    const r = 40 + (i % 3) * 28
    ctx.beginPath()
    ctx.fillStyle = `rgba(255,255,255,${0.12 + (i % 3) * 0.04})`
    ctx.arc(x + Math.sin(t + i) * 12, y + Math.cos(t * 0.7 + i) * 10, r, 0, Math.PI * 2)
    ctx.fill()
  }

  // ground
  ctx.fillStyle = 'rgba(255,255,255,0.25)'
  ctx.beginPath()
  ctx.ellipse(W / 2, H * 0.72, 260, 70, 0, 0, Math.PI * 2)
  ctx.fill()

  // character circle
  const bob = Math.sin(t * 2.2) * 14
  ctx.beginPath()
  ctx.fillStyle = '#fff'
  ctx.arc(W / 2, H * 0.48 + bob, 110, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.fillStyle = 'rgba(255,126,182,0.2)'
  ctx.arc(W / 2, H * 0.48 + bob, 96, 0, Math.PI * 2)
  ctx.fill()

  ctx.font = '120px serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(scene.emoji, W / 2, H * 0.48 + bob)

  ctx.restore()

  // title card
  ctx.fillStyle = 'rgba(26, 20, 40, 0.55)'
  roundRect(ctx, 48, H - 340, W - 96, 240, 28)
  ctx.fill()

  ctx.fillStyle = '#fff'
  ctx.font = '800 36px Nunito, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText(scene.title, 80, H - 280)

  ctx.font = '700 28px Nunito, sans-serif'
  wrapText(ctx, scene.narrate, 80, H - 220, W - 160, 36)

  ctx.font = '700 22px Nunito, sans-serif'
  ctx.fillStyle = 'rgba(255,255,255,0.75)'
  ctx.fillText(`Kichkintoy AI · ${name}`, 80, H - 120)
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
) {
  const words = text.split(' ')
  let line = ''
  let yy = y
  for (const word of words) {
    const test = line ? `${line} ${word}` : word
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, yy)
      line = word
      yy += lineHeight
    } else {
      line = test
    }
  }
  if (line) ctx.fillText(line, x, yy)
}

export { W, H }
