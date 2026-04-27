import { Link } from 'react-router-dom'
import { useEffect, useRef, useState, useCallback } from 'react'

/* ── Animated Gradient Mesh Canvas (Linear/Vercel style) ── */
function GradientMesh() {
  const ref = useRef(null)
  useEffect(() => {
    const c = ref.current; if (!c) return
    const ctx = c.getContext('2d')
    let w, h, raf, mouse = { x: 0.5, y: 0.5 }, t = 0
    const resize = () => { w = c.width = window.innerWidth; h = c.height = window.innerHeight }
    resize()
    const onMouse = e => { mouse.x = e.clientX / w; mouse.y = e.clientY / h }
    window.addEventListener('mousemove', onMouse)
    window.addEventListener('resize', resize)

    // Blob definitions — warm AI palette (no blue)
    const blobs = [
      { x: 0.2, y: 0.3, r: 0.45, vx: 0.0003, vy: 0.0004, color: [244, 63, 94] },    // rose
      { x: 0.8, y: 0.2, r: 0.4, vx: -0.0004, vy: 0.0003, color: [168, 85, 247] },    // violet
      { x: 0.5, y: 0.8, r: 0.5, vx: 0.0002, vy: -0.0005, color: [251, 146, 60] },    // orange
      { x: 0.3, y: 0.6, r: 0.35, vx: -0.0003, vy: -0.0002, color: [16, 185, 129] },  // emerald
      { x: 0.7, y: 0.7, r: 0.3, vx: 0.0005, vy: 0.0002, color: [139, 92, 246] },     // purple
      { x: 0.1, y: 0.1, r: 0.25, vx: 0.0002, vy: 0.0006, color: [245, 158, 11] },    // amber
    ]

    const draw = () => {
      t += 0.008
      // Deep dark base
      ctx.fillStyle = '#030014'
      ctx.fillRect(0, 0, w, h)

      // Move blobs + mouse influence
      blobs.forEach(b => {
        b.x += b.vx + Math.sin(t * 1.5 + b.r * 10) * 0.001
        b.y += b.vy + Math.cos(t * 1.2 + b.r * 8) * 0.001
        // Mouse attraction (subtle)
        b.x += (mouse.x - b.x) * 0.0008
        b.y += (mouse.y - b.y) * 0.0008
        // Bounce
        if (b.x < -0.1 || b.x > 1.1) b.vx *= -1
        if (b.y < -0.1 || b.y > 1.1) b.vy *= -1
      })

      // Draw each blob as a radial gradient
      blobs.forEach(b => {
        const px = b.x * w, py = b.y * h
        const radius = b.r * Math.max(w, h) * (0.9 + Math.sin(t + b.r * 5) * 0.15)
        const grad = ctx.createRadialGradient(px, py, 0, px, py, radius)
        const [r, g, bl] = b.color
        grad.addColorStop(0, `rgba(${r},${g},${bl},0.25)`)
        grad.addColorStop(0.4, `rgba(${r},${g},${bl},0.08)`)
        grad.addColorStop(1, `rgba(${r},${g},${bl},0)`)
        ctx.globalCompositeOperation = 'screen'
        ctx.fillStyle = grad
        ctx.fillRect(0, 0, w, h)
      })

      // Mouse spotlight
      const mx = mouse.x * w, my = mouse.y * h
      const spotlight = ctx.createRadialGradient(mx, my, 0, mx, my, 400)
      spotlight.addColorStop(0, 'rgba(244,63,94,0.06)')
      spotlight.addColorStop(1, 'rgba(244,63,94,0)')
      ctx.globalCompositeOperation = 'screen'
      ctx.fillStyle = spotlight
      ctx.fillRect(0, 0, w, h)

      ctx.globalCompositeOperation = 'source-over'
      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(raf); window.removeEventListener('mousemove', onMouse); window.removeEventListener('resize', resize) }
  }, [])
  return <canvas ref={ref} className="gradient-mesh-canvas" />
}


/* ── Scroll reveal hook ── */
function useReveal() {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current; if (!el) return
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect() } }, { threshold: 0.15 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  return [ref, visible]
}

function Reveal({ children, delay = 0, direction = 'up' }) {
  const [ref, visible] = useReveal()
  const transforms = { up: 'translateY(40px)', down: 'translateY(-40px)', left: 'translateX(40px)', right: 'translateX(-40px)', scale: 'scale(0.9)' }
  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'none' : transforms[direction],
      transition: `all 0.7s cubic-bezier(0.16,1,0.3,1) ${delay}s`,
    }}>{children}</div>
  )
}

/* ── Counter ── */
function Counter({ end, suffix = '' }) {
  const [count, setCount] = useState(0)
  const ref = useRef(null)
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let v = 0; const step = end / 40
        const t = setInterval(() => { v += step; if (v >= end) { setCount(end); clearInterval(t) } else setCount(Math.floor(v)) }, 30)
        obs.disconnect()
      }
    }, { threshold: 0.5 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [end])
  return <span ref={ref}>{count}{suffix}</span>
}

