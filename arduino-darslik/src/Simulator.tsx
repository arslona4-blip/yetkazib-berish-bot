import { useEffect, useRef, useState, type ReactNode } from 'react'
import type { SimKind } from './lessons'

type Props = { kind: SimKind }

export function Simulator({ kind }: Props) {
  switch (kind) {
    case 'install':
      return <InstallSim />
    case 'blink':
      return <BlinkSim />
    case 'button':
      return <ButtonSim />
    case 'pwm':
      return <PwmSim />
    case 'pot':
      return <PotSim />
    case 'buzzer':
      return <BuzzerSim />
    case 'servo':
      return <ServoSim />
    case 'ultrasonic':
      return <UltrasonicSim />
    case 'traffic':
      return <TrafficSim />
    default:
      return null
  }
}

function BoardShell({
  title,
  children,
  caption,
}: {
  title: string
  children: ReactNode
  caption?: string
}) {
  return (
    <div className="sim">
      <div className="sim-head">
        <strong>Simulyator</strong>
        <span>{title}</span>
      </div>
      <div className="sim-stage">{children}</div>
      {caption ? <p className="sim-cap">{caption}</p> : null}
    </div>
  )
}

function InstallSim() {
  const checks = [
    'Arduino IDE yuklab olindi (arduino.cc)',
    'USB kabel bilan plata ulandi',
    'Tools → Board to‘g‘ri tanlandi',
    'Tools → Port ko‘rinadi',
    'Blink Upload → Done uploading',
  ]
  const [ok, setOk] = useState<boolean[]>(() => checks.map(() => false))
  const done = ok.filter(Boolean).length

  return (
    <BoardShell
      title="O‘rnatish checklist"
      caption={`${done}/${checks.length} tayyor — hammasi ✓ bo‘lsa IDE tayyor.`}
    >
      <ul className="check-list">
        {checks.map((c, i) => (
          <li key={c}>
            <label>
              <input
                type="checkbox"
                checked={ok[i]}
                onChange={() =>
                  setOk((prev) => prev.map((v, j) => (j === i ? !v : v)))
                }
              />
              <span>{c}</span>
            </label>
          </li>
        ))}
      </ul>
    </BoardShell>
  )
}

function BlinkSim() {
  const [ms, setMs] = useState(500)
  const [on, setOn] = useState(false)

  useEffect(() => {
    const id = window.setInterval(() => setOn((v) => !v), Math.max(80, ms))
    return () => window.clearInterval(id)
  }, [ms])

  return (
    <BoardShell title="LED Blink" caption={`delay(${ms}) — koddagi kabi miltillaydi.`}>
      <div className="board">
        <div className={`led${on ? ' on' : ''}`} />
        <p className="mono">pin 13 · {on ? 'HIGH' : 'LOW'}</p>
        <label className="slider-label">
          delay (ms)
          <input
            type="range"
            min={100}
            max={1500}
            step={50}
            value={ms}
            onChange={(e) => setMs(Number(e.target.value))}
          />
        </label>
      </div>
    </BoardShell>
  )
}

function ButtonSim() {
  const [pressed, setPressed] = useState(false)
  return (
    <BoardShell
      title="Tugma + LED"
      caption="INPUT_PULLUP: bosilganda LOW → LED yonadi."
    >
      <div className="board row">
        <button
          type="button"
          className={`hw-btn${pressed ? ' down' : ''}`}
          onPointerDown={() => setPressed(true)}
          onPointerUp={() => setPressed(false)}
          onPointerLeave={() => setPressed(false)}
        >
          Tugma
        </button>
        <div className={`led${pressed ? ' on' : ''}`} />
      </div>
      <p className="mono center">
        BTN={pressed ? 'LOW' : 'HIGH'} · LED={pressed ? 'HIGH' : 'LOW'}
      </p>
    </BoardShell>
  )
}

function PwmSim() {
  const [v, setV] = useState(120)
  return (
    <BoardShell title="PWM yorqinlik" caption={`analogWrite(9, ${v})`}>
      <div className="board">
        <div className="led on" style={{ opacity: 0.15 + (v / 255) * 0.85 }} />
        <label className="slider-label">
          0–255
          <input
            type="range"
            min={0}
            max={255}
            value={v}
            onChange={(e) => setV(Number(e.target.value))}
          />
        </label>
      </div>
    </BoardShell>
  )
}

