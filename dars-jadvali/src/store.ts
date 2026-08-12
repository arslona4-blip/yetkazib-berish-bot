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
      className: old.className || '9-A',
      schoolName: old.schoolName || 'Maktab',
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

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) {
      const migrated = migrateLegacy()
      if (migrated) {
        saveSettings(migrated)
        return migrated
      }
      return defaultSettings()
    }
    const parsed = JSON.parse(raw) as AppSettings
    if (!parsed.profiles?.length) return defaultSettings()
    return parsed
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
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
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
