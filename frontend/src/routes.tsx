import { createBrowserRouter } from 'react-router-dom'
import App from './App'
import { AdminLayout } from './admin/AdminLayout'
import { ProtectedRoute } from './admin/ProtectedRoute'
import { LoginPage } from './admin/pages/LoginPage'
import { ForgotPasswordPage } from './admin/pages/ForgotPasswordPage'
import { ResetPasswordPage } from './admin/pages/ResetPasswordPage'
import { AssessmentListPage } from './admin/pages/AssessmentListPage'
import { AssessmentEditorPage } from './admin/pages/AssessmentEditorPage'
import { NewAssessmentPage } from './admin/pages/NewAssessmentPage'

export const router = createBrowserRouter([
  {
    // Public wizard — completely unchanged
    path: '/',
    element: <App />,
  },
  {
    path: '/admin',
    element: <AdminLayout />,
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'forgot-password', element: <ForgotPasswordPage /> },
      { path: 'reset-password', element: <ResetPasswordPage /> },
      {
        // ProtectedRoute wraps all authenticated admin pages
        element: <ProtectedRoute />,
        children: [
          { path: 'assessments', element: <AssessmentListPage /> },
          // IMPORTANT: 'new' must come BEFORE ':id' so the router matches it first
          { path: 'assessments/new', element: <NewAssessmentPage /> },
          { path: 'assessments/:id', element: <AssessmentEditorPage /> },
        ],
      },
    ],
  },
])
