import type { Gender, Person } from '../types'
import { displayName } from '../lib/tree'

type Props = {
  value: Person
  people: Person[]
  onChange: (next: Person) => void
  onSave: () => void
  onDelete?: () => void
  onCancel: () => void
}

function readPhoto(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

export function PersonForm({
  value,
  people,
  onChange,
  onSave,
  onDelete,
  onCancel,
}: Props) {
  const others = people.filter((p) => p.id !== value.id)
  const males = others.filter((p) => p.gender === 'male')
  const females = others.filter((p) => p.gender === 'female')

  return (
    <form
      className="form"
      onSubmit={(e) => {
        e.preventDefault()
        onSave()
      }}
    >
      <div className="field">
        <label htmlFor="firstName">Ism</label>
        <input
          id="firstName"
          required
          value={value.firstName}
          onChange={(e) => onChange({ ...value, firstName: e.target.value })}
          placeholder="Masalan: Ali"
        />
      </div>

      <div className="field">
        <label htmlFor="lastName">Familiya</label>
        <input
          id="lastName"
          value={value.lastName}
          onChange={(e) => onChange({ ...value, lastName: e.target.value })}
          placeholder="Masalan: Karimov"
        />
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="gender">Jins</label>
          <select
            id="gender"
            value={value.gender}
            onChange={(e) =>
              onChange({ ...value, gender: e.target.value as Gender })
            }
          >
            <option value="male">Erkak</option>
            <option value="female">Ayol</option>
            <option value="other">Boshqa</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="photo">Rasm</label>
          <input
            id="photo"
            type="file"
            accept="image/*"
            onChange={async (e) => {
              const file = e.target.files?.[0]
              if (!file) return
              const dataUrl = await readPhoto(file)
              onChange({ ...value, photoDataUrl: dataUrl })
            }}
          />
        </div>
      </div>

      {value.photoDataUrl ? (
        <img className="photo-preview" src={value.photoDataUrl} alt="" />
      ) : null}

      <div className="field-row">
        <div className="field">
          <label htmlFor="birthYear">Tug‘ilgan yil</label>
          <input
            id="birthYear"
            inputMode="numeric"
            value={value.birthYear}
            onChange={(e) => onChange({ ...value, birthYear: e.target.value })}
            placeholder="1990"
          />
        </div>
        <div className="field">
          <label htmlFor="deathYear">Vafot yili</label>
          <input
            id="deathYear"
            inputMode="numeric"
            value={value.deathYear}
            onChange={(e) => onChange({ ...value, deathYear: e.target.value })}
            placeholder="ixtiyoriy"
          />
        </div>
      </div>

      <div className="field">
        <label htmlFor="fatherId">Ota</label>
        <select
          id="fatherId"
          value={value.fatherId || ''}
          onChange={(e) =>
            onChange({ ...value, fatherId: e.target.value || null })
          }
        >
          <option value="">— tanlanmagan —</option>
          {males.map((p) => (
            <option key={p.id} value={p.id}>
              {displayName(p)}
            </option>
          ))}
          {others
            .filter((p) => p.gender !== 'male')
            .map((p) => (
              <option key={p.id} value={p.id}>
                {displayName(p)}
              </option>
            ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="motherId">Ona</label>
        <select
          id="motherId"
          value={value.motherId || ''}
          onChange={(e) =>
            onChange({ ...value, motherId: e.target.value || null })
          }
        >
          <option value="">— tanlanmagan —</option>
          {females.map((p) => (
            <option key={p.id} value={p.id}>
              {displayName(p)}
            </option>
          ))}
          {others
            .filter((p) => p.gender !== 'female')
            .map((p) => (
              <option key={p.id} value={p.id}>
                {displayName(p)}
              </option>
            ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="spouseId">Turmush o‘rtog‘i</label>
        <select
          id="spouseId"
          value={value.spouseId || ''}
          onChange={(e) =>
            onChange({ ...value, spouseId: e.target.value || null })
          }
        >
          <option value="">— tanlanmagan —</option>
          {others.map((p) => (
            <option key={p.id} value={p.id}>
              {displayName(p)}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="notes">Izoh</label>
        <textarea
          id="notes"
          value={value.notes}
          onChange={(e) => onChange({ ...value, notes: e.target.value })}
          placeholder="Qisqa eslatma..."
        />
      </div>

      <label className="hint" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          type="checkbox"
          checked={value.isRoot}
          onChange={(e) => onChange({ ...value, isRoot: e.target.checked })}
        />
        Shajara markazi (asosiy shaxs)
      </label>

      <div className="actions">
        <button type="submit" className="btn btn-primary">
          Saqlash
        </button>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Bekor
        </button>
        {onDelete ? (
          <button type="button" className="btn btn-danger" onClick={onDelete}>
            O‘chirish
          </button>
        ) : null}
      </div>
    </form>
  )
}
