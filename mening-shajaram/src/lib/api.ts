import type { TreeData } from '../types'
import { parseTree, treeForShare } from './backup'

function apiBase(): string {
  // Railway: /shajara/ + /api/... bir origin
  return ''
}

export async function publishTree(tree: TreeData): Promise<{ code: string; url: string }> {
  const res = await fetch(`${apiBase()}/api/shajara/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tree: treeForShare(tree) }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || 'Ulashish muvaffaqiyatsiz')
  }
  return res.json()
}

export async function fetchSharedTree(code: string): Promise<TreeData> {
  const clean = code.trim().toUpperCase()
  const res = await fetch(`${apiBase()}/api/shajara/share/${encodeURIComponent(clean)}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || 'Kod topilmadi')
  }
  const body = await res.json()
  const tree = parseTree(body.tree)
  if (!tree) throw new Error('Shajara ma’lumoti buzilgan')
  return tree
}

export function shareLandingUrl(code: string): string {
  const origin = window.location.origin
  return `${origin}/shajara/?code=${encodeURIComponent(code)}`
}
