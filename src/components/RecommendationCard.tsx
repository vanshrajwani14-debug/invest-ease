import React from 'react'

type RecommendationCardProps = {
  name: string
  category: string
  score?: number | string | null
  explanation?: string
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  name,
  category,
  score,
  explanation
}) => {
  const hasScore = score !== undefined && score !== null && score !== ''
  const displayScore =
    typeof score === 'number'
      ? score.toFixed(1)
      : typeof score === 'string'
      ? score
      : null

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary-600">
            {category}
          </p>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {name}
          </h3>
        </div>
        {hasScore && displayScore && (
          <span className="rounded-full bg-primary-50 px-3 py-1 text-sm font-semibold text-primary-700 dark:bg-primary-900/40 dark:text-primary-200">
            Score: {displayScore}
          </span>
        )}
      </div>
      {explanation && (
        <p className="mt-3 text-sm text-gray-600 dark:text-gray-300">{explanation}</p>
      )}
    </div>
  )
}

