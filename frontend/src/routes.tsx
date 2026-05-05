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
    // Public TRIAGE form (session 0)
    path: '/triage',
    element: <TRIAGEWizard />,
  },
  {
    // Consultant intake form (session 1) — protected by admin auth in IntakeApp itself
    path: '/intake/:leadId',
    element: <IntakePage />,
  },
  {
    // Public client DEEP form (session 2) — accessed via signed URL
    path: '/client/deep/:token',
    element: <DeepFormRoute />,
  },
  {
    // Public client report viewer — accessed via signed URL
    path: '/client/report/:token',
    element: <ReportViewerRoute />,
  },
  {
    path: '/admin',
    element: <AdminLayout />,
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'forgot-password', element: <ForgotPasswordPage /> },
      { path: 'reset-password', element: <ResetPasswordPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: 'leads', element: <LeadsListPage /> },
          { path: 'leads/:id', element: <LeadDetailPage /> },
        ],
      },
    ],
  },
])
