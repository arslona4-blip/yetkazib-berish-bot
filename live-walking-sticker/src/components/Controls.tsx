import type { AnimationSettings } from '../types'

interface ControlsProps {
  settings: AnimationSettings
  disabled?: boolean
  onChange: (next: Partial<AnimationSettings>) => void
}

export function Controls({ settings, disabled, onChange }: ControlsProps) {
  return (
    <section className="panel controls-panel">
      <h2>2. Animation</h2>
      <p className="panel-sub">Smooth left ↔ right walk with a light bob. Face pixels stay untouched.</p>

      <div className="control-row play-row">
        <button
          type="button"
          className="btn btn-primary btn-large"
          disabled={disabled}
          onClick={() => onChange({ playing: !settings.playing })}
        >
          {settings.playing ? 'Pause' : 'Play'}
        </button>
        <label className="loop-toggle">
          <input
            type="checkbox"
            checked={settings.loop}
            disabled={disabled}
            onChange={(e) => onChange({ loop: e.target.checked, playing: e.target.checked ? settings.playing : false })}
          />
          <span>Loop</span>
        </label>
      </div>

      <label className="slider-field">
        <div className="slider-label">
          <span>Speed</span>
          <span className="slider-value">{settings.speed.toFixed(2)}×</span>
        </div>
        <input
          type="range"
          min={0.25}
          max={3}
          step={0.05}
          value={settings.speed}
          disabled={disabled}
          onChange={(e) => onChange({ speed: Number(e.target.value) })}
        />
      </label>

      <label className="slider-field">
        <div className="slider-label">
          <span>Size</span>
          <span className="slider-value">{Math.round(settings.size * 100)}%</span>
        </div>
        <input
          type="range"
          min={0.2}
          max={0.95}
          step={0.01}
          value={settings.size}
          disabled={disabled}
          onChange={(e) => onChange({ size: Number(e.target.value) })}
        />
      </label>

      <label className="slider-field">
        <div className="slider-label">
          <span>Movement distance</span>
          <span className="slider-value">{Math.round(settings.distance * 100)}%</span>
        </div>
        <input
          type="range"
          min={0.1}
          max={0.9}
          step={0.01}
          value={settings.distance}
          disabled={disabled}
          onChange={(e) => onChange({ distance: Number(e.target.value) })}
        />
      </label>
    </section>
  )
}
