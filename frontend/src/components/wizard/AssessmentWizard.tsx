import { useState } from 'react'
import { useFormState } from '../../hooks/useFormState'
import { useVisibleSections } from '../../hooks/useVisibleSections'
import { useSubmission } from '../../hooks/useSubmission'
import { validateSection } from '../../utils/validators'
import { mapFormToPayload } from '../../utils/formMapper'
import { ProgressBar } from './ProgressBar'
import { NavigationButtons } from './NavigationButtons'
import { SubmissionStatus } from './SubmissionStatus'
import { Section1Empresa } from '../sections/Section1Empresa'
import { Section2Stack } from '../sections/Section2Stack'
import { Section3AtencionCliente } from '../sections/Section3AtencionCliente'
import { Section4Marketing } from '../sections/Section4Marketing'
import { Section5Operaciones } from '../sections/Section5Operaciones'
import { Section6GestionFinanzas } from '../sections/Section6GestionFinanzas'
import { Section7RRHH } from '../sections/Section7RRHH'
import { Section8Compliance } from '../sections/Section8Compliance'
import { Section9Presupuesto } from '../sections/Section9Presupuesto'
import type { ValidationErrors } from '../../utils/validators'
import type { FormState } from '../../types/form'

const SECTION_TITLES: Record<number, { title: string; description: string }> = {
  1: {
    title: 'Sobre tu empresa',
    description: 'Necesitamos entender tu negocio para adaptar las recomendaciones a tu realidad.',
  },
  2: {
    title: 'Tu entorno tecnológico',
    description: 'Qué herramientas usáis hoy — tanto de IA como de gestión. Esto determina qué integraciones son viables.',
  },
  3: {
    title: 'Cómo gestionáis la atención al cliente',
    description: 'Entender tu día a día con los clientes nos permite detectar dónde la automatización puede tener mayor impacto.',
  },
  4: {
    title: 'Marketing y captación de clientes',
    description: 'Cómo generáis contenido y atraéis clientes hoy. La IA puede transformar estos procesos — pero necesitamos saber de dónde partís.',
  },
  5: {
    title: 'Tus procesos operativos',
    description: 'Esta es la sección más importante del análisis. Describe con el mayor detalle posible los procesos que más tiempo y recursos consumen.',
  },
  6: {
    title: 'Gestión financiera y administrativa',
    description: 'La automatización de tareas administrativas es una de las áreas con ROI más inmediato para PYMEs.',
  },
  7: {
    title: 'Gestión de personas',
    description: 'Si vuestro equipo está creciendo, hay herramientas que pueden ahorrar horas de gestión administrativa.',
  },
  8: {
    title: 'Protección de datos y cumplimiento',
    description: 'Evaluamos tu situación frente al RGPD y el AI Act para identificar riesgos y recomendarte las acciones prioritarias.',
  },
  9: {
    title: 'Inversión y próximos pasos',
    description: 'Con esta información cerramos el análisis y generamos tu informe personalizado.',
  },
}

function SectionContent({
  sectionNumber,
  state,
  onChange,
  errors,
}: {
  sectionNumber: number
  state: FormState
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors: ValidationErrors
}) {
  switch (sectionNumber) {
    case 1: return <Section1Empresa state={state} onChange={onChange} errors={errors} />
    case 2: return <Section2Stack state={state} onChange={onChange} errors={errors} />
    case 3: return <Section3AtencionCliente state={state} onChange={onChange} errors={errors} />
    case 4: return <Section4Marketing state={state} onChange={onChange} errors={errors} />
    case 5: return <Section5Operaciones state={state} onChange={onChange} errors={errors} />
    case 6: return <Section6GestionFinanzas state={state} onChange={onChange} errors={errors} />
    case 7: return <Section7RRHH state={state} onChange={onChange} errors={errors} />
    case 8: return <Section8Compliance state={state} onChange={onChange} errors={errors} />
    case 9: return <Section9Presupuesto state={state} onChange={onChange} errors={errors} />
    default: return null
  }
}

export function AssessmentWizard() {
  const { state, updateField } = useFormState()
  const visibleSections = useVisibleSections(state.employee_range)
  const { submissionState, errorMessage, submit, downloadReport, reset } = useSubmission()
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [animating, setAnimating] = useState(false)

  const currentSection = visibleSections[currentStepIndex]
  const isFirst = currentStepIndex === 0
  const isLast = currentStepIndex === visibleSections.length - 1
  const isProcessing = ['submitting', 'polling', 'ready', 'downloading', 'error'].includes(submissionState)

  const sectionMeta = SECTION_TITLES[currentSection]

  function navigateToStep(targetIndex: number) {
    setAnimating(true)
    setTimeout(() => {
      setCurrentStepIndex(targetIndex)
      setErrors({})
      setAnimating(false)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }, 200)
  }

  function handleNext() {
    const sectionErrors = validateSection(currentSection, state)

    if (sectionErrors) {
      setErrors(sectionErrors)
      // Scroll to first error
      setTimeout(() => {
        const firstErrorEl = document.querySelector('[data-error]')
        firstErrorEl?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 50)
      return
    }

    if (isLast) {
      handleSubmit()
      return
    }

    navigateToStep(currentStepIndex + 1)
  }

  function handlePrevious() {
    if (!isFirst) {
      navigateToStep(currentStepIndex - 1)
    }
  }

  async function handleSubmit() {
    const payload = mapFormToPayload(state)
    await submit(payload)
  }

  if (isProcessing) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-10 min-h-[400px]">
        <SubmissionStatus
          state={submissionState}
          error={errorMessage}
          onDownload={downloadReport}
          onRetry={reset}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-6 py-5 sm:px-8">
        <ProgressBar
          currentStep={currentStepIndex + 1}
          totalSteps={visibleSections.length}
          sectionTitle={sectionMeta.title}
        />
      </div>

      <div
        className={`bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8 transition-opacity duration-200 ${
          animating ? 'opacity-0' : 'opacity-100'
        }`}
      >
        <div className="mb-6">
          <h2 className="text-xl font-bold text-teal-600 mb-1">{sectionMeta.title}</h2>
          <p className="text-sm text-gray-500">{sectionMeta.description}</p>
        </div>

        <SectionContent
          sectionNumber={currentSection}
          state={state}
          onChange={updateField}
          errors={errors}
        />

        <NavigationButtons
          onPrevious={handlePrevious}
          onNext={handleNext}
          isFirst={isFirst}
          isLast={isLast}
        />
      </div>
    </div>
  )
}