/* ── Typewriter ── */
function TypeWriter({ words }) {
  const [text, setText] = useState('')
  const [wi, setWi] = useState(0)
  const [ci, setCi] = useState(0)
  const [del, setDel] = useState(false)
  useEffect(() => {
    const w = words[wi]
    const t = setTimeout(() => {
      if (!del) {
        setText(w.slice(0, ci + 1))
        if (ci + 1 === w.length) { setTimeout(() => setDel(true), 2000); return }
        setCi(c => c + 1)
      } else {
        setText(w.slice(0, ci))
        if (ci === 0) { setDel(false); setWi(i => (i + 1) % words.length); return }
        setCi(c => c - 1)
      }
    }, del ? 35 : 70)
    return () => clearTimeout(t)
  }, [ci, del, wi, words])
  return <>{text}<span className="tw-cursor">|</span></>
}

/* ── 3D Tilt Card ── */
function TiltCard({ children, className, style }) {
  const ref = useRef(null)
  const onMove = useCallback(e => {
    const el = ref.current; if (!el) return
    const r = el.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width - 0.5
    const y = (e.clientY - r.top) / r.height - 0.5
    el.style.transform = `perspective(800px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) scale(1.02)`
  }, [])
  const onLeave = useCallback(() => { if (ref.current) ref.current.style.transform = 'none' }, [])
  return <div ref={ref} className={className} style={style} onMouseMove={onMove} onMouseLeave={onLeave}>{children}</div>
}

