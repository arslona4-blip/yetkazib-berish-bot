/** Public URL path for Jadval PWA (maxfiy — eski /jadval/ yopilgan). */
export const JADVAL_BASE = '/jadval-fedd3d/'

export function jadvalAsset(path: string) {
  const p = path.replace(/^\//, '')
  return `${JADVAL_BASE}${p}`
}
