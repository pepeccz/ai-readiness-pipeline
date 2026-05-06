import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import { forgotPassword } from '../api/auth'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      await forgotPassword(email)
      setSent(true)
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setError('Demasiados intentos. Probá en una hora.')
      } else {
        // Even on unexpected errors, show the generic success message
        // to avoid user enumeration via error differentiation
        setSent(true)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <img src="/zanovix-logo.png" alt="Zanovix Admin" className="h-10 w-auto" />
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h1 className="text-lg font-semibold text-gray-900 mb-1">Recuperar contraseña</h1>
          <p className="text-sm text-gray-500 mb-6">
            Ingresá tu email y te enviaremos un enlace para crear una nueva contraseña.
          </p>

          {sent ? (
            <div className="flex flex-col gap-4">
              <div className="px-3 py-3 bg-teal-50 border border-teal-200 rounded-lg">
                <p className="text-sm text-teal-700">
                  Si el email existe, recibirás un enlace en breve.
                </p>
              </div>
              <Link
                to="/admin/login"
                className="text-sm text-center text-teal-600 hover:text-teal-700 hover:underline"
              >
                Volver al inicio de sesión
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="email" className="text-sm font-medium text-gray-700">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  disabled={submitting}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors placeholder:text-gray-400"
                  placeholder="admin@zanovix.com"
                />
              </div>

              {error && (
                <div className="px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 px-4 bg-teal-500 text-white text-sm font-medium rounded-lg hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? 'Enviando...' : 'Enviar enlace'}
              </button>

              <Link
                to="/admin/login"
                className="text-sm text-center text-gray-500 hover:text-gray-700 hover:underline"
              >
                Volver al inicio de sesión
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
