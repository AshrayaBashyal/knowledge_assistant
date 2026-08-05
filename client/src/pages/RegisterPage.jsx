import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import Field from '../components/ui/Field'
import Button from '../components/ui/Button'
import Alert from '../components/ui/Alert'
import Spinner from '../components/ui/Spinner'
import { useAuth } from '../lib/AuthContext'
import { useToast } from '../lib/ToastContext'
import { getErrorMessage } from '../lib/errors'

export default function RegisterPage() {
  const { register } = useAuth()
  const { notify } = useToast()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register({ email, password, fullName })
      notify('Account created — sign in to continue.', { variant: 'success' })
      navigate('/login', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card tab="ledger">
      <h1 className="mb-5 font-display italic text-2xl text-ink">Create account</h1>

      {error && <Alert variant="error" className="mb-4">{error}</Alert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Field
          label="Full name (optional)"
          type="text"
          autoComplete="name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
        <Field
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Field
          label="Password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit" className="w-full justify-center" disabled={submitting}>
          {submitting ? <Spinner size={16} /> : 'Create account'}
        </Button>
      </form>

      <p className="mt-5 text-center text-sm text-ink-soft">
        Already have an account? <Link to="/login" className="text-ledger hover:underline">Sign in</Link>
      </p>
    </Card>
  )
}