function PotSim() {
  const [raw, setRaw] = useState(512)
  const pwm = Math.round((raw / 1023) * 255)
  return (
    <BoardShell title="Potensiometr A0" caption={`map(${raw},0,1023,0,255) → ${pwm}`}>
      <div className="board">
        <div className="led on" style={{ opacity: 0.15 + (pwm / 255) * 0.85 }} />
        <label className="slider-label">
          Pot (A0)
          <input
            type="range"
            min={0}
            max={1023}
            value={raw}
            onChange={(e) => setRaw(Number(e.target.value))}
          />
        </label>
        <p className="mono">A0={raw} · PWM={pwm}</p>
      </div>
    </BoardShell>
  )
}

function BuzzerSim() {
  const ctxRef = useRef<AudioContext | null>(null)

  function play() {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (!Ctx) return
    if (!ctxRef.current) ctxRef.current = new Ctx()
    const ctx = ctxRef.current
    const notes = [523, 659, 784]
    let t = ctx.currentTime
    for (const f of notes) {
      const o = ctx.createOscillator()
      const g = ctx.createGain()
      o.frequency.value = f
      o.type = 'square'
      g.gain.value = 0.04
      o.connect(g)
      g.connect(ctx.destination)
      o.start(t)
      o.stop(t + 0.18)
      t += 0.25
    }
  }

  return (
    <BoardShell title="Piezo tone()" caption="Brauzerda ohang — haqiqiy piezo pin 8 da.">
      <div className="board">
        <button type="button" className="btn primary" onClick={play}>
          Melodiya chalish
        </button>
        <p className="mono">523 → 659 → 784 Hz</p>
      </div>
    </BoardShell>
  )
}

function ServoSim() {
  const [angle, setAngle] = useState(90)
  return (
    <BoardShell title="Servo 0–180°" caption={`s.write(${angle})`}>
      <div className="board">
        <div className="servo">
          <div className="servo-arm" style={{ transform: `rotate(${angle - 90}deg)` }} />
        </div>
        <label className="slider-label">
          Burchak
          <input
            type="range"
            min={0}
            max={180}
            value={angle}
            onChange={(e) => setAngle(Number(e.target.value))}
          />
        </label>
      </div>
    </BoardShell>
  )
}

function UltrasonicSim() {
  const [cm, setCm] = useState(30)
  return (
    <BoardShell title="HC-SR04" caption={`Masofa ≈ ${cm} cm`}>
      <div className="board sonar">
        <div className="sensor" />
        <div className="beam" style={{ width: `${Math.min(100, cm)}%` }} />
        <div className="object" style={{ left: `calc(${Math.min(92, cm)}% - 12px)` }} />
        <label className="slider-label">
          Obyekt masofasi (cm)
          <input
            type="range"
            min={2}
            max={100}
            value={cm}
            onChange={(e) => setCm(Number(e.target.value))}
          />
        </label>
      </div>
    </BoardShell>
  )
}

function TrafficSim() {
  const [phase, setPhase] = useState(0)

  useEffect(() => {
    const times = [3000, 800, 3000, 800]
    const id = window.setTimeout(
      () => setPhase((p) => (p + 1) % 4),
      times[phase],
    )
    return () => window.clearTimeout(id)
  }, [phase])

  const lights =
    phase === 0
      ? [1, 0, 0]
      : phase === 1
        ? [1, 1, 0]
        : phase === 2
          ? [0, 0, 1]
          : [0, 1, 0]

  return (
    <BoardShell title="Svetofor sikli" caption="Qizil → sariq → yashil → sariq">
      <div className="traffic">
        <div className={`t-led red${lights[0] ? ' on' : ''}`} />
        <div className={`t-led yellow${lights[1] ? ' on' : ''}`} />
        <div className={`t-led green${lights[2] ? ' on' : ''}`} />
      </div>
    </BoardShell>
  )
}
