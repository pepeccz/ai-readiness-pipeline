import { fetchJson } from './client'

export interface AdminUser {
  id: string
  email: string
  last_login_at: string | null
}

export const login = (email: string, password: string) =>
  fetchJson<{ user: { id: string; email: string } }>('/admin/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })

export const logout = () =>
  fetchJson<void>('/admin/auth/logout', { method: 'POST' })

export const me = () =>
  fetchJson<AdminUser>('/admin/auth/me')

export const forgotPassword = (email: string) =>
  fetchJson<{ detail: string }>('/admin/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })

export const resetPassword = (token: string, new_password: string) =>
  fetchJson<{ detail: string }>('/admin/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password }),
  })
