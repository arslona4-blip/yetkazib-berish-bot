import type { Person } from '../types'
import { buildFocusTree } from '../lib/tree'
import { PersonChip } from './PersonChip'

type Props = {
  people: Person[]
  focusId: string
  onFocus: (id: string) => void
}

export function TreeView({ people, focusId, onFocus }: Props) {
  const tree = buildFocusTree(people, focusId)
  if (!tree) {
    return <div className="empty-tree">Shajara bo‘sh. Avval o‘zingizni qo‘shing.</div>
  }

  const { father, mother, focus, spouse, children } = tree
  const hasParents = Boolean(father || mother)

  return (
    <div className="tree-stage">
      {hasParents ? (
        <>
          <div className="tree-row">
            {father ? <PersonChip person={father} onSelect={onFocus} /> : null}
            {mother ? <PersonChip person={mother} onSelect={onFocus} /> : null}
          </div>
          <div className="tree-connector" />
        </>
      ) : null}

      <div className="couple">
        <PersonChip person={focus} focused onSelect={onFocus} />
        {spouse ? (
          <>
            <span className="couple-heart" aria-hidden>
              ♥
            </span>
            <PersonChip person={spouse} onSelect={onFocus} />
          </>
        ) : null}
      </div>

      {children.length ? (
        <>
          <div className="tree-connector" />
          <div className="tree-row">
            {children.map((child) => (
              <PersonChip key={child.id} person={child} onSelect={onFocus} />
            ))}
          </div>
        </>
      ) : (
        <p className="hint" style={{ textAlign: 'center', marginTop: 16 }}>
          Farzandlar yo‘q — «A’zolar» dan qo‘shing.
        </p>
      )}
    </div>
  )
}
