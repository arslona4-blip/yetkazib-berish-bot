import type { ExportFormat, ExportProgress } from '../types'

interface ExportPanelProps {
  disabled?: boolean
  busy: boolean
  progress: ExportProgress | null
  onExport: (format: ExportFormat) => void
}

const FORMATS: { id: ExportFormat; label: string; hint: string }[] = [
  { id: 'gif', label: 'Export GIF', hint: 'Transparent animated GIF' },
  { id: 'webm', label: 'Export WebM', hint: 'Transparent video when supported' },
  { id: 'apng', label: 'Export APNG', hint: 'High-quality animated PNG' },
  {
    id: 'telegram-webm',
    label: 'Telegram sticker',
    hint: '512×512 VP9 WebM ≤3s',
  },
]

export function ExportPanel({ disabled, busy, progress, onExport }: ExportPanelProps) {
  return (
    <section className="panel export-panel">
      <h2>3. Export</h2>
      <p className="panel-sub">Download a looping walking sticker with a transparent background.</p>

      <div className="export-grid">
        {FORMATS.map((f) => (
          <button
            key={f.id}
            type="button"
            className="btn btn-export"
            disabled={disabled || busy}
            onClick={() => onExport(f.id)}
          >
            <span className="export-label">{f.label}</span>
            <span className="export-hint">{f.hint}</span>
          </button>
        ))}
      </div>

      {progress && (
        <div className="export-progress" role="status" aria-live="polite">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${Math.round(progress.progress * 100)}%` }}
            />
          </div>
          <p className="progress-msg">{progress.message}</p>
        </div>
      )}
    </section>
  )
}
