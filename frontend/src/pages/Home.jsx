import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <main>
      {/* ═══ Hero ═══ */}
      <section className="hero">
        <div className="container">
          <div className="hero-badge">
            <span className="dot" />
            <span>6-Step AI Pipeline • Powered by Gemini</span>
          </div>

          <h1>
            Transform Ideas into<br />
            <span className="gradient-text">Stunning Cheatsheets</span>
          </h1>

          <p>
            Enter a topic or upload an existing cheatsheet — our AI pipeline analyzes,
            researches trends, and generates professional visual cheatsheets in seconds.
          </p>

          <div className="hero-buttons">
            <Link to="/generate" className="btn btn-primary btn-lg">
              ⚡ Generate Cheatsheet
            </Link>
            <a href="#how-it-works" className="btn btn-secondary btn-lg">
              Learn More →
            </a>
          </div>
        </div>
      </section>

      {/* ═══ Features ═══ */}
      <section className="features">
        <div className="container">
          <div className="section-title">
            <h2>Why CheatSheet AI?</h2>
            <p>Six intelligent steps working together to create the perfect cheatsheet</p>
          </div>

          <div className="features-grid">
            <div className="card feature-card">
              <div className="feature-icon" style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>🧠</div>
              <h3>Smart Understanding</h3>
              <p>Gemini Pro analyzes your topic, identifies key subtopics, difficulty level, and the best structure for your cheatsheet.</p>
            </div>

            <div className="card feature-card">
              <div className="feature-icon" style={{ background: 'rgba(139,92,246,0.15)', color: '#8b5cf6' }}>🔍</div>
              <h3>Trend Research</h3>
              <p>Deep Research discovers the latest trends, best practices, and recommends color palettes, layouts, and visual styles.</p>
            </div>

            <div className="card feature-card">
              <div className="feature-icon" style={{ background: 'rgba(6,182,212,0.15)', color: '#06b6d4' }}>📸</div>
              <h3>Image Analysis</h3>
              <p>Upload an existing cheatsheet and our AI extracts content, analyzes structure, and creates an improved version.</p>
            </div>

            <div className="card feature-card">
              <div className="feature-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>🎨</div>
              <h3>Visual Generation</h3>
              <p>Gemini generates professional cheatsheet visuals with modern design — dark themes, organized grids, and clean typography.</p>
            </div>

            <div className="card feature-card">
              <div className="feature-icon" style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981' }}>📄</div>
              <h3>HTML Output</h3>
              <p>Every cheatsheet comes as a beautifully styled HTML document you can open in any browser, print, or share.</p>
            </div>

            <div className="card feature-card">
              <div className="feature-icon" style={{ background: 'rgba(244,63,94,0.15)', color: '#f43f5e' }}>⚡</div>
              <h3>Smart Retry</h3>
              <p>Built-in rate limit handling with automatic retries and model fallback chains ensures reliable generation every time.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ Pipeline Flow ═══ */}
      <section className="pipeline-section" id="how-it-works">
        <div className="container">
          <div className="section-title">
            <h2>How It Works</h2>
            <p>A 6-step AI pipeline that transforms your input into a professional cheatsheet</p>
          </div>

          <div className="pipeline-flow">
            {[
              { num: 1, icon: '🧠', name: 'Understand', model: 'Gemini Pro' },
              { num: 2, icon: '📸', name: 'Analyze Image', model: 'Nano Banana' },
              { num: 3, icon: '🔍', name: 'Trend Research', model: 'Deep Research' },
              { num: 4, icon: '📝', name: 'Build Prompt', model: 'Prompt Builder' },
              { num: 5, icon: '⚙️', name: 'Generate', model: 'Gemini Pro' },
              { num: 6, icon: '🎨', name: 'Visualize', model: 'Image Gen' },
            ].map((step) => (
              <div className="flow-step" key={step.num}>
                <div className="flow-step-number">{step.num}</div>
                <div className="flow-step-icon">{step.icon}</div>
                <div className="flow-step-name">{step.name}</div>
                <div className="flow-step-model">{step.model}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section style={{ padding: '80px 0' }}>
        <div className="container" style={{ textAlign: 'center' }}>
          <div className="card" style={{
            padding: '60px 40px',
            background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08))',
            border: '1px solid rgba(59,130,246,0.2)',
            maxWidth: 700,
            margin: '0 auto',
          }}>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: 12 }}>
              Ready to Create?
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: '1.05rem' }}>
              Start generating professional cheatsheets in seconds
            </p>
            <Link to="/generate" className="btn btn-primary btn-lg">
              ⚡ Start Generating
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
