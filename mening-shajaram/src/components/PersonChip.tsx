import type { Person } from '../types'
import { displayName, yearsLabel } from '../lib/tree'

type Props = {
  person: Person
  focused?: boolean
  onSelect: (id: string) => void
}

export function PersonChip({ person, focused, onSelect }: Props) {
  const initial = (person.firstName || '?').slice(0, 1).toUpperCase()
  return (
    <button
      type="button"
      className={`person-chip${focused ? ' is-focus' : ''}`}
      onClick={() => onSelect(person.id)}
    >
      <div className="avatar">
        {person.photoDataUrl ? (
          <img src={person.photoDataUrl} alt="" />
        ) : (
          initial
        )}
      </div>
      <div className="name">{displayName(person)}</div>
      {yearsLabel(person) ? <div className="years">{yearsLabel(person)}</div> : null}
    </button>
  )
}
