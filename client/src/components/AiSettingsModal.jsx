import { useState, useEffect } from 'react'
import {
  X,
  Key,
  CheckCircle,
  WarningCircle,
  ArrowClockwise,
  ShieldCheck,
  Cpu,
  Trash,
  ArrowSquareOut,
} from '@phosphor-icons/react'
import {
  fetchAiSettings,
  updateAiSettings,
  resetAiSettings,
  validateApiKey,
} from '../services/aiSettingsService'

const GEMINI_MODELS = [
  { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite (Fastest & Free)' },
  { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash (Balanced)' },
  { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash (Standard)' },
  { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro (Deep Reasoning)' },
]

const GROQ_MODELS = [
  { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile (Recommended / High Intelligence)' },
  { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B Instant (Ultra-Low Latency)' },
  { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B (32k Context Window)' },
]

export default function AiSettingsModal({ isOpen, onClose }) {
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [provider, setProvider] = useState('default')
  const [preferredModel, setPreferredModel] = useState('')
  const [geminiKey, setGeminiKey] = useState('')
  const [groqKey, setGroqKey] = useState('')
  const [maskedGemini, setMaskedGemini] = useState('')
  const [maskedGroq, setMaskedGroq] = useState('')
  const [hasGeminiKey, setHasGeminiKey] = useState(false)
  const [hasGroqKey, setHasGroqKey] = useState(false)

  const [testResult, setTestResult] = useState(null)
  const [feedback, setFeedback] = useState(null)

  useEffect(() => {
    if (isOpen) {
      loadSettings()
    } else {
      setTestResult(null)
      setFeedback(null)
    }
  }, [isOpen])

  async function loadSettings() {
    setLoading(true)
    try {
      const data = await fetchAiSettings()
      setProvider(data.provider || 'default')
      setPreferredModel(data.preferred_model || '')
      setMaskedGemini(data.masked_gemini_key || '')
      setMaskedGroq(data.masked_groq_key || '')
      setHasGeminiKey(data.has_gemini_key || false)
      setHasGroqKey(data.has_groq_key || false)
      setGeminiKey('')
      setGroqKey('')
    } catch {
      setFeedback({ type: 'error', message: 'Failed to load AI settings' })
    } finally {
      setLoading(false)
    }
  }

  async function handleTestConnection() {
    setTestResult(null)
    setTesting(true)

    const keyToTest = provider === 'gemini' ? (geminiKey.trim() || maskedGemini) : (groqKey.trim() || maskedGroq)
    if (!keyToTest || (provider === 'gemini' && !hasGeminiKey && !geminiKey.trim()) || (provider === 'groq' && !hasGroqKey && !groqKey.trim())) {
      setTestResult({ valid: false, error: 'Please enter an API key to test.' })
      setTesting(false)
      return
    }

    try {
      const res = await validateApiKey({
        provider,
        api_key: provider === 'gemini' ? geminiKey.trim() : groqKey.trim(),
        model: preferredModel,
      })
      setTestResult({ valid: true, message: res.message || 'Key verified successfully!' })
    } catch (err) {
      setTestResult({ valid: false, error: err.message || 'Validation failed. Please verify your key.' })
    } finally {
      setTesting(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    setFeedback(null)
    try {
      const payload = {
        provider,
        preferred_model: preferredModel,
      }
      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim()
      if (groqKey.trim()) payload.groq_api_key = groqKey.trim()

      const updated = await updateAiSettings(payload)
      setMaskedGemini(updated.masked_gemini_key || '')
      setMaskedGroq(updated.masked_groq_key || '')
      setHasGeminiKey(updated.has_gemini_key || false)
      setHasGroqKey(updated.has_groq_key || false)
      setGeminiKey('')
      setGroqKey('')
      setFeedback({ type: 'success', message: 'AI model & API settings saved successfully!' })
      setTimeout(() => {
        onClose()
      }, 1200)
    } catch (err) {
      setFeedback({ type: 'error', message: err.message || 'Failed to save settings.' })
    } finally {
      setSaving(false)
    }
  }

  async function handleReset() {
    if (!window.confirm('Reset back to system default keys and clear your custom keys?')) return
    setSaving(true)
    try {
      await resetAiSettings()
      await loadSettings()
      setFeedback({ type: 'success', message: 'Reverted to system default provider.' })
    } catch {
      setFeedback({ type: 'error', message: 'Failed to reset settings.' })
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 backdrop-blur-xs">
      <div className="relative w-full max-w-lg rounded-tab bg-paper border border-mist shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-mist px-6 py-4 bg-paper-dim">
          <div className="flex items-center gap-2.5">
            <Cpu size={22} className="text-brass" />
            <div>
              <h2 className="font-display italic text-xl text-ink leading-tight">AI Model & API Keys</h2>
              <p className="font-mono text-xs text-ink-soft">Bring Your Own Key (BYOK) or use system default</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-tab p-1.5 text-ink-soft hover:text-ink hover:bg-mist/40 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-ink-soft font-mono text-xs gap-2">
              <ArrowClockwise size={16} className="animate-spin" />
              Loading configuration…
            </div>
          ) : (
            <>
              {feedback && (
                <div
                  className={`flex items-start gap-2.5 rounded-tab p-3 text-xs font-mono ${
                    feedback.type === 'success'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : 'bg-rose-50 text-rose-800 border border-rose-200'
                  }`}
                >
                  {feedback.type === 'success' ? <CheckCircle size={16} /> : <WarningCircle size={16} />}
                  <span>{feedback.message}</span>
                </div>
              )}

              {/* Provider Selection */}
              <div>
                <label className="block font-mono text-xs font-semibold text-ink uppercase tracking-wider mb-2">
                  Active Provider
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setProvider('default')
                      setPreferredModel('')
                      setTestResult(null)
                    }}
                    className={`flex flex-col items-center justify-center p-3 rounded-tab border text-xs font-medium transition-all ${
                      provider === 'default'
                        ? 'border-brass bg-brass/10 text-ink shadow-xs'
                        : 'border-mist bg-paper hover:bg-paper-dim text-ink-soft'
                    }`}
                  >
                    <ShieldCheck size={20} className={provider === 'default' ? 'text-brass' : ''} />
                    <span className="mt-1.5">System Free</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setProvider('gemini')
                      setPreferredModel('gemini-2.5-flash-lite')
                      setTestResult(null)
                    }}
                    className={`flex flex-col items-center justify-center p-3 rounded-tab border text-xs font-medium transition-all ${
                      provider === 'gemini'
                        ? 'border-brass bg-brass/10 text-ink shadow-xs'
                        : 'border-mist bg-paper hover:bg-paper-dim text-ink-soft'
                    }`}
                  >
                    <Key size={20} className={provider === 'gemini' ? 'text-brass' : ''} />
                    <span className="mt-1.5">Google Gemini</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setProvider('groq')
                      setPreferredModel('llama-3.3-70b-versatile')
                      setTestResult(null)
                    }}
                    className={`flex flex-col items-center justify-center p-3 rounded-tab border text-xs font-medium transition-all ${
                      provider === 'groq'
                        ? 'border-brass bg-brass/10 text-ink shadow-xs'
                        : 'border-mist bg-paper hover:bg-paper-dim text-ink-soft'
                    }`}
                  >
                    <Cpu size={20} className={provider === 'groq' ? 'text-brass' : ''} />
                    <span className="mt-1.5">Groq (Ultra-Fast)</span>
                  </button>
                </div>
              </div>

              {/* Provider details */}
              {provider === 'default' && (
                <div className="rounded-tab border border-mist bg-paper-dim p-4 text-xs font-mono text-ink-soft space-y-2">
                  <p className="text-ink font-medium">✓ Using System Free Key</p>
                  <p>
                    Requests use the server-provided rotating Gemini API keys with 0 setup required on your part.
                  </p>
                </div>
              )}

              {provider === 'gemini' && (
                <div className="space-y-4 rounded-tab border border-mist p-4 bg-paper-dim/50">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold text-ink">Gemini Configuration</span>
                    <a
                      href="https://aistudio.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 font-mono text-[11px] text-brass hover:underline"
                    >
                      Get free key <ArrowSquareOut size={12} />
                    </a>
                  </div>

                  <div>
                    <label className="block font-mono text-[11px] text-ink-soft mb-1">Model Selection</label>
                    <select
                      value={preferredModel || 'gemini-2.5-flash-lite'}
                      onChange={(e) => setPreferredModel(e.target.value)}
                      className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-xs text-ink focus:border-brass focus:outline-hidden"
                    >
                      {GEMINI_MODELS.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-mono text-[11px] text-ink-soft mb-1">
                      Gemini API Key {hasGeminiKey && <span className="text-emerald-700">(Active: {maskedGemini})</span>}
                    </label>
                    <input
                      type="password"
                      placeholder={hasGeminiKey ? 'Enter new key to replace' : 'AIzaSy...'}
                      value={geminiKey}
                      onChange={(e) => setGeminiKey(e.target.value)}
                      className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-xs font-mono text-ink placeholder:text-ink-soft/50 focus:border-brass focus:outline-hidden"
                    />
                  </div>
                </div>
              )}

              {provider === 'groq' && (
                <div className="space-y-4 rounded-tab border border-mist p-4 bg-paper-dim/50">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold text-ink">Groq Configuration</span>
                    <a
                      href="https://console.groq.com/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 font-mono text-[11px] text-brass hover:underline"
                    >
                      Get free key <ArrowSquareOut size={12} />
                    </a>
                  </div>

                  <div>
                    <label className="block font-mono text-[11px] text-ink-soft mb-1">Model Selection</label>
                    <select
                      value={preferredModel || 'llama-3.3-70b-versatile'}
                      onChange={(e) => setPreferredModel(e.target.value)}
                      className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-xs text-ink focus:border-brass focus:outline-hidden"
                    >
                      {GROQ_MODELS.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-mono text-[11px] text-ink-soft mb-1">
                      Groq API Key {hasGroqKey && <span className="text-emerald-700">(Active: {maskedGroq})</span>}
                    </label>
                    <input
                      type="password"
                      placeholder={hasGroqKey ? 'Enter new key to replace' : 'gsk_...'}
                      value={groqKey}
                      onChange={(e) => setGroqKey(e.target.value)}
                      className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-xs font-mono text-ink placeholder:text-ink-soft/50 focus:border-brass focus:outline-hidden"
                    />
                  </div>
                </div>
              )}

              {/* Test Key feedback */}
              {testResult && (
                <div
                  className={`rounded-tab p-3 text-xs font-mono border ${
                    testResult.valid
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : 'bg-rose-50 text-rose-800 border-rose-200'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {testResult.valid ? <CheckCircle size={16} /> : <WarningCircle size={16} />}
                    <div>
                      <p className="font-semibold">{testResult.valid ? 'Verified' : 'Validation Error'}</p>
                      <p className="mt-0.5">{testResult.valid ? testResult.message : testResult.error}</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-mist px-6 py-4 bg-paper-dim flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {(hasGeminiKey || hasGroqKey || provider !== 'default') && (
              <button
                type="button"
                onClick={handleReset}
                disabled={saving || loading}
                className="flex items-center gap-1.5 rounded-tab px-3 py-1.5 font-mono text-xs text-crimson hover:bg-crimson/10 transition-colors"
                title="Reset to default"
              >
                <Trash size={14} />
                <span>Reset</span>
              </button>
            )}

            {provider !== 'default' && (
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testing || saving || loading}
                className="flex items-center gap-1.5 rounded-tab border border-mist bg-paper px-3 py-1.5 font-mono text-xs text-ink hover:bg-paper-dim transition-colors"
              >
                {testing ? <ArrowClockwise size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
                <span>{testing ? 'Testing…' : 'Test Key'}</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-tab px-3.5 py-1.5 font-mono text-xs text-ink-soft hover:text-ink transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || loading}
              className="flex items-center gap-1.5 rounded-tab bg-ledger px-4 py-1.5 font-mono text-xs font-medium text-paper hover:bg-ledger-dim transition-colors"
            >
              {saving ? <ArrowClockwise size={14} className="animate-spin" /> : null}
              <span>{saving ? 'Saving…' : 'Save Settings'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
