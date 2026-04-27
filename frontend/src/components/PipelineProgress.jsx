export default function PipelineProgress({ currentStep, steps }) {
  return (
    <div className="pipeline-steps">
      {steps.map((step) => {
        let status = ''
        if (step.id < currentStep) status = 'completed'
        else if (step.id === currentStep) status = 'active'

        return (
          <div key={step.id} className={`step ${status}`}>
            <div className="step-number">
              {status === 'completed' ? '✓' : step.id}
            </div>
            <div className="step-info">
              <div className="step-name">{step.name}</div>
              <div className="step-model">{step.model}</div>
            </div>
            <div className="step-status">
              {status === 'completed' && '✅'}
              {status === 'active' && <span className="spinner" />}
              {status === '' && '⏳'}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export const PIPELINE_STEPS = [
  { id: 1, name: 'Understanding Your Request', model: 'Gemini Pro' },
  { id: 3, name: 'Researching Trends & Style', model: 'Deep Research' },
  { id: 4, name: 'Building Optimized Prompt', model: 'Prompt Builder' },
  { id: 5, name: 'Generating Content', model: 'Gemini Pro' },
  { id: 6, name: 'Creating Visual Cheatsheet', model: 'Gemini Image Gen' },
]

export const IMAGE_PIPELINE_STEPS = [
  { id: 2, name: 'Analyzing Uploaded Image', model: 'Nano Banana Pro' },
  { id: 1, name: 'Understanding Extracted Content', model: 'Gemini Pro' },
  { id: 3, name: 'Researching Trends & Style', model: 'Deep Research' },
  { id: 4, name: 'Building Optimized Prompt', model: 'Prompt Builder' },
  { id: 5, name: 'Generating Content', model: 'Gemini Pro' },
  { id: 6, name: 'Creating Visual Cheatsheet', model: 'Gemini Image Gen' },
]
