export default function ResultViewer({ result }) {
  if (!result) return null

  const { title, text_output, image_output, analysis, mode, generation_time } = result

  const handleDownload = async (url, filename) => {
    try {
      const res = await fetch(url)
      const blob = await res.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    } catch {
      window.open(url, '_blank')
    }
  }

  return (
    <div className="result-container" style={{ animation: 'fadeInUp 0.5s ease' }}>
      {/* ── Success Banner ── */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(59,130,246,0.1))',
        border: '1px solid rgba(16,185,129,0.3)',
        marginBottom: 20,
        padding: '20px 24px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: '2rem' }}>🎉</span>
          <div style={{ flex: 1 }}>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800 }}>
              {title || 'Your Cheatsheet is Ready!'}
            </h2>
            {analysis && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 2 }}>
                {analysis.topic} • {analysis.difficulty} • {analysis.subtopics?.length || 0} subtopics
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ── Mind-Map Image Preview (PRIMARY) ── */}
      {image_output && (
        <div style={{ marginBottom: 24 }}>
          <div style={{
            borderRadius: 16,
            overflow: 'hidden',
            border: '2px solid rgba(59,130,246,0.2)',
            background: '#060a14',
          }}>
            <img
              src={image_output}
              alt={`Mind-map: ${title}`}
              style={{
                width: '100%',
                height: 'auto',
                display: 'block',
              }}
            />
          </div>
        </div>
      )}

      {/* ── Download Buttons ── */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {image_output && (
          <button
            className="btn btn-primary"
            onClick={() => handleDownload(image_output, result.image_filename || 'cheatsheet_mindmap.png')}
            style={{
              fontSize: '0.95rem',
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #f43f5e, #a855f7)',
            }}
          >
            🖼️ Download Mind-Map (PNG)
          </button>
        )}
        {text_output && (
          <button
            className="btn btn-secondary"
            onClick={() => handleDownload(text_output, result.text_filename || 'cheatsheet.html')}
            style={{ fontSize: '0.9rem' }}
          >
            📄 Download HTML
          </button>
        )}
        {image_output && (
          <a
            href={image_output}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ fontSize: '0.9rem' }}
          >
            🔗 Open Image Full Size
          </a>
        )}
      </div>

      {/* ── HTML Cheatsheet Preview (secondary, collapsible) ── */}
      {text_output && (text_output.endsWith('.html') || text_output.includes('.html')) && (
        <details style={{ marginTop: 16 }}>
          <summary style={{
            cursor: 'pointer',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem',
            padding: '8px 0',
            userSelect: 'none',
          }}>
            📋 Show HTML Cheatsheet Preview
          </summary>
          <div className="result-frame" style={{ marginTop: 10 }}>
            <iframe
              src={text_output}
              title="Generated Cheatsheet"
              sandbox="allow-same-origin"
            />
          </div>
        </details>
      )}

      {/* ── Analysis Tags ── */}
      {analysis && analysis.subtopics && analysis.subtopics.length > 0 && (
        <div className="card" style={{ marginTop: 24 }}>
          <h3 style={{ marginBottom: 12, fontSize: '1rem', fontWeight: 700, color: 'var(--accent-amber)' }}>
            📊 Content Breakdown
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {analysis.subtopics.map((topic, i) => (
              <span
                key={i}
                style={{
                  padding: '4px 12px',
                  background: 'rgba(59,130,246,0.1)',
                  border: '1px solid rgba(59,130,246,0.2)',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.82rem',
                  color: 'var(--accent-blue)',
                }}
              >
                {topic}
              </span>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: 16, fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'right' }}>
        Generated: {generation_time} • Mode: {mode}
      </div>
    </div>
  )
}
