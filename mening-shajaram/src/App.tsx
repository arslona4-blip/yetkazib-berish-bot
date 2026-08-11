import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { PersonForm } from './components/PersonForm'
import { TreeView } from './components/TreeView'
import { fetchSharedTree, publishTree, shareLandingUrl } from './lib/api'
import { downloadTreeJson, readTreeFromFile } from './lib/backup'
import {
  clearTree,
  createEmptyTree,
  deletePerson,
  loadTree,
  newPersonId,
  saveTree,
  upsertPerson,
} from './lib/storage'
import { displayName, getRoot, yearsLabel } from './lib/tree'
import type { Person, Screen, TreeData } from './types'
import './styles.css'

function blankPerson(partial?: Partial<Person>): Person {
  return {
    id: newPersonId(),
    firstName: '',
    lastName: '',
    gender: 'male',
    birthYear: '',
    deathYear: '',
    photoDataUrl: '',
    notes: '',
    fatherId: null,
    motherId: null,
    spouseId: null,
    isRoot: false,
    createdAt: new Date().toISOString(),
    ...partial,
  }
}

export default function App() {
  const [tree, setTree] = useState<TreeData | null>(() => loadTree())
  const [screen, setScreen] = useState<Screen>(() =>
    loadTree() ? 'tree' : 'welcome',
  )
  const [focusId, setFocusId] = useState<string>(() => {
    const t = loadTree()
    return getRoot(t?.people || [])?.id || ''
  })
  const [draft, setDraft] = useState<Person | null>(null)
  const [ownerName, setOwnerName] = useState('')
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(
    null,
  )
  const [joinCode, setJoinCode] = useState('')
  const [shareCode, setShareCode] = useState('')
  const [shareUrl, setShareUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')

  useEffect(() => {
    const onBeforeInstall = (e: Event) => {
      e.preventDefault()
      setInstallEvent(e as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', onBeforeInstall)
    return () =>
      window.removeEventListener('beforeinstallprompt', onBeforeInstall)
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = (params.get('code') || '').trim().toUpperCase()
    if (!code) return
    void (async () => {
      setBusy(true)
      setStatusMsg('Shajara yuklanmoqda…')
      try {
        const remote = await fetchSharedTree(code)
        applyTree(remote)
        setShareCode(code)
        setShareUrl(shareLandingUrl(code))
        setStatusMsg(`Kod ${code} bilan ochildi`)
        // clean URL
        window.history.replaceState({}, '', `${window.location.pathname}`)
      } catch (err) {
        setStatusMsg(err instanceof Error ? err.message : 'Kod ochilmadi')
        setScreen('join')
        setJoinCode(code)
      } finally {
        setBusy(false)
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const people = tree?.people || []

  const sortedPeople = useMemo(
    () =>
      [...people].sort((a, b) =>
        displayName(a).localeCompare(displayName(b), 'uz'),
      ),
    [people],
  )

  function applyTree(next: TreeData) {
    const roots = next.people.filter((p) => p.isRoot)
    let peopleFixed = next.people
    if (roots.length > 1) {
      const keep = roots[0].id
      peopleFixed = next.people.map((p) => ({
        ...p,
        isRoot: p.id === keep,
      }))
    } else if (peopleFixed.length && !peopleFixed.some((p) => p.isRoot)) {
      peopleFixed = peopleFixed.map((p, i) => ({ ...p, isRoot: i === 0 }))
    }
    const saved = { ...next, people: peopleFixed }
    saveTree(saved)
    setTree(saved)
    setFocusId(getRoot(saved.people)?.id || '')
    setScreen('tree')
  }

  function persist(next: TreeData) {
    applyTree(next)
  }

  function startTree() {
    const name = ownerName.trim()
    if (!name) return
    const root = blankPerson({
      firstName: name.split(' ')[0] || name,
      lastName: name.split(' ').slice(1).join(' '),
      isRoot: true,
      gender: 'male',
    })
    const next = createEmptyTree(name, root)
    persist(next)
  }

  function openNewPerson() {
    setDraft(
      blankPerson({
        isRoot: people.length === 0,
      }),
    )
    setScreen('person')
  }

  function openEdit(id: string) {
    const person = people.find((p) => p.id === id)
    if (!person) return
    setDraft({ ...person })
    setScreen('person')
  }

  function saveDraft() {
    if (!draft || !tree) return
    if (!draft.firstName.trim()) return
    let nextPeople = tree.people
    if (draft.isRoot) {
      nextPeople = tree.people.map((p) => ({ ...p, isRoot: p.id === draft.id }))
    }
    const next = upsertPerson({ ...tree, people: nextPeople }, draft)
    persist(next)
    setFocusId(draft.id)
    setDraft(null)
    setScreen('tree')
  }

  function removeDraft() {
    if (!draft || !tree) return
    if (!confirm('Bu shaxsni o‘chirasizmi?')) return
    const next = deletePerson(tree, draft.id)
    persist(next)
    setFocusId(getRoot(next.people)?.id || '')
    setDraft(null)
    setScreen('people')
  }

  function resetAll() {
    if (!confirm('Butun shajara o‘chirilsinmi? Bu amalni qaytarib bo‘lmaydi.')) return
    clearTree()
    setTree(null)
    setFocusId('')
    setDraft(null)
    setShareCode('')
    setShareUrl('')
    setScreen('welcome')
  }

  async function installApp() {
    if (!installEvent) return
    await installEvent.prompt()
    setInstallEvent(null)
  }

  async function handleShare() {
    if (!tree) return
    setBusy(true)
    setStatusMsg('')
    try {
      const res = await publishTree(tree)
      setShareCode(res.code)
      setShareUrl(res.url || shareLandingUrl(res.code))
      setStatusMsg(`Ulashish kodi: ${res.code}`)
      if (navigator.share) {
        try {
          await navigator.share({
            title: tree.treeTitle,
            text: `Mening Shajaram — kod: ${res.code}`,
            url: res.url || shareLandingUrl(res.code),
          })
        } catch {
          /* user cancelled */
        }
      }
    } catch (err) {
      setStatusMsg(err instanceof Error ? err.message : 'Ulashib bo‘lmadi')
    } finally {
      setBusy(false)
    }
  }

  async function handleJoin(e: FormEvent) {
    e.preventDefault()
    if (!joinCode.trim()) return
    setBusy(true)
    setStatusMsg('')
    try {
      const remote = await fetchSharedTree(joinCode)
      applyTree(remote)
      setShareCode(joinCode.trim().toUpperCase())
      setShareUrl(shareLandingUrl(joinCode.trim().toUpperCase()))
      setStatusMsg('Shajara ochildi')
    } catch (err) {
      setStatusMsg(err instanceof Error ? err.message : 'Kod topilmadi')
    } finally {
      setBusy(false)
    }
  }

  async function handleImportFile(file: File | undefined) {
    if (!file) return
    setBusy(true)
    setStatusMsg('')
    try {
      const data = await readTreeFromFile(file)
      if (tree && !confirm('Joriy shajara o‘rniga yuklansinmi?')) {
        setBusy(false)
        return
      }
      applyTree(data)
      setStatusMsg('Zaxira tiklandi')
    } catch (err) {
      setStatusMsg(err instanceof Error ? err.message : 'Import xato')
    } finally {
      setBusy(false)
    }
  }

  async function copyShare() {
    const text = shareUrl || shareCode
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
      setStatusMsg('Nusxa olindi')
    } catch {
      setStatusMsg(text)
    }
  }

  const showNav =
    screen === 'tree' || screen === 'people' || screen === 'about' || screen === 'share'

  return (
    <div className={`app-shell${showNav ? '' : ' no-nav'}`}>
      {busy ? <div className="busy-bar" aria-live="polite">Kuting…</div> : null}

      {screen === 'welcome' ? (
        <section className="welcome">
          <div className="welcome-mark" aria-hidden />
          <div className="welcome-content">
            <h1 className="brand">
              Mening <span>Shajaram</span>
            </h1>
            <p className="lede">
              Oila ildizlaringizni bir joyda saqlang — ota, ona, farzandlar va
              avlodlar.
            </p>
            <div className="btn-row">
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setScreen('onboarding')}
              >
                Shajara boshlash
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setScreen('join')}
              >
                Kod bilan ochish
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {screen === 'onboarding' ? (
        <section className="screen">
          <div className="topbar">
            <div>
              <h1>Boshlash</h1>
              <p>Avval o‘zingizni yozing — shajara markazi.</p>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Orqaga"
              onClick={() => setScreen('welcome')}
            >
              ←
            </button>
          </div>
          <form
            className="form"
            onSubmit={(e) => {
              e.preventDefault()
              startTree()
            }}
          >
            <div className="field">
              <label htmlFor="owner">Ism familiyangiz</label>
              <input
                id="owner"
                required
                value={ownerName}
                onChange={(e) => setOwnerName(e.target.value)}
                placeholder="Masalan: Dilshod Karimov"
                autoFocus
              />
            </div>
            <p className="hint">
              Ma’lumotlar telefoningizda saqlanadi. Ulashish orqali oilangizga
              kod yuborishingiz mumkin.
            </p>
            <button type="submit" className="btn btn-primary btn-block">
              Davom etish
            </button>
          </form>
        </section>
      ) : null}

      {screen === 'join' ? (
        <section className="screen">
          <div className="topbar">
            <div>
              <h1>Kod bilan ochish</h1>
              <p>Oilangiz yuborgan 6 belgilik kod</p>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Orqaga"
              onClick={() => setScreen(tree ? 'share' : 'welcome')}
            >
              ←
            </button>
          </div>
          <form className="form" onSubmit={handleJoin}>
            <div className="field">
              <label htmlFor="joinCode">Ulashish kodi</label>
              <input
                id="joinCode"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                placeholder="MASALAN: AB12CD"
                autoCapitalize="characters"
                autoFocus
              />
            </div>
            {statusMsg ? <p className="hint">{statusMsg}</p> : null}
            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={busy || !joinCode.trim()}
            >
              Ochish
            </button>
          </form>
        </section>
      ) : null}

      {screen === 'tree' && tree ? (
        <section className="screen">
          <div className="topbar">
            <div>
              <h1>{tree.treeTitle}</h1>
              <p>{people.length} ta a’zo</p>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={openNewPerson}
            >
              + Qo‘shish
            </button>
          </div>

          {installEvent ? (
            <div className="install-banner">
              <span>Ilovani telefoningizga o‘rnating</span>
              <button type="button" className="btn btn-primary" onClick={installApp}>
                O‘rnatish
              </button>
            </div>
          ) : null}

          <div className="focus-picker" aria-label="Markaziy shaxs">
            {sortedPeople.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`focus-pill${p.id === focusId ? ' active' : ''}`}
                onClick={() => setFocusId(p.id)}
              >
                {displayName(p)}
              </button>
            ))}
          </div>

          <TreeView
            people={people}
            focusId={focusId || getRoot(people)?.id || ''}
            onFocus={(id) => {
              setFocusId(id)
            }}
          />

          <p className="hint" style={{ textAlign: 'center' }}>
            Kartani bosing — markazga o‘tadi. Ulashish: pastki menyu.
          </p>
        </section>
      ) : null}

      {screen === 'people' && tree ? (
        <section className="screen">
          <div className="topbar">
            <div>
              <h1>A’zolar</h1>
              <p>Hammani ro‘yxatda ko‘ring</p>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={openNewPerson}
            >
              + Yangi
            </button>
          </div>

          <div className="people-list">
            {sortedPeople.map((p) => (
              <button
                key={p.id}
                type="button"
                className="person-row"
                onClick={() => openEdit(p.id)}
              >
                <div className="avatar">
                  {p.photoDataUrl ? (
                    <img src={p.photoDataUrl} alt="" />
                  ) : (
                    (p.firstName || '?').slice(0, 1).toUpperCase()
                  )}
                </div>
                <div className="meta">
                  <strong>{displayName(p)}</strong>
                  <span>{yearsLabel(p) || 'Yil kiritilmagan'}</span>
                </div>
                {p.isRoot ? <span className="badge">Markaz</span> : null}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {screen === 'person' && draft ? (
        <section className="screen">
          <div className="topbar">
            <div>
              <h1>
                {people.some((p) => p.id === draft.id) ? 'Tahrirlash' : 'Yangi a’zo'}
              </h1>
              <p>Oila bog‘lanishlarini belgilang</p>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Orqaga"
              onClick={() => {
                setDraft(null)
                setScreen('people')
              }}
            >
              ←
            </button>
          </div>
          <PersonForm
            value={draft}
            people={people}
            onChange={setDraft}
            onSave={saveDraft}
            onCancel={() => {
              setDraft(null)
              setScreen(tree ? 'people' : 'welcome')
            }}
            onDelete={
              people.some((p) => p.id === draft.id) ? removeDraft : undefined
            }
          />
        </section>
      ) : null}

      {screen === 'share' && tree ? (
        <section className="screen">
          <div className="topbar">
            <div>
              <h1>Ulashish va zaxira</h1>
              <p>Oilaga kod yuboring yoki JSON saqlang</p>
            </div>
          </div>

          <div className="panel">
            <h2 className="panel-title">Bulutga ulashish</h2>
            <p className="hint">
              Kod yaratiladi. Havolani oilangizga yuboring. (Rasmlar
              ulashishda yuborilmaydi — hajm uchun.)
            </p>
            <div className="actions">
              <button
                type="button"
                className="btn btn-primary"
                disabled={busy}
                onClick={() => void handleShare()}
              >
                Kod yaratish
              </button>
              {shareCode ? (
                <button type="button" className="btn btn-ghost" onClick={() => void copyShare()}>
                  Nusxa
                </button>
              ) : null}
            </div>
            {shareCode ? (
              <div className="share-box">
                <strong>{shareCode}</strong>
                <span>{shareUrl}</span>
              </div>
            ) : null}
          </div>

          <div className="panel">
            <h2 className="panel-title">Zaxira (JSON)</h2>
            <div className="actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => downloadTreeJson(tree)}
              >
                Yuklab olish
              </button>
              <label className="btn btn-ghost file-btn">
                Tiklash
                <input
                  type="file"
                  accept="application/json,.json"
                  hidden
                  onChange={(e) => void handleImportFile(e.target.files?.[0])}
                />
              </label>
            </div>
          </div>

          <div className="panel">
            <h2 className="panel-title">Boshqa shajara</h2>
            <button
              type="button"
              className="btn btn-ghost btn-block"
              onClick={() => setScreen('join')}
            >
              Kod bilan ochish
            </button>
          </div>

          {statusMsg ? <p className="hint">{statusMsg}</p> : null}
        </section>
      ) : null}

      {screen === 'about' ? (
        <section className="screen">
          <div className="topbar">
            <div>
              <h1>Mening Shajaram</h1>
              <p>Oila shajarasi PWA</p>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Orqaga"
              onClick={() => setScreen(tree ? 'tree' : 'welcome')}
            >
              ←
            </button>
          </div>
          <p className="hint">
            Oila a’zolarini qo‘shing, ota–ona / farzand / turmush o‘rtog‘i
            bog‘lang. Ulashish kodi orqali oilangizga yuboring.
          </p>
          <p className="hint">
            Local zaxira telefoningizda. Bulut ulashish — vaqtinchalik kod
            orqali.
          </p>
          {tree ? (
            <div className="actions">
              <button type="button" className="btn btn-danger" onClick={resetAll}>
                Shajarani tozalash
              </button>
            </div>
          ) : null}
        </section>
      ) : null}

      {showNav ? (
        <nav className="bottom-nav" aria-label="Asosiy menyu">
          <div className="bottom-nav-inner nav-4">
            <button
              type="button"
              className={`nav-item${screen === 'tree' ? ' active' : ''}`}
              onClick={() => setScreen('tree')}
            >
              <span className="nav-ico">🌳</span>
              Shajara
            </button>
            <button
              type="button"
              className={`nav-item${screen === 'people' ? ' active' : ''}`}
              onClick={() => setScreen('people')}
            >
              <span className="nav-ico">👥</span>
              A’zolar
            </button>
            <button
              type="button"
              className={`nav-item${screen === 'share' ? ' active' : ''}`}
              onClick={() => setScreen('share')}
            >
              <span className="nav-ico">🔗</span>
              Ulashish
            </button>
            <button
              type="button"
              className={`nav-item${screen === 'about' ? ' active' : ''}`}
              onClick={() => setScreen('about')}
            >
              <span className="nav-ico">ℹ️</span>
              Haqida
            </button>
          </div>
        </nav>
      ) : null}
    </div>
  )
}

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
}
