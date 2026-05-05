import { createBrowserRouter, Navigate, useParams } from 'react-router-dom'
import { AdminLayout } from './admin/AdminLayout'
import { ProtectedRoute } from './admin/ProtectedRoute'
import { LoginPage } from './admin/pages/LoginPage'
import { ForgotPasswordPage } from './admin/pages/ForgotPasswordPage'
import { ResetPasswordPage } from './admin/pages/ResetPasswordPage'
import { LeadsListPage } from './admin/pages/LeadsListPage'
import { LeadDetailPage } from './admin/pages/LeadDetailPage'
import { TRIAGEWizard } from './triage/TRIAGEWizard'
import { IntakeApp } from './intake/IntakeApp'
import { DeepFormPage } from './client-session2/DeepFormPage'
import { ReportViewerPage } from './client-session2/ReportViewerPage'

// Route wrapper: extracts :leadId param and passes to IntakeApp
function IntakePage() {
  const { leadId } = useParams<{ leadId: string }>()
  if (!leadId) return <Navigate to="/admin/leads" replace />
  return <IntakeApp leadId={leadId} />
}

// Route wrapper: extracts :token param and passes to DeepFormPage
function DeepFormRoute() {
  const { token } = useParams<{ token: string }>()
  if (!token) return <Navigate to="/triage" replace />
  return <DeepFormPage token={token} />
}

// Route wrapper: extracts :token param and passes to ReportViewerPage
function ReportViewerRoute() {
  const { token } = useParams<{ token: string }>()
  if (!token) return <Navigate to="/triage" replace />
  return <ReportViewerPage token={token} />
}

export const router = createBrowserRouter([
  {
    // Root → redirect to triage
    path: '/',
    element: <Navigate to="/triage" replace />,
  },
  {
    // Public TRIAGE wizard — NO QueryClient, NO AuthProvider (ADR-10 / REQ-13)
    path: '/triage',
    element: <TRIAGEWizard />,
  },

  /**
   * ADR-10 / REQ-13: Single AdminLayout parent for ALL authenticated routes.
   * This means /admin/*, /intake/:leadId/*, and /login share ONE QueryClientProvider
   * and ONE AuthProvider instance — so TanStack Query cache invalidations from
   * the admin tree are immediately visible to the intake tree and vice-versa.
   *
   * Public triage wizard (/triage) is intentionally outside this tree.
   */
  {
    element: <AdminLayout />,
    children: [
      // Auth pages (public within the authenticated layout — no ProtectedRoute guard)
      { path: '/login', element: <LoginPage /> },
      { path: '/admin/login', element: <LoginPage /> },
      { path: '/admin/forgot-password', element: <ForgotPasswordPage /> },
      { path: '/admin/reset-password', element: <ResetPasswordPage /> },

      // Protected admin routes
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/admin/leads', element: <LeadsListPage /> },
          { path: '/admin/leads/:id', element: <LeadDetailPage /> },

          // Intake (consultant session 1) — same auth context as /admin
          { path: '/intake/:leadId', element: <IntakePage /> },
        ],
      },
    ],
  },

  {
    // Public client DEEP form (session 2) — accessed via signed URL, no auth
    path: '/client/deep/:token',
    element: <DeepFormRoute />,
  },
  {
    // Public client report viewer — accessed via signed URL, no auth
    path: '/client/report/:token',
    element: <ReportViewerRoute />,
  },
])
