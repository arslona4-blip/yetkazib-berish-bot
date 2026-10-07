import { useCallback, useEffect, useState } from 'react'
import { ImageUpload } from './components/ImageUpload'
import { PreviewCanvas } from './components/PreviewCanvas'
import { Controls } from './components/Controls'
import { ExportPanel } from './components/ExportPanel'
import {
  blobToImage,
  preloadBackgroundRemoval,
  removeBackground,
} from './lib/backgroundRemoval'
import { exportSticker } from './lib/export'
import {
  DEFAULT_SETTINGS,
  type AnimationSettings,
  type ExportFormat,
  type ExportProgress,
} from './types'
import './App.css'

type ProcessState = 'idle' | 'loading-model' | 'removing' | 'ready' | 'error'

export default function App() {
  const [originalUrl, setOriginalUrl] = useState<string | null>(null)
  const [stickerUrl, setStickerUrl] = useState<string | null>(null)
  const [sticker, setSticker] = useState<HTMLImageElement | null>(null)
  const [settings, setSettings] = useState<AnimationSettings>(DEFAULT_SETTINGS)
  const [processState, setProcessState] = useState<ProcessState>('idle')
  const [statusMsg, setStatusMsg] = useState('Upload a PNG or JPG to begin.')
  const [statusRatio, setStatusRatio] = useState<number | undefined>()
  const [exportBusy, setExportBusy] = useState(false)
  const [exportProgress, setExportProgress] = useState<ExportProgress | null>(null)

  useEffect(() => {
    // Preload ONNX assets in the background
    preloadBackgroundRemoval((msg, ratio) => {
      setStatusMsg((current) =>
        current === 'Upload a PNG or JPG to begin.' || current.startsWith('Loading model')
          ? msg
          : current,
      )
      setStatusRatio(ratio)
    }).catch(() => {
      /* non-fatal — will retry on first removal */
    })
  }, [])

  useEffect(() => {
    return () => {
      if (originalUrl) URL.revokeObjectURL(originalUrl)
    }
  }, [originalUrl])

  useEffect(() => {
    return () => {
      if (stickerUrl) URL.revokeObjectURL(stickerUrl)
    }
  }, [stickerUrl])

  const onFileSelected = useCallback(async (file: File) => {
    const url = URL.createObjectURL(file)
    setOriginalUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return url
    })
    setSticker(null)
    setStickerUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return null
    })
    setProcessState('removing')
    setStatusMsg('Removing background — original face preserved…')
    setStatusRatio(0.1)

    try {
      const cutout = await removeBackground(file, (msg, ratio) => {
        setStatusMsg(msg)
        setStatusRatio(ratio)
      })
      const cutoutUrl = URL.createObjectURL(cutout)
      const img = await blobToImage(cutout)
      setStickerUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return cutoutUrl
      })
      setSticker(img)
      setProcessState('ready')
      setStatusMsg('Ready — adjust the walk and export your sticker.')
      setStatusRatio(1)
      setSettings((s) => ({ ...s, playing: true, loop: true }))
    } catch (err) {
      console.error(err)
      setProcessState('error')
      setStatusMsg(
        err instanceof Error
          ? err.message
          : 'Background removal failed. Try another image or refresh.',
      )
      setStatusRatio(undefined)
    }
  }, [])

  const onSettingsChange = useCallback((partial: Partial<AnimationSettings>) => {
    setSettings((s) => {
      const next = { ...s, ...partial }
      // Loop off implies pause for clarity; loop on restores play intent
      if (partial.loop === false) next.playing = false
      if (partial.loop === true && partial.playing === undefined) next.playing = true
      return next
    })
  }, [])

  const onExport = useCallback(
    async (format: ExportFormat) => {
      if (!sticker || exportBusy) return
      setExportBusy(true)
      setExportProgress({
        format,
        phase: 'rendering',
        progress: 0,
        message: 'Starting export…',
      })
      try {
        await exportSticker({
          sticker,
          format,
          settings,
          onProgress: (phase, ratio, message) => {
            setExportProgress({ format, phase, progress: ratio, message })
          },
        })
        setExportProgress({
          format,
          phase: 'done',
          progress: 1,
          message: 'Download started.',
        })
        setTimeout(() => setExportProgress(null), 2200)
      } catch (err) {
        console.error(err)
        setExportProgress({
          format,
          phase: 'error',
          progress: 0,
          message: err instanceof Error ? err.message : 'Export failed.',
        })
      } finally {
        setExportBusy(false)
      }
    },
    [sticker, settings, exportBusy],
  )

  const ready = processState === 'ready' && !!sticker
  const busyProcessing = processState === 'removing' || processState === 'loading-model'

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-glow" aria-hidden />
        <p className="brand">Live Walking Sticker</p>
        <h1 className="hero-title">Turn a photo into a walking sticker</h1>
        <p className="hero-sub">
          Upload · remove background · walk left to right · export GIF, WebM, APNG, or Telegram
        </p>
      </header>

      <main className="layout">
        <div className="col col-controls">
          <ImageUpload
            disabled={busyProcessing || exportBusy}
            previewUrl={originalUrl}
            onFileSelected={onFileSelected}
          />
          <Controls
            settings={settings}
            disabled={!ready || exportBusy}
            onChange={onSettingsChange}
          />
          <ExportPanel
            disabled={!ready}
            busy={exportBusy}
            progress={exportProgress}
            onExport={onExport}
          />
        </div>

        <div className="col col-preview">
          <PreviewCanvas stickerUrl={stickerUrl} settings={settings} />

          <div className={`status-banner state-${processState}`} role="status">
            {typeof statusRatio === 'number' && busyProcessing && (
              <div className="progress-bar compact">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.round(statusRatio * 100)}%` }}
                />
              </div>
            )}
            <p>{statusMsg}</p>
          </div>

          <aside className="identity-note">
            Identity lock: we never redraw or retouch faces — only background pixels are removed,
            then the original subject is animated by translation.
          </aside>
        </div>
      </main>

      <footer className="footer">
        <span>Runs fully in your browser · originals stay on-device</span>
      </footer>
    </div>
  )
}
