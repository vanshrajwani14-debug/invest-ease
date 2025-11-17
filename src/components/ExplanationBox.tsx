import React from 'react'

type ExplanationBoxProps = {
  title?: string
  text: string
}

export const ExplanationBox: React.FC<ExplanationBoxProps> = ({ title = 'Why these picks', text }) => {
  return (
    <div className="rounded-2xl border border-dashed border-primary-200 bg-primary-50/60 p-4 dark:border-primary-800 dark:bg-primary-950/40">
      <h4 className="text-sm font-semibold uppercase tracking-wide text-primary-700 dark:text-primary-200">
        {title}
      </h4>
      <p className="mt-2 text-sm text-primary-900 dark:text-primary-100">{text}</p>
    </div>
  )
}

