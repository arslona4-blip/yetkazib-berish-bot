import { useCallback, useRef, useState, type DragEvent, type ChangeEvent } from 'react'
import { isSupportedImageFile } from '../lib/backgroundRemoval'

interface ImageUploadProps {
  disabled?: boolean
  previewUrl: string | null
  onFileSelected: (file: File) => void
}

export function ImageUpload({ disabled, previewUrl, onFileSelected }: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFile = useCallback(
    (file: File | undefined | null) => {
      if (!file) return
      if (!isSupportedImageFile(file)) {
        setError('Please upload a PNG or JPG image.')
        return
      }
      setError(null)
      onFileSelected(file)
    },
    [onFileSelected],
  )

  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFile(e.target.files?.[0])
    e.target.value = ''
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    handleFile(e.dataTransfer.files?.[0])
  }

  return (
    <section className="panel upload-panel">
      <h2>1. Upload</h2>
      <p className="panel-sub">
        PNG or JPG. Your face stays exactly as photographed — we only remove the background.
      </p>

      <button
        type="button"
        className={`dropzone ${dragOver ? 'drag-over' : ''} ${previewUrl ? 'has-preview' : ''}`}
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        aria-label="Upload PNG or JPG image"
      >
        {previewUrl ? (
          <img src={previewUrl} alt="Uploaded original" className="upload-preview" />
        ) : (
          <div className="dropzone-empty">
            <span className="dropzone-title">Tap to choose a photo</span>
            <span className="dropzone-hint">or drag & drop · PNG / JPG</span>
          </div>
        )}
      </button>

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,.png,.jpg,.jpeg"
        hidden
        onChange={onChange}
      />

      {error && <p className="error-text" role="alert">{error}</p>}
    </section>
  )
}
