interface ProgressBarProps {
  currentStep: number
  totalSteps: number
  sectionTitle: string
}

export function ProgressBar({ currentStep, totalSteps, sectionTitle }: ProgressBarProps) {
  const percentage = Math.round((currentStep / totalSteps) * 100)

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-teal-700">
          Paso {currentStep} de {totalSteps}
        </span>
        <span className="text-sm text-gray-500">{percentage}% completado</span>
      </div>
      <p className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">{sectionTitle}</p>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-teal-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
