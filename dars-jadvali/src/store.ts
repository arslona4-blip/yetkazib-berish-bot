import {
  createProfile,
  defaultSettings,
  emptyCell,
  emptyCells,
  type AppSettings,
  type Cell,
  type Profile,
} from './model'

const KEY = 'maktab-jadval-pro-v2'
const LEGACY = 'maktab-dars-jadvali-v1'

function migrateLegacy(): AppSettings | null {
  try {
    const raw = localStorage.getItem(LEGACY)
    if (!raw) return null
    const old = JSON.parse(raw) as {
      className?: string
      schoolName?: string
      subjects?: Record<string, string>
    }
    const cells: Record<string, Cell> = emptyCells(
      defaultSettings().profiles[0].periods,
    )
    if (old.subjects) {
      for (const [k, v] of Object.entries(old.subjects)) {
        cells[k] = { ...emptyCell(), subject: v || '' }
      }
    }
    const p = createProfile({
      className: old.className || '',
      schoolName: old.schoolName || '',
      cells,
    })
    const s = defaultSettings()
    s.profiles = [p]
    s.activeProfileId = p.id
    return s
  } catch {
    return null
  }
}

const PLACEHOLDER_CLASS = new Set(['9', '9-A', '7-A', '5-A', 'Yangi'])
const PLACEHOLDER_SCHOOL = new Set([
  '24 maktab',
  'Maktab',
  'Ixtisoslashtirilgan maktab',
  '№12-maktab',
])

function scrubPlaceholders(s: AppSettings): AppSettings {
  return {
    ...s,
    profiles: s.profiles.map((p) => ({
      ...p,
      className: PLACEHOLDER_CLASS.has(p.className.trim()) ? '' : p.className,
      schoolName: PLACEHOLDER_SCHOOL.has(p.schoolName.trim()) ? '' : p.schoolName,
    })),
  }
}

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) {
      const migrated = migrateLegacy()
      if (migrated) {
        const cleaned = scrubPlaceholders(migrated)
        saveSettings(cleaned)
        return cleaned
      }
      return defaultSettings()
    }
    const parsed = JSON.parse(raw) as AppSettings
    if (!parsed.profiles?.length) return defaultSettings()
    return scrubPlaceholders(parsed)
  } catch {
    return defaultSettings()
  }
}

export function saveSettings(s: AppSettings) {
  localStorage.setItem(KEY, JSON.stringify(s))
}

export function activeProfile(s: AppSettings): Profile {
  return s.profiles.find((p) => p.id === s.activeProfileId) ?? s.profiles[0]
}

export function downloadJson(filename: string, data: unknown) {
  downloadBlob(filename, new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
}

export function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'download'
  a.rel = 'noopener'
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1500)
}

export async function shareOrDownload(
  filename: string,
  blob: Blob,
  title: string,
): Promise<'shared' | 'downloaded'> {
  const file = new File([blob], filename, { type: blob.type || 'application/octet-stream' })
  try {
    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({ title, files: [file] })
      return 'shared'
    }
  } catch {
    /* fall through to download */
  }
  downloadBlob(filename, blob)
  return 'downloaded'
}

export function readJsonFile(file: File): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => {
      try {
        resolve(JSON.parse(String(r.result)))
      } catch (e) {
        reject(e)
      }
    }
    r.onerror = () => reject(r.error)
    r.readAsText(file)
  })
}
