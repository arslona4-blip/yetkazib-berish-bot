import { useEffect, useState, type ReactNode } from 'react'
import type { SimKind } from './lessons'

type Props = { kind: SimKind }

export function Simulator({ kind }: Props) {
  switch (kind) {
    case 'intro':
      return <IntroSim />
    case 'blink':
      return <IntroSim />
    case 'traffic':
      return <TrafficSim />
    case 'pwm':
      return <PwmSim />
    case 'serial':
      return <SerialSim />
    case 'vars':
      return <VarsSim />
    case 'ifel':
      return <IfSim />
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

function IntroSim() {
  const [mode, setMode] = useState<'one' | 'parallel'>('one')
  const [on, setOn] = useState(false)
  useEffect(() => {
    const id = window.setInterval(() => setOn((v) => !v), 1000)
    return () => window.clearInterval(id)
  }, [])

  return (
    <BoardShell
      title="LED + maket"
      caption="Chap: Arduino pin → rezistor → LED → GND"
    >
      <div className="mode-row">
        <button
          type="button"
          className={`chip${mode === 'one' ? ' on' : ''}`}
          onClick={() => setMode('one')}
        >
          1 LED
        </button>
        <button
          type="button"
          className={`chip${mode === 'parallel' ? ' on' : ''}`}
          onClick={() => setMode('parallel')}
        >
          Parallel 2 LED
        </button>
      </div>
      <div className="board row">
        <div className="chip-board">
          <span className="pin-label">5V</span>
          <span className="pin-label">GND</span>
          <span className="pin-label">13</span>
        </div>
        <div className={`led${on ? ' on' : ''}`} />
        {mode === 'parallel' ? <div className={`led${on ? ' on' : ''}`} /> : null}
      </div>
      <p className="mono center">{on ? 'HIGH · yonadi' : 'LOW · o‘chadi'}</p>
    </BoardShell>
  )
}

function PwmSim() {
  const [v, setV] = useState(120)
  return (
    <BoardShell title="PWM analogWrite" caption={`qiymat = ${v} (0–255)`}>
      <div className="board">
        <div className="led on" style={{ opacity: 0.12 + (v / 255) * 0.88 }} />
        <label className="slider-label">
          PWM
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
    <BoardShell title="Svetofor" caption="Qizil → qizil+sariq → yashil → sariq">
      <div className="traffic">
        <div className={`t-led red${lights[0] ? ' on' : ''}`} />
        <div className={`t-led yellow${lights[1] ? ' on' : ''}`} />
        <div className={`t-led green${lights[2] ? ' on' : ''}`} />
      </div>
    </BoardShell>
  )
}

function SerialSim() {
  const [lines, setLines] = useState<string[]>(['Serial Monitor 9600'])
  function runDemo() {
    setLines([])
    const seq = [
      { t: 0, s: 'Assalomu alaykum.' },
      { t: 1000, s: 'Mening ismim Nozima.' },
      { t: 1500, s: "Men texnologiya o'qituvchisiman. Yoshim 30 da." },
    ]
    seq.forEach(({ t, s }) => {
      window.setTimeout(() => {
        setLines((prev) => [...prev, s])
      }, t)
    })
  }
  return (
    <BoardShell title="Serial Monitor" caption="print / println / delay namuna">
      <div className="serial-box">
        {lines.map((l, i) => (
          <div key={`${l}-${i}`}>{l}</div>
        ))}
      </div>
      <button type="button" className="btn primary" onClick={runDemo}>
        Demo ishga tushirish
      </button>
    </BoardShell>
  )
}

function VarsSim() {
  const [c, setC] = useState(0)
  useEffect(() => {
    const id = window.setInterval(() => setC((x) => x + 2), 1000)
    return () => window.clearInterval(id)
  }, [])
  return (
    <BoardShell title="int o‘zgaruvchi" caption="c har soniyada +2 (Serial ga chiqadi)">
      <div className="board">
        <div className="big-num mono">{c}</div>
        <p className="muted">int c = …</p>
      </div>
    </BoardShell>
  )
}

function IfSim() {
  const [n, setN] = useState(0)
  useEffect(() => {
    const id = window.setInterval(() => setN((x) => (x >= 10 ? 0 : x + 1)), 600)
    return () => window.clearInterval(id)
  }, [])
  const ledOn = n >= 5 && n < 10
  return (
    <BoardShell title="if sharti" caption="n==5 → LED yon; n==10 → o‘ch va reset">
      <div className="board row">
        <div className="big-num mono">{n}</div>
        <div className={`led${ledOn ? ' on' : ''}`} />
      </div>
      <p className="mono center">
        {n === 5 ? 'if (n==5) HIGH' : n === 10 || n === 0 ? 'reset' : '…'}
      </p>
    </BoardShell>
  )
}
