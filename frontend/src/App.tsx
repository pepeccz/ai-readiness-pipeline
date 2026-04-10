import { AssessmentWizard } from './components/wizard/AssessmentWizard'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-lg font-bold text-gray-800">Zanovix</span>
          </div>
          <div className="h-5 w-px bg-gray-200" />
          <span className="text-sm text-gray-500 font-medium">AI Readiness Assessment</span>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        {/* Hero intro */}
        <div className="text-center mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3 leading-tight">
            ¿Está tu empresa lista para la{' '}
            <span className="text-teal-500">Inteligencia Artificial</span>?
          </h1>
          <p className="text-gray-500 text-base sm:text-lg max-w-xl mx-auto">
            Completa este formulario en 10–15 minutos y recibirás un informe personalizado
            con las oportunidades de IA más relevantes para tu negocio.
          </p>
          <div className="flex items-center justify-center gap-6 mt-5 text-sm text-gray-400">
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              10–15 minutos
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              100% confidencial
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Informe en PDF
            </span>
          </div>
        </div>

        {/* Wizard */}
        <AssessmentWizard />

        {/* Footer */}
        <footer className="text-center mt-10 text-xs text-gray-400">
          <p>
            Tu información está protegida bajo el RGPD. Zanovix no comparte tus datos con terceros.
          </p>
          <p className="mt-1">
            © {new Date().getFullYear()} Zanovix · Todos los derechos reservados
          </p>
        </footer>
      </main>
    </div>
  )
}

export default App
