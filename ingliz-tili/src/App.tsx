import { useEffect, useMemo, useRef, useState } from 'react'
import {
  GAME_LIST,
  makeMatchPairs,
  makeMemoryCards,
  scrambleWord,
  shuffle,
  type GameId,
  type MatchPair,
  type MemoryCard,
} from './games'
import {
  answersMatch,
  LESSONS,
  LEVEL_LABEL,
  SKILL_META,
  type Lesson,
  type Level,
  type QuizItem,
  type SkillId,
} from './lessons'
import {
  lessonSkillCount,
  loadProgress,
  markGame,
  markSkill,
  type Progress,
} from './progress'
import { listenOnce, scorePronunciation, speechSupported } from './speech'
import { speak, stopSpeak } from './tts'
import './styles.css'

type View = 'home' | 'hub' | 'skill' | 'game'

export default function App() {
  const [view, setView] = useState<View>('home')
  const [lessonId, setLessonId] = useState(LESSONS[0].id)
  const [skill, setSkill] = useState<SkillId>('vocab')
  const [game, setGame] = useState<GameId>('match')
  const [progress, setProgress] = useState<Progress>(() => loadProgress())
  const [filter, setFilter] = useState<'all' | Level>('all')
  const [toast, setToast] = useState('')

  const lesson = useMemo(
    () => LESSONS.find((l) => l.id === lessonId) || LESSONS[0],
    [lessonId],
  )

  const filtered = useMemo(() => {
    if (filter === 'all') return LESSONS
    return LESSONS.filter((l) => l.level === filter)
  }, [filter])

  useEffect(() => () => stopSpeak(), [])

  function showToast(msg: string) {
    setToast(msg)
    window.setTimeout(() => setToast(''), 1600)
  }

  function openHub(id: string) {
    stopSpeak()
    setLessonId(id)
    setView('hub')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function openSkill(s: SkillId) {
    stopSpeak()
    setSkill(s)
    setView('skill')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function openGame(g: GameId, fromLesson?: string) {
    stopSpeak()
    if (fromLesson) setLessonId(fromLesson)
    setGame(g)
    setView('game')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function onSkillDone(score: number) {
    const p = markSkill(lesson.id, skill, score)
    setProgress(p)
    showToast(`+XP · ${score}%`)
  }

  function onGameDone(score: number) {
    const p = markGame(`${game}-${lesson.id}`, score)
    setProgress(p)
    showToast(`O‘yin · ${score} ball`)
  }

  if (view === 'home') {
    return (
      <div className="page">
        <header className="hero">
          <div className="hero-bg" aria-hidden />
          <div className="hero-wave" aria-hidden />
          <p className="eyebrow">O‘zbek → English · 6 ko‘nikma + o‘yinlar</p>
          <h1 className="brand">Ingliz</h1>
          <p className="lead">
            Lug‘at, listening, reading, writing, speaking, talaffuz va quiz.
            Zerikmang — o‘yinlar bilan mashq qiling.
          </p>
          <div className="stats-row">
            <div className="stat">
              <strong>{progress.xp}</strong>
              <span>XP</span>
            </div>
            <div className="stat">
              <strong>{progress.streak}</strong>
              <span>Kun ketma-ket</span>
            </div>
            <div className="stat">
              <strong>
                {progress.done.length}/{LESSONS.length}
              </strong>
              <span>Dars</span>
            </div>
          </div>
        </header>

        <section className="panel-block">
          <div className="section-head">
            <h2>O‘yinlar</h2>
            <p>Tez, qiziqarli, darslardan so‘zlar bilan</p>
          </div>
          <div className="game-grid">
            {GAME_LIST.map((g) => (
              <button
                key={g.id}
                type="button"
                className="game-card"
                onClick={() => openGame(g.id, lessonId)}
              >
                <span className="game-ico" aria-hidden>
                  {g.emoji}
                </span>
                <strong>{g.title}</strong>
                <span>{g.blurb}</span>
                {progress.games[`${g.id}-${lessonId}`] != null ? (
                  <em>Rekord: {progress.games[`${g.id}-${lessonId}`]}</em>
                ) : null}
              </button>
            ))}
          </div>
        </section>

        <div className="filters" role="tablist" aria-label="Daraja">
          {(
            [
              ['all', 'Hammasi'],
              ['boshlangich', 'Boshlang‘ich'],
              ['ortacha', 'O‘rta'],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              type="button"
              className={`chip${filter === k ? ' on' : ''}`}
              onClick={() => setFilter(k)}
            >
              {label}
            </button>
          ))}
        </div>

        <section className="grid" aria-label="Darslar">
          {filtered.map((l) => {
            const isDone = progress.done.includes(l.id)
            const sk = lessonSkillCount(progress, l.id)
            return (
              <button
                key={l.id}
                type="button"
                className={`lesson-btn${isDone ? ' done' : ''}`}
                onClick={() => openHub(l.id)}
              >
                <div className="lesson-top">
                  <span className="num">{String(l.num).padStart(2, '0')}</span>
                  <span className="tag">{LEVEL_LABEL[l.level]}</span>
                </div>
                <h2>{l.title}</h2>
                <p>{l.summary}</p>
                <div className="lesson-foot">
                  <span>
                    {l.minutes} daq · {sk}/7 ko‘nikma
                  </span>
                  <span>{isDone ? `✓ ${progress.scores[l.id] ?? 0}%` : 'Ochish →'}</span>
                </div>
              </button>
            )
          })}
        </section>

        {toast ? <div className="toast">{toast}</div> : null}
      </div>
    )
  }

  if (view === 'hub') {
    const sk = progress.skills[lesson.id] || {}
    return (
      <div className="page lesson-page">
        <div className="topbar">
          <button type="button" className="ghost" onClick={() => setView('home')}>
            ← Bosh
          </button>
          <span className="muted">
            {LEVEL_LABEL[lesson.level]} · {lesson.minutes} daq
          </span>
          <button
            type="button"
            className="ghost"
            onClick={() => openGame('lightning', lesson.id)}
          >
            ⚡
          </button>
        </div>

        <header className="lesson-head">
          <p className="eyebrow">Dars {String(lesson.num).padStart(2, '0')}</p>
          <h1>{lesson.title}</h1>
          <p className="lead">{lesson.tip}</p>
        </header>

        <div className="skill-grid">
          {SKILL_META.map((s) => {
            const score = sk[s.id]
            return (
              <button
                key={s.id}
                type="button"
                className={`skill-card${score != null ? ' done' : ''}`}
                onClick={() => openSkill(s.id)}
              >
                <strong>{s.title}</strong>
                <span>{s.blurb}</span>
                <em>{score != null ? `${score}%` : 'Boshlash'}</em>
              </button>
            )
          })}
        </div>

        <section className="panel-block">
          <div className="section-head">
            <h2>Shu dars o‘yinlari</h2>
          </div>
          <div className="game-grid compact">
            {GAME_LIST.map((g) => (
              <button
                key={g.id}
                type="button"
                className="game-card"
                onClick={() => openGame(g.id, lesson.id)}
              >
                <span className="game-ico">{g.emoji}</span>
                <strong>{g.title}</strong>
              </button>
            ))}
          </div>
        </section>

        {toast ? <div className="toast">{toast}</div> : null}
      </div>
    )
  }

  if (view === 'game') {
    return (
      <GameScreen
        lesson={lesson}
        game={game}
        onBack={() => setView('hub')}
        onHome={() => setView('home')}
        onDone={onGameDone}
      />
    )
  }

  return (
    <SkillScreen
      lesson={lesson}
      skill={skill}
      onBack={() => setView('hub')}
      onHome={() => setView('home')}
      onDone={onSkillDone}
      toast={toast}
    />
  )
}

function Top({
  back,
  home,
  label,
}: {
  back: () => void
  home: () => void
  label: string
}) {
  return (
    <div className="topbar">
      <button type="button" className="ghost" onClick={back}>
        ← Orqaga
      </button>
      <span className="muted">{label}</span>
      <button type="button" className="ghost" onClick={home}>
        Bosh
      </button>
    </div>
  )
}

function SkillScreen({
  lesson,
  skill,
  onBack,
  onHome,
  onDone,
  toast,
}: {
  lesson: Lesson
  skill: SkillId
  onBack: () => void
  onHome: () => void
  onDone: (score: number) => void
  toast: string
}) {
  const meta = SKILL_META.find((s) => s.id === skill)!

  return (
    <div className="page lesson-page">
      <Top back={onBack} home={onHome} label={meta.title} />
      <header className="lesson-head tight">
        <p className="eyebrow">{lesson.title}</p>
        <h1>{meta.title}</h1>
        <p className="lead">{meta.blurb}</p>
      </header>

      {skill === 'vocab' ? <VocabSkill lesson={lesson} onDone={onDone} /> : null}
      {skill === 'quiz' ? (
        <QuizSkill items={lesson.quiz} onDone={onDone} title="Quiz" />
      ) : null}
      {skill === 'reading' ? <ReadingSkill lesson={lesson} onDone={onDone} /> : null}
      {skill === 'writing' ? <WritingSkill lesson={lesson} onDone={onDone} /> : null}
      {skill === 'listening' ? <ListeningSkill lesson={lesson} onDone={onDone} /> : null}
      {skill === 'speaking' ? <SpeakingSkill lesson={lesson} onDone={onDone} /> : null}
      {skill === 'pronounce' ? <PronounceSkill lesson={lesson} onDone={onDone} /> : null}

      {toast ? <div className="toast">{toast}</div> : null}
    </div>
  )
}

function VocabSkill({
  lesson,
  onDone,
}: {
  lesson: Lesson
  onDone: (n: number) => void
}) {
  const items = useMemo(
    () => [...lesson.words.map((w) => ({ en: w.en, uz: w.uz, tip: w.tip })), ...lesson.phrases],
    [lesson],
  )
  const [idx, setIdx] = useState(0)
  const [seen, setSeen] = useState(1)
  const [flash, setFlash] = useState(false)
  const cur = items[idx]

  function say() {
    setFlash(true)
    void speak(cur.en)
    window.setTimeout(() => setFlash(false), 280)
  }

  function next(delta: number) {
    const n = Math.min(items.length - 1, Math.max(0, idx + delta))
    setIdx(n)
    setSeen((s) => Math.max(s, n + 1))
  }

  function finish() {
    onDone(Math.round((seen / items.length) * 100))
  }

  return (
    <section className={`flashcard${flash ? ' pulse' : ''}`}>
      <button type="button" className="speak" onClick={say} aria-label="Eshitish">
        ♪
      </button>
      <p className="en phrase">{cur.en}</p>
      <p className="uz">{cur.uz}</p>
      {'tip' in cur && typeof (cur as { tip?: string }).tip === 'string' ? (
        <p className="tip">{(cur as { tip?: string }).tip}</p>
      ) : null}
      <div className="nav-row">
        <button type="button" className="btn" disabled={idx === 0} onClick={() => next(-1)}>
          ←
        </button>
        <span className="muted">
          {idx + 1}/{items.length}
        </span>
        <button
          type="button"
          className="btn"
          disabled={idx >= items.length - 1}
          onClick={() => next(1)}
        >
          →
        </button>
      </div>
      <button type="button" className="btn primary wide" onClick={say}>
        Eshitish
      </button>
      {idx >= items.length - 1 ? (
        <button type="button" className="btn wide" onClick={finish}>
          Ko‘nikmani yakunlash
        </button>
      ) : null}
    </section>
  )
}

function QuizSkill({
  items,
  onDone,
  title,
}: {
  items: QuizItem[]
  onDone: (n: number) => void
  title: string
}) {
  const [idx, setIdx] = useState(0)
  const [picked, setPicked] = useState<number | null>(null)
  const [correct, setCorrect] = useState(0)
  const correctRef = useRef(0)
  const [done, setDone] = useState(false)
  const q = items[idx]

  function answer(i: number) {
    if (picked !== null || done) return
    setPicked(i)
    if (i === q.answer) {
      correctRef.current += 1
      setCorrect(correctRef.current)
    }
  }

  function next() {
    if (picked === null) return
    if (idx + 1 >= items.length) {
      setDone(true)
      onDone(Math.round((correctRef.current / items.length) * 100))
      return
    }
    setIdx((x) => x + 1)
    setPicked(null)
  }

  if (done) {
    const pct = Math.round((correct / items.length) * 100)
    return (
      <section className="quiz-result reveal">
        <p className="eyebrow">{title} natija</p>
        <h1>{pct}%</h1>
        <p className="lead">
          {correct}/{items.length} to‘g‘ri
        </p>
      </section>
    )
  }

  return (
    <section className="quiz-box reveal">
      <p className="muted">
        {idx + 1}/{items.length}
      </p>
      <h1 className="q-prompt">{q.prompt}</h1>
      {q.hint ? <p className="hint">{q.hint}</p> : null}
      <div className="options">
        {q.options.map((opt, i) => {
          let cls = 'opt'
          if (picked !== null) {
            if (i === q.answer) cls += ' correct'
            else if (i === picked) cls += ' wrong'
          }
          return (
            <button
              key={opt}
              type="button"
              className={cls}
              disabled={picked !== null}
              onClick={() => answer(i)}
            >
              {opt}
            </button>
          )
        })}
      </div>
      {picked !== null ? (
        <button type="button" className="btn primary wide" onClick={next}>
          {idx + 1 >= items.length ? 'Natija' : 'Keyingi →'}
        </button>
      ) : null}
    </section>
  )
}

function ReadingSkill({
  lesson,
  onDone,
}: {
  lesson: Lesson
  onDone: (n: number) => void
}) {
  const [phase, setPhase] = useState<'read' | 'quiz'>('read')
  return phase === 'read' ? (
    <section className="read-box reveal">
      <h2>{lesson.reading.title}</h2>
      <p className="read-text">{lesson.reading.text}</p>
      <button
        type="button"
        className="btn"
        onClick={() => void speak(lesson.reading.text, { rate: 0.85 })}
      >
        Matnni eshitish
      </button>
      <button type="button" className="btn primary wide" onClick={() => setPhase('quiz')}>
        Savollarga o‘tish
      </button>
    </section>
  ) : (
    <QuizSkill items={lesson.reading.questions} onDone={onDone} title="Reading" />
  )
}

function WritingSkill({
  lesson,
  onDone,
}: {
  lesson: Lesson
  onDone: (n: number) => void
}) {
  const [idx, setIdx] = useState(0)
  const [value, setValue] = useState('')
  const [correct, setCorrect] = useState(0)
  const correctRef = useRef(0)
  const [feedback, setFeedback] = useState<'ok' | 'bad' | null>(null)
  const [done, setDone] = useState(false)
  const item = lesson.writing[idx]

  function check() {
    if (feedback) return
    const ok = answersMatch(value, item.answer, item.accept)
    setFeedback(ok ? 'ok' : 'bad')
    if (ok) {
      correctRef.current += 1
      setCorrect(correctRef.current)
    }
  }

  function next() {
    if (!feedback) return
    if (idx + 1 >= lesson.writing.length) {
      const pct = Math.round((correctRef.current / lesson.writing.length) * 100)
      setDone(true)
      onDone(pct)
      return
    }
    setIdx((i) => i + 1)
    setValue('')
    setFeedback(null)
  }

  if (done) {
    return (
      <section className="quiz-result reveal">
        <p className="eyebrow">Writing</p>
        <h1>{Math.round((correct / lesson.writing.length) * 100)}%</h1>
      </section>
    )
  }

  return (
    <section className="write-box reveal">
      <p className="muted">
        {idx + 1}/{lesson.writing.length}
      </p>
      <h2>{item.promptUz}</h2>
      <input
        className="text-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Inglizcha yozing…"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
        onKeyDown={(e) => {
          if (e.key === 'Enter') (feedback ? next : check)()
        }}
      />
      {feedback === 'ok' ? <p className="ok-msg">To‘g‘ri!</p> : null}
      {feedback === 'bad' ? (
        <p className="bad-msg">Javob: {item.answer}</p>
      ) : null}
      {!feedback ? (
        <button type="button" className="btn primary wide" onClick={check}>
          Tekshirish
        </button>
      ) : (
        <button type="button" className="btn primary wide" onClick={next}>
          {idx + 1 >= lesson.writing.length ? 'Natija' : 'Keyingi →'}
        </button>
      )}
    </section>
  )
}

function ListeningSkill({
  lesson,
  onDone,
}: {
  lesson: Lesson
  onDone: (n: number) => void
}) {
  const [idx, setIdx] = useState(0)
  const [picked, setPicked] = useState<number | null>(null)
  const [correct, setCorrect] = useState(0)
  const correctRef = useRef(0)
  const [done, setDone] = useState(false)
  const [slow, setSlow] = useState(false)
  const item = lesson.listening[idx]

  function play() {
    void speak(item.audioText, { rate: slow ? 0.7 : 0.92 })
  }

  function answer(i: number) {
    if (picked !== null) return
    setPicked(i)
    if (i === item.answer) {
      correctRef.current += 1
      setCorrect(correctRef.current)
    }
  }

  function next() {
    if (picked === null) return
    if (idx + 1 >= lesson.listening.length) {
      setDone(true)
      onDone(Math.round((correctRef.current / lesson.listening.length) * 100))
      return
    }
    setIdx((x) => x + 1)
    setPicked(null)
  }

  if (done) {
    return (
      <section className="quiz-result reveal">
        <p className="eyebrow">Listening</p>
        <h1>{Math.round((correct / lesson.listening.length) * 100)}%</h1>
      </section>
    )
  }

  return (
    <section className="quiz-box reveal">
      <p className="muted">
        {idx + 1}/{lesson.listening.length}
      </p>
      <h1 className="q-prompt">Nima eshitdingiz?</h1>
      <div className="cta-row">
        <button type="button" className="btn primary" onClick={play}>
          ▶ Eshitish
        </button>
        <button
          type="button"
          className={`btn${slow ? ' onish' : ''}`}
          onClick={() => setSlow((s) => !s)}
        >
          {slow ? 'Sekin ✓' : 'Sekin'}
        </button>
      </div>
      <div className="options">
        {item.options.map((opt, i) => {
          let cls = 'opt'
          if (picked !== null) {
            if (i === item.answer) cls += ' correct'
            else if (i === picked) cls += ' wrong'
          }
          return (
            <button
              key={opt}
              type="button"
              className={cls}
              disabled={picked !== null}
              onClick={() => answer(i)}
            >
              {opt}
            </button>
          )
        })}
      </div>
      {picked !== null ? (
        <button type="button" className="btn primary wide" onClick={next}>
          {idx + 1 >= lesson.listening.length ? 'Natija' : 'Keyingi →'}
        </button>
      ) : null}
    </section>
  )
}

function SpeakingSkill({
  lesson,
  onDone,
}: {
  lesson: Lesson
  onDone: (n: number) => void
}) {
  const lines = useMemo(
    () => lesson.phrases.slice(0, 5).map((p) => p.en),
    [lesson],
  )
  const [idx, setIdx] = useState(0)
  const [status, setStatus] = useState('')
  const [heard, setHeard] = useState('')
  const [scores, setScores] = useState<number[]>([])
  const [listening, setListening] = useState(false)
  const [done, setDone] = useState(false)
  const [attempted, setAttempted] = useState(false)
  const target = lines[idx]
  const supported = speechSupported()

  async function trySpeak() {
    if (listening) return
    setListening(true)
    setStatus('Gapiring…')
    setHeard('')
    stopSpeak()
    const res = await listenOnce('en-US', 7000)
    setListening(false)
    if (!res.ok) {
      setStatus(
        res.error === 'supported_emas'
          ? 'Mikrofon API yo‘q — matn bilan mashq qiling'
          : 'Qayta urinib ko‘ring',
      )
      return
    }
    setHeard(res.text)
    const sc = scorePronunciation(target, res.text)
    setScores((s) => {
      const copy = [...s]
      copy[idx] = sc
      return copy
    })
    setAttempted(true)
    setStatus(sc >= 70 ? `Yaxshi! ${sc}%` : `Yana urinib ko‘ring · ${sc}%`)
  }

  function next() {
    if (idx + 1 >= lines.length) {
      const list = lines.map((_, i) => scores[i] ?? 0)
      const avg = Math.round(list.reduce((a, b) => a + b, 0) / list.length)
      setDone(true)
      onDone(avg)
      return
    }
    setIdx((i) => i + 1)
    setHeard('')
    setStatus('')
    setAttempted(false)
  }

  if (done) {
    const list = lines.map((_, i) => scores[i] ?? 0)
    const avg = Math.round(list.reduce((a, b) => a + b, 0) / Math.max(1, list.length))
    return (
      <section className="quiz-result reveal">
        <p className="eyebrow">Speaking</p>
        <h1>{avg}%</h1>
      </section>
    )
  }

  return (
    <section className="speak-box reveal">
      <p className="muted">
        {idx + 1}/{lines.length}
      </p>
      <p className="en phrase">{target}</p>
      <div className="cta-row">
        <button type="button" className="btn" onClick={() => void speak(target, { rate: 0.85 })}>
          Namuna
        </button>
        <button
          type="button"
          className={`btn primary${listening ? ' pulse-btn' : ''}`}
          onClick={() => void trySpeak()}
          disabled={!supported || listening}
        >
          {listening ? 'Tinglanmoqda…' : '🎤 Gapirish'}
        </button>
      </div>
      {!supported ? (
        <p className="hint">Brauzeringiz mikrofonli speakingni qo‘llab-quvvatlamaydi (Chrome tavsiya).</p>
      ) : null}
      {heard ? <p className="heard">Siz: “{heard}”</p> : null}
      {status ? <p className="tip">{status}</p> : null}
      <button type="button" className="btn wide" onClick={next} disabled={supported && !attempted}>
        {idx + 1 >= lines.length ? 'Natija' : 'Keyingi →'}
      </button>
      {!supported ? (
        <button
          type="button"
          className="btn wide"
          onClick={() => {
            const copy = [...scores]
            copy[idx] = 60
            setScores(copy)
            if (idx + 1 >= lines.length) {
              const avg = Math.round(
                copy.reduce((a, b) => a + (b ?? 0), 0) / lines.length,
              )
              setDone(true)
              onDone(avg)
              return
            }
            setIdx((i) => i + 1)
            setHeard('')
            setStatus('')
            setAttempted(false)
          }}
        >
          O‘tkazib yuborish (60%)
        </button>
      ) : null}
    </section>
  )
}

function PronounceSkill({
  lesson,
  onDone,
}: {
  lesson: Lesson
  onDone: (n: number) => void
}) {
  const [idx, setIdx] = useState(0)
  const [slow, setSlow] = useState(true)
  const [tries, setTries] = useState(0)
  const [heard, setHeard] = useState('')
  const [score, setScore] = useState<number | null>(null)
  const [listening, setListening] = useState(false)
  const [bank, setBank] = useState<number[]>([])
  const [done, setDone] = useState(false)
  const item = lesson.pronounce[idx]
  const supported = speechSupported()

  async function practice() {
    setListening(true)
    setHeard('')
    setScore(null)
    const res = await listenOnce('en-US', 6500)
    setListening(false)
    setTries((t) => t + 1)
    if (!res.ok) return
    setHeard(res.text)
    setScore(scorePronunciation(item.text, res.text))
  }

  function next() {
    const sc = score ?? (supported ? 0 : 70)
    const nextBank = [...bank, sc]
    setBank(nextBank)
    if (idx + 1 >= lesson.pronounce.length) {
      const avg = Math.round(nextBank.reduce((a, b) => a + b, 0) / nextBank.length)
      setDone(true)
      onDone(avg)
      return
    }
    setIdx((i) => i + 1)
    setHeard('')
    setScore(null)
    setTries(0)
  }

  if (done) {
    const avg = Math.round(bank.reduce((a, b) => a + b, 0) / Math.max(1, bank.length))
    return (
      <section className="quiz-result reveal">
        <p className="eyebrow">Talaffuz</p>
        <h1>{avg}%</h1>
      </section>
    )
  }

  return (
    <section className="speak-box reveal">
      <p className="muted">
        {idx + 1}/{lesson.pronounce.length}
      </p>
      <p className="en phrase">{item.text}</p>
      <p className="tip">{item.tip}</p>
      <div className="cta-row">
        <button
          type="button"
          className="btn primary"
          onClick={() => void speak(item.text, { rate: slow ? 0.65 : 0.9 })}
        >
          ▶ Eshitish
        </button>
        <button type="button" className="btn" onClick={() => setSlow((s) => !s)}>
          {slow ? 'Sekin ✓' : 'Oddiy'}
        </button>
      </div>
      <button
        type="button"
        className={`btn primary wide${listening ? ' pulse-btn' : ''}`}
        onClick={() => void practice()}
        disabled={listening || !supported}
      >
        {listening ? 'Tinglanmoqda…' : 'Takrorlang (mikrofon)'}
      </button>
      {heard ? <p className="heard">Siz: “{heard}”</p> : null}
      {score != null ? (
        <p className={score >= 70 ? 'ok-msg' : 'bad-msg'}>Moslik: {score}%</p>
      ) : null}
      <button
        type="button"
        className="btn wide"
        onClick={next}
        disabled={supported && score == null && tries < 1}
      >
        {idx + 1 >= lesson.pronounce.length ? 'Natija' : 'Keyingi →'}
      </button>
    </section>
  )
}

function GameScreen({
  lesson,
  game,
  onBack,
  onHome,
  onDone,
}: {
  lesson: Lesson
  game: GameId
  onBack: () => void
  onHome: () => void
  onDone: (score: number) => void
}) {
  const meta = GAME_LIST.find((g) => g.id === game)!
  return (
    <div className="page lesson-page">
      <Top back={onBack} home={onHome} label={meta.title} />
      <header className="lesson-head tight">
        <p className="eyebrow">{lesson.title} · o‘yin</p>
        <h1>
          {meta.emoji} {meta.title}
        </h1>
        <p className="lead">{meta.blurb}</p>
      </header>
      {game === 'match' ? <MatchGame lesson={lesson} onDone={onDone} /> : null}
      {game === 'scramble' ? <ScrambleGame lesson={lesson} onDone={onDone} /> : null}
      {game === 'memory' ? <MemoryGame lesson={lesson} onDone={onDone} /> : null}
      {game === 'lightning' ? <LightningGame lesson={lesson} onDone={onDone} /> : null}
    </div>
  )
}

function MatchGame({ lesson, onDone }: { lesson: Lesson; onDone: (n: number) => void }) {
  const pairs = useMemo(() => makeMatchPairs(lesson, 5), [lesson])
  const [left] = useState(() => shuffle(pairs))
  const [right] = useState(() => shuffle(pairs))
  const [selL, setSelL] = useState<string | null>(null)
  const [selR, setSelR] = useState<string | null>(null)
  const [matched, setMatched] = useState<string[]>([])
  const [wrong, setWrong] = useState(0)
  const [lock, setLock] = useState(false)
  const [done, setDone] = useState(false)
  const [finalScore, setFinalScore] = useState(0)

  function tryMatch(nextL: string | null, nextR: string | null) {
    if (!nextL || !nextR || lock) return
    setLock(true)
    if (nextL === nextR) {
      const next = [...matched, nextL]
      setMatched(next)
      setSelL(null)
      setSelR(null)
      setLock(false)
      if (next.length >= pairs.length) {
        const score = Math.max(20, 100 - wrong * 10)
        setFinalScore(score)
        setDone(true)
        onDone(score)
      }
      return
    }
    setWrong((w) => w + 1)
    window.setTimeout(() => {
      setSelL(null)
      setSelR(null)
      setLock(false)
    }, 450)
  }

  if (done) {
    return (
      <section className="quiz-result reveal">
        <h1>{finalScore}</h1>
        <p className="lead">Juftlar topildi!</p>
      </section>
    )
  }

  return (
    <section className="match-board reveal">
      <div className="match-col">
        {left.map((p: MatchPair) => (
          <button
            key={`l-${p.id}`}
            type="button"
            className={`match-chip${matched.includes(p.id) ? ' matched' : ''}${selL === p.id ? ' sel' : ''}`}
            disabled={matched.includes(p.id) || lock}
            onClick={() => {
              setSelL(p.id)
              tryMatch(p.id, selR)
            }}
          >
            {p.en}
          </button>
        ))}
      </div>
      <div className="match-col">
        {right.map((p: MatchPair) => (
          <button
            key={`r-${p.id}`}
            type="button"
            className={`match-chip uz${matched.includes(p.id) ? ' matched' : ''}${selR === p.id ? ' sel' : ''}`}
            disabled={matched.includes(p.id) || lock}
            onClick={() => {
              setSelR(p.id)
              tryMatch(selL, p.id)
            }}
          >
            {p.uz}
          </button>
        ))}
      </div>
    </section>
  )
}

function ScrambleGame({ lesson, onDone }: { lesson: Lesson; onDone: (n: number) => void }) {
  const words = useMemo(
    () => shuffle(lesson.words.filter((w) => !w.en.includes(' '))).slice(0, 6),
    [lesson],
  )
  const [idx, setIdx] = useState(0)
  const [scrambled, setScrambled] = useState(() => scrambleWord(words[0]?.en || 'hi'))
  const [value, setValue] = useState('')
  const [correct, setCorrect] = useState(0)
  const [done, setDone] = useState(false)
  const target = words[idx]?.en || ''

  useEffect(() => {
    setScrambled(scrambleWord(target.replace(/\s+/g, '')))
    setValue('')
  }, [idx, target])

  function check() {
    const ok = answersMatch(value, target)
    const nextCorrect = correct + (ok ? 1 : 0)
    if (ok) setCorrect(nextCorrect)
    if (idx + 1 >= words.length) {
      setDone(true)
      onDone(Math.round((nextCorrect / words.length) * 100))
      return
    }
    setIdx((i) => i + 1)
  }

  if (done) {
    return (
      <section className="quiz-result reveal">
        <h1>{Math.round((correct / words.length) * 100)}</h1>
        <p className="lead">Harflar yig‘ildi</p>
      </section>
    )
  }

  return (
    <section className="write-box reveal">
      <p className="muted">
        {idx + 1}/{words.length}
      </p>
      <p className="scramble-letters">{scrambled.split('').join(' ')}</p>
      <p className="uz">{words[idx]?.uz}</p>
      <input
        className="text-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="So‘zni yozing"
        onKeyDown={(e) => {
          if (e.key === 'Enter') check()
        }}
      />
      <button type="button" className="btn primary wide" onClick={check}>
        Keyingi
      </button>
    </section>
  )
}

function MemoryGame({ lesson, onDone }: { lesson: Lesson; onDone: (n: number) => void }) {
  const [cards] = useState<MemoryCard[]>(() => makeMemoryCards(lesson, 4))
  const [open, setOpen] = useState<string[]>([])
  const [matched, setMatched] = useState<string[]>([])
  const [moves, setMoves] = useState(0)
  const [done, setDone] = useState(false)
  const [lock, setLock] = useState(false)

  function flip(id: string) {
    if (lock || matched.includes(id) || open.includes(id)) return
    const next = [...open, id]
    setOpen(next)
    if (next.length < 2) return
    setLock(true)
    setMoves((m) => m + 1)
    const [a, b] = next.map((x) => cards.find((c) => c.id === x)!)
    window.setTimeout(() => {
      if (a.pairId === b.pairId) {
        const m = [...matched, a.id, b.id]
        setMatched(m)
        setOpen([])
        setLock(false)
        if (m.length >= cards.length) {
          const score = Math.max(30, 100 - (moves + 1) * 5)
          setDone(true)
          onDone(score)
        }
      } else {
        setOpen([])
        setLock(false)
      }
    }, 550)
  }

  if (done) {
    return (
      <section className="quiz-result reveal">
        <h1>{Math.max(30, 100 - moves * 5)}</h1>
        <p className="lead">{moves} yurish</p>
      </section>
    )
  }

  return (
    <section className="memory-grid reveal">
      {cards.map((c) => {
        const show = open.includes(c.id) || matched.includes(c.id)
        return (
          <button
            key={c.id}
            type="button"
            className={`mem-card${show ? ' show' : ''}${matched.includes(c.id) ? ' matched' : ''}`}
            onClick={() => flip(c.id)}
          >
            <span>{show ? c.label : '?'}</span>
          </button>
        )
      })}
    </section>
  )
}

function LightningGame({ lesson, onDone }: { lesson: Lesson; onDone: (n: number) => void }) {
  const pool = useMemo(() => shuffle(lesson.quiz), [lesson])
  const [time, setTime] = useState(60)
  const [idx, setIdx] = useState(0)
  const [score, setScore] = useState(0)
  const [done, setDone] = useState(false)
  const scoreRef = useRef(0)
  const doneCb = useRef(onDone)
  doneCb.current = onDone
  const q = pool[idx % pool.length]

  useEffect(() => {
    if (done) return
    if (time <= 0) {
      setDone(true)
      doneCb.current(scoreRef.current)
      return
    }
    const t = window.setTimeout(() => setTime((x) => x - 1), 1000)
    return () => window.clearTimeout(t)
  }, [time, done])

  function pick(i: number) {
    if (done) return
    if (i === q.answer) {
      scoreRef.current += 10
      setScore(scoreRef.current)
    }
    setIdx((x) => x + 1)
  }

  if (done) {
    return (
      <section className="quiz-result reveal">
        <p className="eyebrow">Chaqmoq</p>
        <h1>{score}</h1>
        <p className="lead">ball</p>
      </section>
    )
  }

  return (
    <section className="quiz-box reveal">
      <div className="timer-row">
        <span className={`timer${time < 10 ? ' hot' : ''}`}>{time}s</span>
        <strong>{score} ball</strong>
      </div>
      <h1 className="q-prompt">{q.prompt}</h1>
      <div className="options">
        {q.options.map((opt, i) => (
          <button key={opt} type="button" className="opt" onClick={() => pick(i)}>
            {opt}
          </button>
        ))}
      </div>
    </section>
  )
}
