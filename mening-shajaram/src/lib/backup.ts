import type { TreeData } from '../types'

export function parseTree(raw: unknown): TreeData | null {
  if (!raw || typeof raw !== 'object') return null
  const data = raw as TreeData
  if (data.version !== 1 || !Array.isArray(data.people)) return null
  if (typeof data.ownerName !== 'string' || typeof data.treeTitle !== 'string') {
    return null
  }
  return data
}

/** Cloud ulashish uchun rasmlarni olib tashlaydi (hajm). */
export function treeForShare(data: TreeData): TreeData {
  return {
    ...data,
    people: data.people.map((p) => ({ ...p, photoDataUrl: '' })),
    updatedAt: new Date().toISOString(),
  }
}

export function downloadTreeJson(data: TreeData): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const stamp = new Date().toISOString().slice(0, 10)
  a.href = url
  a.download = `mening-shajaram-${stamp}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export async function readTreeFromFile(file: File): Promise<TreeData> {
  const text = await file.text()
  const parsed = parseTree(JSON.parse(text))
  if (!parsed) throw new Error('Fayl formati noto‘g‘ri')
  return parsed
}
