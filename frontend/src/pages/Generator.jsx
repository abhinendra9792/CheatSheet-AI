import { useState, useRef, useEffect } from 'react'
import PipelineProgress, { PIPELINE_STEPS, IMAGE_PIPELINE_STEPS } from '../components/PipelineProgress'
import ResultViewer from '../components/ResultViewer'

const COMBINED_STEPS = [
  { id: 2, name: 'Analyzing Uploaded Image', model: 'Nano Banana Pro' },
  { id: 1, name: 'Understanding Your Request', model: 'Gemini Pro' },
  { id: 3, name: 'Researching Trends & Style', model: 'Deep Research' },
  { id: 4, name: 'Building Optimized Prompt', model: 'Prompt Builder' },
  { id: 5, name: 'Generating Content', model: 'Gemini Pro' },
  { id: 6, name: 'Creating Visual Cheatsheet', model: 'Gemini Image Gen' },
]

export default function Generator() {
  const [prompt, setPrompt] = useState('')
  const [file, setFile] = useState(null)
  const [fileName, setFileName] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  // Determine which steps to show based on what user provided
  const hasImage = !!file
  const steps = hasImage ? COMBINED_STEPS : PIPELINE_STEPS

  // Simulate step progression during loading
  useEffect(() => {
    if (!loading) return
    let stepIndex = 0

    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        setCurrentStep(steps[stepIndex].id)
        stepIndex++
      }
    }, 8000)

    setCurrentStep(steps[0].id)
    return () => clearInterval(interval)
  }, [loading, steps])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!prompt.trim() && !file) return

    setLoading(true)
    setError('')
    setResult(null)
    setCurrentStep(0)

    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5 * 60 * 1000)

      const formData = new FormData()
      if (prompt.trim()) formData.append('prompt', prompt.trim())
      if (file) formData.append('image', file)

      const res = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })
      clearTimeout(timeout)

      if (!res.ok) {
        let detail = `Server error: ${res.status}`
        try { const err = await res.json(); detail = err.detail || detail } catch {}
        throw new Error(detail)
      }

      const data = await res.json()
      setResult(data)
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out (5 min). The API may be rate-limited. Try again in a few minutes.')
      } else {
        setError(err.message || 'Failed to generate cheatsheet')
      }
    } finally {
      setLoading(false)
      setCurrentStep(0)
    }
  }

  const handleFileDrop = (e) => {
    e.preventDefault()
    e.currentTarget.classList.remove('drag-over')
    const droppedFile = e.dataTransfer?.files?.[0]
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setFile(droppedFile)
      setFileName(droppedFile.name)
    }
  }

  const handleFileSelect = (e) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setFileName(selected.name)
    }
  }

  const removeFile = (e) => {
    e.stopPropagation()
    setFile(null)
    setFileName('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const canSubmit = !loading && (prompt.trim() || file)

  return (
    <main className="generator">
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: 8 }}>
            <span className="gradient-text">Generate Cheatsheet</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Type what you need, upload an image, or both — we'll handle the rest
          </p>
        </div>

        <div className="generator-layout">
          {/* ═══ Left: Unified Form ═══ */}
          <div className="generator-form">
            <form onSubmit={handleSubmit} className="form-section">
              {/* Text Input */}
              <div className="input-group">
                <label className="input-label">💬 What do you need?</label>
                <textarea
                  className="textarea"
                  placeholder="e.g. Generate a Docker cheatsheet with essential commands and best practices..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={loading}
                  rows={4}
                />
              </div>

              {/* Image Upload */}
              <div className="input-group">
                <label className="input-label">📸 Reference Image (optional)</label>
                <div
                  className={`upload-zone ${file ? 'has-file' : ''}`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('drag-over') }}
                  onDragLeave={(e) => e.currentTarget.classList.remove('drag-over')}
                  onDrop={handleFileDrop}
                  style={{ padding: file ? '24px' : '32px 24px' }}
                >
                  <div className="upload-icon" style={{ fontSize: file ? '1.5rem' : '2rem' }}>
                    {file ? '✅' : '📸'}
                  </div>
                  {file ? (
                    <div className="upload-text">
                      <strong>{fileName}</strong>
                      <br />
                      <span
                        onClick={removeFile}
                        style={{
                          color: 'var(--accent-rose)',
                          cursor: 'pointer',
                          fontSize: '0.82rem',
                          textDecoration: 'underline',
                        }}
                      >
                        Remove
                      </span>
                    </div>
                  ) : (
                    <div className="upload-text">
                      <strong>Click to upload</strong> or drag and drop
                      <br />
                      <span style={{ fontSize: '0.82rem' }}>
                        Upload an existing cheatsheet to improve it
                      </span>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                </div>
              </div>

              {/* What will happen indicator */}
              <div style={{
                padding: '10px 16px',
                background: 'var(--bg-glass)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.82rem',
                color: 'var(--text-muted)',
              }}>
                {prompt.trim() && file && '🔄 Text + Image → Full 6-step pipeline (Steps 2→1→3→4→5→6)'}
                {prompt.trim() && !file && '📝 Text only → 5-step pipeline (Steps 1→3→4→5→6)'}
                {!prompt.trim() && file && '📸 Image only → Analyze & regenerate (Steps 2→1→3→4→5→6)'}
                {!prompt.trim() && !file && '💡 Enter text and/or upload an image to get started'}
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                className="btn btn-primary btn-lg"
                disabled={!canSubmit}
                style={{ width: '100%' }}
              >
                {loading ? (
                  <>
                    <span className="spinner" />
                    Generating your cheatsheet...
                  </>
                ) : (
                  <>⚡ Generate Cheatsheet</>
                )}
              </button>
            </form>

            {/* Error */}
            {error && (
              <div className="card" style={{
                marginTop: 16,
                borderColor: 'var(--accent-rose)',
                background: 'rgba(244,63,94,0.08)',
              }}>
                <p style={{ color: 'var(--accent-rose)', fontSize: '0.9rem' }}>
                  ❌ {error}
                </p>
              </div>
            )}
          </div>

          {/* ═══ Right: Progress + Results ═══ */}
          <div>
            {loading && (
              <div className="card" style={{ animation: 'fadeInUp 0.4s ease' }}>
                <h3 style={{ marginBottom: 8, fontWeight: 700 }}>
                  🚀 Pipeline Running...
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 16 }}>
                  {hasImage
                    ? 'Steps 2 → 1 → 3 → 4 → 5 → 6'
                    : 'Steps 1 → 3 → 4 → 5 → 6'}
                </p>
                <PipelineProgress currentStep={currentStep} steps={steps} />
                <p style={{
                  marginTop: 16,
                  fontSize: '0.82rem',
                  color: 'var(--text-muted)',
                  textAlign: 'center',
                }}>
                  This may take 30-120 seconds depending on API response times
                </p>
              </div>
            )}

            {!loading && !result && !error && (
              <div className="card" style={{
                textAlign: 'center',
                padding: '60px 32px',
                opacity: 0.7,
              }}>
                <div style={{ fontSize: '3rem', marginBottom: 16 }}>📋</div>
                <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Your Cheatsheet</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  Enter a topic, upload an image, or both — and click Generate
                </p>
              </div>
            )}

            {result && <ResultViewer result={result} />}
          </div>
        </div>
      </div>
    </main>
  )
}
