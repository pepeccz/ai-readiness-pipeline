/**
 * TRIAGEWizard — public TRIAGE form (session 0).
 *
 * Placeholder: renders schema-driven form via BlockRenderer.
 * Schema from GET /api/public/triage/schema
 * Submit to POST /api/public/triage/submit
 *
 * TODO (B10): wire schema fetch, BlockRenderer, and submission flow.
 */

export function TRIAGEWizard() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="max-w-xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-10 text-center">
        <div className="w-12 h-12 rounded-xl bg-teal-500 flex items-center justify-center mx-auto mb-6">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          Diagnóstico de IA para tu empresa
        </h1>
        <p className="text-gray-500 text-sm leading-relaxed mb-6">
          Completa este formulario para que nuestro equipo analice el potencial de
          la inteligencia artificial en tu negocio y te enviemos un diagnóstico personalizado.
        </p>
        <p className="text-xs text-teal-600 font-medium bg-teal-50 rounded-lg px-4 py-2">
          Formulario de pre-diagnóstico — disponible próximamente
        </p>
      </div>
    </div>
  )
}
