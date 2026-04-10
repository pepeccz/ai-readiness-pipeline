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
            Diagnóstico estratégico de{' '}
            <span className="text-teal-500">Inteligencia Artificial</span>{' '}
            para tu empresa
          </h1>
          <p className="text-gray-500 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
            Este cuestionario analiza en profundidad tu negocio para generar un informe
            personalizado con recomendaciones concretas de herramientas, análisis de
            cumplimiento normativo (RGPD / AI Act) y un plan de acción con ROI estimado.
          </p>
          <p className="text-gray-400 text-sm mt-3 max-w-xl mx-auto">
            Cuanto más detalladas sean tus respuestas, más preciso y valioso será el informe.
            Tómate el tiempo que necesites — cada respuesta cuenta.
          </p>
          <div className="flex items-center justify-center gap-6 mt-5 text-sm text-gray-400">
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Informe profesional
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              100% confidencial
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Análisis con IA avanzada
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
