import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { resetPassword } from '../api/auth'

// Mirror backend password policy: min 12 chars, at least 1 letter + 1 digit
const PASSWORD_REGEX = /^(?=.*[A-Za-z])(?=.*\d).{12,}$/

function validatePassword(pw: string): string | null {
  if (!PASSWORD_REGEX.test(pw)) {
    return 'La contraseña debe tener al menos 12 caracteres, una letra y un número.'
  }
  return null
}

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const token = searchParams.get('token')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Redirect immediately if no token in URL
  useEffect(() => {
    if (!token) {
      navigate('/admin/login', { replace: true })
    }
  }, [token, navigate])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    const validationError = validatePassword(newPassword)
    if (validationError) {
      setError(validationError)
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setSubmitting(true)

    try {
      await resetPassword(token!, newPassword)
      setSuccess(true)
      // Navigate to login after 2s so the user can read the success message
      setTimeout(() => {
        navigate('/admin/login', { replace: true })
      }, 2000)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === 'invalid_token' || err.status === 400) {
          setError('El enlace expiró o ya fue usado. Pedí uno nuevo.')
        } else if (err.status === 429) {
          setError('Demasiados intentos. Probá más tarde.')
        } else {
          setError('Ocurrió un error. Intentá de nuevo.')
        }
      } else {
        setError('No se pudo conectar al servidor.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (!token) {
    return null // Redirecting via useEffect
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
          <h1 className="text-lg font-semibold text-gray-900 mb-1">Nueva contraseña</h1>
          <p className="text-sm text-gray-500 mb-6">
            Elegí una contraseña segura (mínimo 12 caracteres, una letra y un número).
          </p>

          {success ? (
            <div className="flex flex-col gap-3">
              <div className="px-3 py-3 bg-teal-50 border border-teal-200 rounded-lg">
                <p className="text-sm text-teal-700">
                  Contraseña actualizada. Redirigiendo al inicio de sesión...
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="new-password" className="text-sm font-medium text-gray-700">
                  Nueva contraseña
                </label>
                <input
                  id="new-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  disabled={submitting}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors placeholder:text-gray-400"
                  placeholder="••••••••••••"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="confirm-password" className="text-sm font-medium text-gray-700">
                  Confirmá la contraseña
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  disabled={submitting}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors placeholder:text-gray-400"
                  placeholder="••••••••••••"
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
                {submitting ? 'Guardando...' : 'Guardar contraseña'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
