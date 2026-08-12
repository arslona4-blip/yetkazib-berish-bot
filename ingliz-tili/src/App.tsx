import { useEffect, useMemo, useState } from 'react'
import { LESSONS, LEVEL_LABEL, type Level } from './lessons'
import { loadProgress, markDone, type Progress } from './progress'
import { speak, stopSpeak } from './tts'
import './styles.css'

type View = 'home' | 'lesson' | 'quiz'
type Tab = 'words' | 'phrases'

export default function App() {
  const [view, setView] = useState<View>('home')
  const [lessonId, setLessonId] = useState(LESSONS[0].id)
  const [progress, setProgress] = useState<Progress>(() => loadProgress())
  const [filter, setFilter] = useState<'all' | Level>('all')
  const [tab, setTab] = useState<Tab>('words')
  const [wordIdx, setWordIdx] = useState(0)
  const [phraseIdx, setPhraseIdx] = useState(0)
  const [quizIdx, setQuizIdx] = useState(0)
  const [picked, setPicked] = useState<number | null>(null)
  const [correctCount, setCorrectCount] = useState(0)
  const [quizDone, setQuizDone] = useState(false)
  const [flash, setFlash] = useState(false)

  const lesson = useMemo(
    () => LESSONS.find((l) => l.id === lessonId) || LESSONS[0],
    [lessonId],
  )

  const filtered = useMemo(() => {
    if (filter === 'all') return LESSONS
    return LESSONS.filter((l) => l.level === filter)
  }, [filter])

  const progressPct = Math.round((progress.done.length / LESSONS.length) * 100)

  useEffect(() => () => stopSpeak(), [])

  function openLesson(id: string) {
    stopSpeak()
    setLessonId(id)
    setView('lesson')
    setTab('words')
    setWordIdx(0)
    setPhraseIdx(0)
    setQuizIdx(0)
    setPicked(null)
    setCorrectCount(0)
    setQuizDone(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function startQuiz() {
    stopSpeak()
    setView('quiz')
    setQuizIdx(0)
    setPicked(null)
    setCorrectCount(0)
    setQuizDone(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function say(text: string) {
    setFlash(true)
    void speak(text)
    window.setTimeout(() => setFlash(false), 280)
  }

  function answer(i: number) {
    if (picked !== null || quizDone) return
    setPicked(i)
    if (i === lesson.quiz[quizIdx].answer) {
      setCorrectCount((c) => c + 1)
    }
  }

  function goNextAfterAnswer() {
    if (picked === null) return
    if (quizIdx + 1 >= lesson.quiz.length) {
      const score = Math.round((correctCount / lesson.quiz.length) * 100)
      setProgress(markDone(lesson.id, score))
      setQuizDone(true)
      return
    }
    setQuizIdx((x) => x + 1)
    setPicked(null)
  }

  if (view === 'home') {
    return (
      <div className="page">
        <header className="hero">
          <div className="hero-bg" aria-hidden />
          <div className="hero-wave" aria-hidden />
          <p className="eyebrow">O‘zbek → English · PWA</p>
          <h1 className="brand">Ingliz</h1>
          <p className="lead">
            So‘zlar, gaplar va qisqa testlar. Eshitib o‘rganing — bir tugma bilan
            talaffuz.
          </p>
          <div className="progress-wrap">
            <div className="progress-meta">
              <span>Progress</span>
              <strong>
                {progress.done.length}/{LESSONS.length} · {progressPct}%
              </strong>
            </div>
            <div className="bar">
              <i style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        </header>

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
            const score = progress.scores[l.id]
            return (
              <button
                key={l.id}
                type="button"
                className={`lesson-btn${isDone ? ' done' : ''}`}
                onClick={() => openLesson(l.id)}
              >
                <div className="lesson-top">
                  <span className="num">{String(l.num).padStart(2, '0')}</span>
                  <span className="tag">{LEVEL_LABEL[l.level]}</span>
                </div>
                <h2>{l.title}</h2>
                <p>{l.summary}</p>
                <div className="lesson-foot">
                  <span>
                    {l.minutes} daq · {l.words.length} so‘z
                  </span>
                  <span>{isDone ? `✓ ${score ?? 0}%` : 'Boshlash →'}</span>
                </div>
              </button>
            )
          })}
        </section>

        <footer className="foot">
          1-darsdan boshlang: Salomlashish. Ovoz brauzer Speech API orqali.
        </footer>
      </div>
    )
  }

  const word = lesson.words[wordIdx]
  const phrase = lesson.phrases[phraseIdx]
  const q = lesson.quiz[quizIdx]
  const idx = LESSONS.findIndex((l) => l.id === lesson.id)
  const isDone = progress.done.includes(lesson.id)

  if (view === 'quiz') {
    const scorePct = Math.round((correctCount / lesson.quiz.length) * 100)
    return (
      <div className="page lesson-page">
        <div className="topbar">
          <button
            type="button"
            className="ghost"
            onClick={() => {
              stopSpeak()
              setView('lesson')
              setTab('words')
            }}
          >
            ← Dars
          </button>
          <span className="muted">
            Test · {Math.min(quizIdx + 1, lesson.quiz.length)}/{lesson.quiz.length}
          </span>
          <button type="button" className="ghost" onClick={() => setView('home')}>
            Bosh
          </button>
        </div>

        {quizDone ? (
          <section className="quiz-result reveal">
            <p className="eyebrow">Natija</p>
            <h1>{scorePct}%</h1>
            <p className="lead">
              {correctCount}/{lesson.quiz.length} to‘g‘ri. Dars belgilab qo‘yildi.
            </p>
            <div className="cta-row">
              <button
                type="button"
                className="btn primary"
                onClick={() => openLesson(lesson.id)}
              >
                Darsga qaytish
              </button>
              <button
                type="button"
                className="btn"
                onClick={() =>
                  openLesson(LESSONS[(idx + 1) % LESSONS.length].id)
                }
              >
                Keyingi dars
              </button>
            </div>
          </section>
        ) : (
          <section className="quiz-box reveal">
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
              <button
                type="button"
                className="btn primary wide"
                onClick={goNextAfterAnswer}
              >
                {quizIdx + 1 >= lesson.quiz.length
                  ? 'Natijani ko‘rish'
                  : 'Keyingi →'}
              </button>
            ) : null}
          </section>
        )}
      </div>
    )
  }

  return (
    <div className="page lesson-page">
      <div className="topbar">
        <button
          type="button"
          className="ghost"
          onClick={() => {
            stopSpeak()
            setView('home')
          }}
        >
          ← Ro‘yxat
        </button>
        <span className="muted">
          {idx + 1}/{LESSONS.length}
        </span>
        <button
          type="button"
          className={`ghost${isDone ? ' ok' : ''}`}
          onClick={startQuiz}
        >
          Test
        </button>
      </div>

      <header className="lesson-head">
        <p className="eyebrow">
          {LEVEL_LABEL[lesson.level]} · {lesson.minutes} daq
        </p>
        <h1>{lesson.title}</h1>
        <p className="lead">{lesson.tip}</p>
      </header>

      <nav className="tabs" aria-label="Bo‘lim">
        <button
          type="button"
          className={`tab${tab === 'words' ? ' on' : ''}`}
          onClick={() => setTab('words')}
        >
          So‘zlar
        </button>
        <button
          type="button"
          className={`tab${tab === 'phrases' ? ' on' : ''}`}
          onClick={() => setTab('phrases')}
        >
          Gaplar
        </button>
        <button type="button" className="tab" onClick={startQuiz}>
          Test
        </button>
      </nav>

      {tab === 'words' && word ? (
        <section className={`flashcard${flash ? ' pulse' : ''}`}>
          <button
            type="button"
            className="speak"
            aria-label="Talaffuz"
            onClick={() => say(word.en)}
          >
            ♪
          </button>
          <p className="en">{word.en}</p>
          <p className="uz">{word.uz}</p>
          {word.tip ? <p className="tip">{word.tip}</p> : null}
          <div className="nav-row">
            <button
              type="button"
              className="btn"
              disabled={wordIdx === 0}
              onClick={() => setWordIdx((i) => Math.max(0, i - 1))}
            >
              ←
            </button>
            <span className="muted">
              {wordIdx + 1}/{lesson.words.length}
            </span>
            <button
              type="button"
              className="btn"
              disabled={wordIdx >= lesson.words.length - 1}
              onClick={() =>
                setWordIdx((i) => Math.min(lesson.words.length - 1, i + 1))
              }
            >
              →
            </button>
          </div>
          <button
            type="button"
            className="btn primary wide"
            onClick={() => say(word.en)}
          >
            Eshitish
          </button>
        </section>
      ) : null}

      {tab === 'phrases' && phrase ? (
        <section className={`flashcard${flash ? ' pulse' : ''}`}>
          <button
            type="button"
            className="speak"
            aria-label="Talaffuz"
            onClick={() => say(phrase.en)}
          >
            ♪
          </button>
          <p className="en phrase">{phrase.en}</p>
          <p className="uz">{phrase.uz}</p>
          <div className="nav-row">
            <button
              type="button"
              className="btn"
              disabled={phraseIdx === 0}
              onClick={() => setPhraseIdx((i) => Math.max(0, i - 1))}
            >
              ←
            </button>
            <span className="muted">
              {phraseIdx + 1}/{lesson.phrases.length}
            </span>
            <button
              type="button"
              className="btn"
              disabled={phraseIdx >= lesson.phrases.length - 1}
              onClick={() =>
                setPhraseIdx((i) =>
                  Math.min(lesson.phrases.length - 1, i + 1),
                )
              }
            >
              →
            </button>
          </div>
          <button
            type="button"
            className="btn primary wide"
            onClick={() => say(phrase.en)}
          >
            Eshitish
          </button>
        </section>
      ) : null}

      <div className="cta-row bottom">
        <button type="button" className="btn primary" onClick={startQuiz}>
          Testni boshlash
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => openLesson(LESSONS[(idx + 1) % LESSONS.length].id)}
        >
          Keyingi dars
        </button>
      </div>
    </div>
  )
}
