/**
 * BucketBadge — Color-coded badge for triage_bucket values.
 *
 * Colors per spec REQ-2.3:
 *   auto_accept  → green
 *   review       → yellow
 *   cold_warm    → blue
 *   cold_cool    → gray
 *   reject_soft  → red
 */

import type { LeadBucket } from '../../api/leads'

const BUCKET_LABELS: Record<LeadBucket, string> = {
  auto_accept: 'Auto-aceptado',
  review: 'Revisión',
  cold_warm: 'Frío-cálido',
  cold_cool: 'Frío-frío',
  reject_soft: 'Rechazado',
}

const BUCKET_CLASSES: Record<LeadBucket, string> = {
  auto_accept: 'bg-green-100 text-green-700 border-green-200',
  review: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  cold_warm: 'bg-blue-100 text-blue-700 border-blue-200',
  cold_cool: 'bg-gray-100 text-gray-600 border-gray-200',
  reject_soft: 'bg-red-100 text-red-700 border-red-200',
}

interface BucketBadgeProps {
  bucket: string
}

export function BucketBadge({ bucket }: BucketBadgeProps) {
  const b = bucket as LeadBucket
  const label = BUCKET_LABELS[b] ?? bucket
  const cls = BUCKET_CLASSES[b] ?? 'bg-gray-100 text-gray-600 border-gray-200'

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {label}
    </span>
  )
}
