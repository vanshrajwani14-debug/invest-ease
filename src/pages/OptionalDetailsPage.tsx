import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BackButton } from '../components/BackButton'
import { OptionalInputField } from '../components/OptionalInputField'

const SINGLE_REPORT_OPTIONS = [
  { value: 'mutualfunds', label: 'Mutual Funds' },
  { value: 'stocks', label: 'Stocks' },
  { value: 'bonds', label: 'Government Bonds' },
  { value: 'gold', label: 'Gold' },
  { value: 'sip', label: 'SIP (Systematic Investment Plan)' }
]

type ReportPreference = {
  reportType: 'full' | 'single'
  investmentType: string
}

export const OptionalDetailsPage: React.FC = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    monthlyIncome: '',
    savings: '',
    timeHorizon: '',
    investmentExperience: '',
    financialGoals: '',
    monthlyExpenses: ''
  })
  const [reportPreference, setReportPreference] = useState<ReportPreference>({
    reportType: 'full',
    investmentType: ''
  })
  const [reportError, setReportError] = useState('')

  useEffect(() => {
    const storedPreference = localStorage.getItem('reportPreference')
    if (storedPreference) {
      try {
        const parsed = JSON.parse(storedPreference)
        setReportPreference({
          reportType: parsed.reportType === 'single' ? 'single' : 'full',
          investmentType: parsed.investmentType || ''
        })
      } catch (error) {
        // ignore parsing errors and keep defaults
      }
    }
  }, [])

  const handleInputChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleReportPreferenceChange = (key: keyof ReportPreference, value: string) => {
    setReportPreference(prev => ({
      ...prev,
      [key]: key === 'reportType' ? (value as 'full' | 'single') : value
    }))
    if (reportError) {
      setReportError('')
    }
  }

  const validateReportPreference = () => {
    if (reportPreference.reportType === 'single' && !reportPreference.investmentType) {
      setReportError('Please choose a category for the single-investment report.')
      return false
    }
    setReportError('')
    return true
  }

  const persistReportPreference = () => {
    localStorage.setItem(
      'reportPreference',
      JSON.stringify({
        reportType: reportPreference.reportType,
        investmentType: reportPreference.investmentType
      })
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateReportPreference()) {
      return
    }
    // Store optional data
    localStorage.setItem('optionalDetails', JSON.stringify(formData))
    persistReportPreference()
    navigate('/recommendation')
  }

  const handleSkip = () => {
    if (!validateReportPreference()) {
      return
    }
    persistReportPreference()
    navigate('/recommendation')
  }

  return (
    <div className="min-h-screen py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <BackButton to="/details" />
        </div>

        <div className="card">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Additional Details
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Help us create a more personalized recommendation (optional)
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <OptionalInputField
                label="Monthly Income"
                name="monthlyIncome"
                type="number"
                value={formData.monthlyIncome}
                onChange={handleInputChange}
                placeholder="Enter monthly income"
                prefix="₹"
              />

              <OptionalInputField
                label="Current Savings"
                name="savings"
                type="number"
                value={formData.savings}
                onChange={handleInputChange}
                placeholder="Enter current savings"
                prefix="₹"
              />
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <OptionalInputField
                label="Investment Time Horizon"
                name="timeHorizon"
                type="select"
                value={formData.timeHorizon}
                onChange={handleInputChange}
                options={['1-3 years', '3-5 years', '5-10 years', '10+ years']}
              />

              <OptionalInputField
                label="Investment Experience"
                name="investmentExperience"
                type="select"
                value={formData.investmentExperience}
                onChange={handleInputChange}
                options={['Beginner', 'Intermediate', 'Advanced']}
              />
            </div>

            <OptionalInputField
              label="Primary Financial Goal"
              name="financialGoals"
              type="select"
              value={formData.financialGoals}
              onChange={handleInputChange}
              options={[
                'Retirement Planning',
                'Wealth Creation',
                'Child Education',
                'Home Purchase',
                'Emergency Fund',
                'Tax Saving'
              ]}
            />

            <OptionalInputField
              label="Monthly Expenses"
              name="monthlyExpenses"
              type="number"
              value={formData.monthlyExpenses}
              onChange={handleInputChange}
              placeholder="Enter monthly expenses"
              prefix="₹"
            />

            <div className="border rounded-2xl p-4 sm:p-6 space-y-4">
              <div>
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Report Preference (optional)
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Choose between a full investment report or a single-category deep dive. Default is full.
                </p>
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  {
                    value: 'full',
                    title: 'Full Investment Report',
                    description: 'All categories with balanced insights (default)'
                  },
                  {
                    value: 'single',
                    title: 'Single-Investment Report',
                    description: 'Focus on one investment category'
                  }
                ].map(option => (
                  <label
                    key={option.value}
                    className={`cursor-pointer border rounded-xl p-4 transition ${
                      reportPreference.reportType === option.value
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      className="sr-only"
                      name="reportPreference"
                      value={option.value}
                      checked={reportPreference.reportType === option.value}
                      onChange={(e) => handleReportPreferenceChange('reportType', e.target.value)}
                    />
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">{option.title}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{option.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              {reportPreference.reportType === 'single' && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Select investment category
                  </label>
                  <select
                    value={reportPreference.investmentType}
                    onChange={(e) => handleReportPreferenceChange('investmentType', e.target.value)}
                    className="input-field"
                  >
                    <option value="">Choose a category</option>
                    {SINGLE_REPORT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {reportError && (
                    <p className="text-sm text-red-600">{reportError}</p>
                  )}
                </div>
              )}

              {reportPreference.reportType === 'full' && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  We will continue using the full investment report unless you choose otherwise.
                </p>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 pt-6">
              <button
                type="button"
                onClick={handleSkip}
                className="btn-secondary flex-1"
              >
                Skip & Continue
              </button>
              <button
                type="submit"
                className="btn-primary flex-1"
              >
                Get Recommendations
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