export default function Home() {
  const [activeStep, setActiveStep] = useState(0)
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setActiveStep(s => (s + 1) % 6), 2500)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <main className="landing">
      {/* ═══ HERO ═══ */}
      <section className="hero-ultra">
        <GradientMesh />
        <div className="hero-noise" />
        <div className="hero-grid" />
        <div className="hero-beam hero-beam-1" />
        <div className="hero-beam hero-beam-2" />
        <div className="hero-beam hero-beam-3" />
        <div className="hero-vignette" />

        {/* 3D Floating Elements */}
        <div className="float-3d float-cube" style={{animationDelay:'0s'}} />
        <div className="float-3d float-ring" style={{animationDelay:'2s'}} />
        <div className="float-3d float-pyramid" style={{animationDelay:'4s'}} />
        <div className="float-3d float-sphere" style={{animationDelay:'1s'}} />
        <div className="float-3d float-dots" style={{animationDelay:'3s'}} />

        <div className="container hero-inner" style={{ transform: `translateY(${scrollY * 0.15}px)`, opacity: Math.max(0, 1 - scrollY / 600) }}>
          <div className="hero-chip">
            <span className="chip-dot" />
            <span>6-Step AI Pipeline</span>
            <span className="chip-sep">|</span>
            <span>Powered by Gemini</span>
            <span className="chip-live">● LIVE</span>
          </div>

          <h1 className="hero-title">
            Transform Ideas into<br />
            <span className="hero-gradient"><TypeWriter words={['Stunning Cheatsheets', 'Visual Mind-Maps', 'Learning Infographics', 'Knowledge Posters']} /></span>
          </h1>

          <p className="hero-desc">
            Enter any topic or upload an existing cheatsheet — our AI pipeline analyzes, researches trends, and generates <strong>professional visual mind-maps</strong> in seconds.
          </p>

          <div className="hero-actions">
            <Link to="/generate" className="btn-hero-primary">
              <span className="btn-shimmer" />
              <span className="btn-icon">⚡</span> Generate Cheatsheet
            </Link>
            <a href="#features" className="btn-hero-ghost">
              Explore Features <span className="arrow-bounce">↓</span>
            </a>
          </div>

          <div className="hero-metrics">
            {[
              { val: 6, suf: '', label: 'AI Steps' },
              { val: 4, suf: '', label: 'API Keys' },
              { val: 24, suf: '+', label: 'Model Fallbacks' },
              { val: 3200, suf: 'px', label: 'Output Width' },
            ].map((m, i) => (
              <div className="metric" key={i}>
                <span className="metric-val"><Counter end={m.val} suffix={m.suf} /></span>
                <span className="metric-label">{m.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="scroll-hint">
          <div className="scroll-mouse"><div className="scroll-wheel" /></div>
          <span>Scroll</span>
        </div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section className="section-dark" id="features">
        <div className="container">
          <Reveal><div className="sec-head">
            <span className="sec-chip">✨ Features</span>
            <h2>Why CheatSheet <span className="hero-gradient">AI</span>?</h2>
            <p>Six intelligent AI steps that craft the perfect visual cheatsheet</p>
          </div></Reveal>

          <div className="feat-grid">
            {[
              { icon: '🧠', title: 'Smart Understanding', desc: 'Gemini Pro analyzes your topic, identifies subtopics, difficulty level, and optimal structure.', color: '#f43f5e', tag: 'NLP' },
              { icon: '🔍', title: 'Trend Research', desc: 'Deep Research discovers 2025-2026 trends, best practices, and modern visual styles.', color: '#a855f7', tag: 'Research' },
              { icon: '📸', title: 'Image Analysis', desc: 'Upload any cheatsheet — AI extracts content, analyzes structure, creates an improved version.', color: '#fb923c', tag: 'Vision' },
              { icon: '🎨', title: 'Mind-Map Generator', desc: 'Generates 3200×2000 mind-map PNGs with curved arrows, glass cards, and particle effects.', color: '#f59e0b', tag: 'Visual' },
              { icon: '📄', title: 'Dual Output', desc: 'Get both an interactive HTML cheatsheet AND a downloadable mind-map image.', color: '#10b981', tag: 'Export' },
              { icon: '⚡', title: 'Smart Retry Engine', desc: '4 API keys × 6 models = 24 fallback combinations. Rate-limit proof.', color: '#ec4899', tag: 'Resilient' },
            ].map((f, i) => (
              <Reveal key={i} delay={i * 0.08}>
                <TiltCard className="feat-card" style={{ '--ac': f.color }}>
                  <div className="feat-glow" />
                  <span className="feat-tag">{f.tag}</span>
                  <div className="feat-icon">{f.icon}</div>
                  <h3>{f.title}</h3>
                  <p>{f.desc}</p>
                  <div className="feat-bar" />
                </TiltCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ PIPELINE ═══ */}
      <section className="section-darker" id="how-it-works">
        <div className="container">
          <Reveal><div className="sec-head">
            <span className="sec-chip">🔧 Pipeline</span>
            <h2>How It <span className="hero-gradient">Works</span></h2>
            <p>Watch each step of the AI pipeline in action</p>
          </div></Reveal>

          <div className="pipe-wrap">
            <div className="pipe-line-bg" />
            {[
              { icon: '🧠', name: 'Understand', model: 'Gemini Pro', desc: 'Analyzes topic, extracts subtopics and difficulty' },
              { icon: '📸', name: 'Analyze Image', model: 'Nano Banana', desc: 'Extracts structure from uploaded cheatsheets' },
              { icon: '🔍', name: 'Research Trends', model: 'Deep Research', desc: 'Finds latest trends and best practices' },
              { icon: '📝', name: 'Build Prompt', model: 'Prompt Builder', desc: 'Creates optimized mega-prompt from all data' },
              { icon: '⚙️', name: 'Generate Content', model: 'Gemini Pro', desc: 'Produces structured JSON with sections' },
              { icon: '🎨', name: 'Render Mind-Map', model: 'Pillow Engine', desc: 'Creates 3200×2000 PNG with glass cards' },
            ].map((s, i) => (
              <Reveal key={i} delay={i * 0.1} direction="left">
                <div className={`pipe-step ${i === activeStep ? 'active' : ''} ${i < activeStep ? 'done' : ''}`}>
                  <div className="pipe-num">{i + 1}</div>
                  <div className="pipe-icon">{s.icon}</div>
                  <div className="pipe-info">
                    <h4>{s.name}</h4>
                    <span className="pipe-model">{s.model}</span>
                    <p>{s.desc}</p>
                  </div>
                  {i === activeStep && <div className="pipe-pulse" />}
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ OUTPUT SHOWCASE ═══ */}
      <section className="section-dark">
        <div className="container">
          <Reveal><div className="sec-head">
            <span className="sec-chip">🖼️ Output</span>
            <h2>What You <span className="hero-gradient">Get</span></h2>
            <p>Professional mind-map + HTML cheatsheet in one click</p>
          </div></Reveal>

          <Reveal delay={0.15} direction="scale">
            <div className="showcase-wrap">
              <div className="show-browser-bar">
                <div className="show-dots"><i /><i /><i /></div>
                <div className="show-url">cheatsheet-ai.app / generate</div>
              </div>
              <div className="show-body">
                {[
                  { icon: '🗺️', title: 'Mind-Map PNG (3200×2000)', desc: 'Central hub, curved Bezier arrows, glassmorphism cards, stars, tech icons' },
                  { icon: '📋', title: 'Interactive HTML Cheatsheet', desc: 'Dark theme, code blocks, pro tips, trend tags, fully responsive' },
                  { icon: '⚡', title: 'Mega-Prompt Architecture', desc: 'Single API call = 3× less usage, faster generation, smarter output' },
                ].map((f, i) => (
                  <Reveal key={i} delay={0.1 * i} direction="right">
                    <div className="show-row">
                      <div className="show-icon">{f.icon}</div>
                      <div><h4>{f.title}</h4><p>{f.desc}</p></div>
                    </div>
                  </Reveal>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="cta-ultra">
        <div className="cta-aurora" />
        <div className="container" style={{ position: 'relative', zIndex: 2 }}>
          <Reveal direction="scale">
            <div className="cta-box">
              <h2>Ready to Create Something <span className="hero-gradient">Amazing</span>?</h2>
              <p>Generate professional mind-map cheatsheets — free, no signup</p>
              <Link to="/generate" className="btn-hero-primary" style={{ fontSize: '1.1rem', padding: '18px 40px' }}>
                <span className="btn-shimmer" />
                <span className="btn-icon">⚡</span> Start Generating Now
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </main>
  )
}
