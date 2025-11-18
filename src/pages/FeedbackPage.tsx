import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageSquare, ArrowLeft } from 'lucide-react'
import { FeedbackCategory, FeedbackPayload } from '../types/feedback'

interface FeedbackFormState {
  name: string
  email: string
  category: FeedbackCategory
  rating: string
  message: string
  contactConsent: boolean
}

interface FieldErrors {
  name?: string
  email?: string
  category?: string
  rating?: string
  message?: string
  contactConsent?: string
}

const initialFormState: FeedbackFormState = {
  name: '',
  email: '',
  category: 'General Feedback',
  rating: '',
  message: '',
  contactConsent: false
}

const ratingOptions = [
  { value: '5', label: '5 - Very Satisfied' },
  { value: '4', label: '4 - Satisfied' },
  { value: '3', label: '3 - Neutral' },
  { value: '2', label: '2 - Dissatisfied' },
  { value: '1', label: '1 - Very Dissatisfied' }
]

const categoryOptions: FeedbackCategory[] = [
  'Bug',
  'Feature Request',
  'Usability Issue',
  'General Feedback',
  'Other'
]

/**
 * FeedbackPage - allows users to submit feedback that is persisted via the backend API
 */
export const FeedbackPage: React.FC = () => {
  const [formState, setFormState] = useState<FeedbackFormState>(initialFormState)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const apiBaseUrl = useMemo(
    () => (import.meta as any)?.env?.VITE_API_BASE_URL || 'http://localhost:8000',
    []
  )

  const handleInputChange = (
    field: keyof FeedbackFormState,
    value: string | boolean
  ) => {
    setFormState((prev) => ({
      ...prev,
      [field]: value
    }))
    // Clear error for the field being edited
    setErrors((prev) => ({
      ...prev,
      [field]: undefined
    }))
  }

  const validateForm = () => {
    const newErrors: FieldErrors = {}

    if (!formState.rating) {
      newErrors.rating = 'Please select a rating.'
    }

    if (!formState.message.trim()) {
      newErrors.message = 'Detailed feedback is required.'
    }

    if (formState.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formState.email)) {
      newErrors.email = 'Please enter a valid email address.'
    }

    if (formState.contactConsent && !formState.email) {
      newErrors.contactConsent = 'Email is required if you would like us to contact you.'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSuccessMessage(null)
    setErrorMessage(null)

    if (!validateForm()) {
      return
    }

    const payload: FeedbackPayload = {
      name: formState.name.trim() || undefined,
      email: formState.email.trim() || undefined,
      category: formState.category,
      rating: Number(formState.rating),
      message: formState.message.trim(),
      contactConsent: formState.contactConsent
    }

    try {
      setSubmitting(true)
      const response = await fetch(`${apiBaseUrl}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error('Failed to submit feedback')
      }

      setFormState(initialFormState)
      setSuccessMessage('Thank you! Your feedback has been submitted successfully.')
    } catch (error) {
      console.error(error)
      setErrorMessage('Something went wrong while submitting your feedback. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen py-12 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Dashboard
          </Link>
        </div>

        <div className="card">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <MessageSquare className="h-12 w-12 text-primary-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              We value your feedback
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Help us improve Invest-Ease by sharing your experience.
            </p>
          </div>

          {successMessage && (
            <div className="mb-6 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800 dark:border-green-900 dark:bg-green-900/30 dark:text-green-200">
              {successMessage}
            </div>
          )}

          {errorMessage && (
            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-900/30 dark:text-red-200">
              {errorMessage}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Full Name <span className="text-gray-400 text-xs">(optional)</span>
                </label>
                <input
                  type="text"
                  value={formState.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="input-field"
                  placeholder="Jane Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Email <span className="text-gray-400 text-xs">(optional)</span>
                </label>
                <input
                  type="email"
                  value={formState.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className={`input-field ${errors.email ? 'border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="you@example.com"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email}</p>
                )}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Feedback Category
                </label>
                <select
                  value={formState.category}
                  onChange={(e) => handleInputChange('category', e.target.value as FeedbackCategory)}
                  className="input-field"
                >
                  {categoryOptions.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Rating <span className="text-primary-600">*</span>
                </label>
                <select
                  value={formState.rating}
                  onChange={(e) => handleInputChange('rating', e.target.value)}
                  className={`input-field ${errors.rating ? 'border-red-500 focus:ring-red-500' : ''}`}
                  required
                >
                  <option value="">Select a rating</option>
                  {ratingOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                {errors.rating && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.rating}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Detailed Feedback <span className="text-primary-600">*</span>
              </label>
              <textarea
                value={formState.message}
                onChange={(e) => handleInputChange('message', e.target.value)}
                className={`input-field min-h-[140px] resize-y ${
                  errors.message ? 'border-red-500 focus:ring-red-500' : ''
                }`}
                placeholder="Tell us what worked well, what didn't, and how we can improve..."
              />
              {errors.message && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.message}</p>
              )}
            </div>

            <div className="flex items-start space-x-3">
              <input
                id="contact-consent"
                type="checkbox"
                checked={formState.contactConsent}
                onChange={(e) => handleInputChange('contactConsent', e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <div>
                <label
                  htmlFor="contact-consent"
                  className="text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  I'm happy to be contacted about this feedback.
                </label>
                {errors.contactConsent && (
                  <p className="text-sm text-red-600 dark:text-red-400">{errors.contactConsent}</p>
                )}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-4">
              <button
                type="submit"
                className="btn-primary w-full sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={submitting}
              >
                {submitting ? 'Submitting…' : 'Submit Feedback'}
              </button>
              <Link to="/" className="text-sm font-medium text-primary-600 hover:text-primary-700">
                Back to Dashboard
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

