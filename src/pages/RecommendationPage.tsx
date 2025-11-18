import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, BarChart3 } from 'lucide-react'
import { BackButton } from '../components/BackButton'
import { SummaryCard } from '../components/SummaryCard'
import { AllocationDonutChart } from '../components/AllocationDonutChart'
import { SIPLineGraph } from '../components/SIPLineGraph'
import { RecommendationCard } from '../components/RecommendationCard'
import { ExplanationBox } from '../components/ExplanationBox'

type ReportPreference = {
  reportType: 'full' | 'single'
  investmentType?: string
}

const SINGLE_CATEGORY_LABELS: Record<string, string> = {
  mutualfunds: 'Mutual Funds',
  stocks: 'Stocks',
  bonds: 'Government Bonds',
  gold: 'Gold',
  sip: 'Systematic Investment Plan'
}

export const RecommendationPage: React.FC = () => {
  const navigate = useNavigate()
  const [userDetails, setUserDetails] = useState<any>(null)
  const [recommendationResults, setRecommendationResults] = useState<any>(null)
  const [recommendationLoading, setRecommendationLoading] = useState(false)
  const [recommendationError, setRecommendationError] = useState<string | null>(null)
  const [reportPreference, setReportPreference] = useState<ReportPreference>({
    reportType: 'full',
    investmentType: ''
  })
  const [preferenceLoaded, setPreferenceLoaded] = useState(false)
  const [reportMode, setReportMode] = useState<'full' | 'single'>('full')
  const [singleReportData, setSingleReportData] = useState<any>(null)

  const apiBaseUrl =
    (import.meta as any)?.env?.VITE_API_BASE_URL || 'http://localhost:8000'

  useEffect(() => {
    const mandatory = localStorage.getItem('mandatoryDetails')
    const optional = localStorage.getItem('optionalDetails')
    
    if (mandatory) {
      setUserDetails({
        ...JSON.parse(mandatory),
        ...(optional ? JSON.parse(optional) : {})
      })
    } else {
      navigate('/details')
    }
  }, [navigate])

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
        setReportPreference({
          reportType: 'full',
          investmentType: ''
        })
      }
    }
    setPreferenceLoaded(true)
  }, [])

  const parseOptionalNumber = (value: any) => {
    if (value === undefined || value === null || value === '') return undefined
    const parsed = Number(value)
    return Number.isNaN(parsed) ? undefined : parsed
  }

  const fetchRecommendations = useCallback(
    async (details: any, preference: ReportPreference) => {
      setRecommendationLoading(true)
      setRecommendationError(null)

      const payload = {
        age: Number(details.age ?? details.userAge ?? 30),
        investment_amount: Number(details.investmentAmount ?? details.investment_amount ?? 0),
        risk_preference: details.riskPreference ?? details.risk_preference ?? 'Medium',
        monthly_income: parseOptionalNumber(details.monthlyIncome ?? details.monthly_income),
        savings: parseOptionalNumber(details.savings ?? details.totalSavings ?? details.netWorth),
        time_horizon: details.timeHorizon ?? details.time_horizon,
        experience_level: details.experienceLevel ?? details.experience_level,
        financial_goals: details.financialGoals ?? details.financial_goals,
        monthly_expenses: parseOptionalNumber(details.monthlyExpenses ?? details.monthly_expenses),
        report_type: preference?.reportType ?? 'full',
        investment_type: preference?.investmentType || undefined
      }

      try {
        const response = await fetch(`${apiBaseUrl}/api/recommend`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        })

        if (!response.ok) {
          throw new Error('Unable to fetch recommendations')
        }

        const data = await response.json()
        const normalized = data?.recommendations ?? data
        setRecommendationResults(normalized)
        const serverReportType = data?.report_type === 'single' ? 'single' : 'full'
        setReportMode(serverReportType)
        setSingleReportData(data?.single_report ?? null)
      } catch (error: any) {
        setRecommendationError(error.message || 'Failed to load recommendations')
        setRecommendationResults(null)
        setReportMode('full')
        setSingleReportData(null)
      } finally {
        setRecommendationLoading(false)
      }
    },
    [apiBaseUrl]
  )

  useEffect(() => {
    if (userDetails && preferenceLoaded) {
      fetchRecommendations(userDetails, reportPreference)
    }
  }, [userDetails, preferenceLoaded, reportPreference, fetchRecommendations])

  // Dummy data based on risk preference (fallback for charts & legacy sections)
  const getDummyRecommendation = () => {
    if (!userDetails) return null

    const riskLevel = userDetails.riskPreference
    const amount = parseFloat(userDetails.investmentAmount)

    const recommendations = {
      Low: {
        expectedReturn: '8-10%',
        allocation: {
          labels: ['Fixed Deposits', 'Government Bonds', 'Debt Funds', 'Gold ETF'],
          values: [40, 30, 20, 10]
        },
        features: [
          'Capital protection',
          'Steady returns',
          'Low volatility',
          'Tax efficient options'
        ],
        explanation: 'This conservative portfolio is designed for investors who prioritize capital preservation over high returns. With 70% allocation to fixed-income securities (FDs and bonds), your investment is protected from market volatility. The remaining 30% in debt funds and gold ETF provides modest growth potential while maintaining stability. This approach is ideal for investors nearing retirement or those who cannot afford significant losses.'
      },
      Medium: {
        expectedReturn: '10-12%',
        allocation: {
          labels: ['Equity Funds', 'Debt Funds', 'Hybrid Funds', 'Gold ETF', 'FD'],
          values: [40, 25, 20, 10, 5]
        },
        features: [
          'Balanced growth',
          'Moderate risk',
          'Diversified portfolio',
          'Professional management'
        ],
        explanation: 'This balanced portfolio offers the best of both worlds - growth potential through equity exposure (60% in equity and hybrid funds) while maintaining stability through debt instruments (30%). This diversified approach helps smooth out market volatility while targeting inflation-beating returns. The 10% gold allocation acts as a hedge against economic uncertainty, making this suitable for investors with a 5-10 year investment horizon.'
      },
      High: {
        expectedReturn: '12-15%',
        allocation: {
          labels: ['Equity Funds', 'Small Cap Funds', 'International Funds', 'Debt Funds'],
          values: [50, 25, 15, 10]
        },
        features: [
          'High growth potential',
          'Long-term wealth creation',
          'Market-linked returns',
          'Tax benefits available'
        ],
        explanation: 'This aggressive growth portfolio is designed for long-term wealth creation with 90% equity exposure across different market segments. The large allocation to small-cap funds (25%) and international funds (15%) provides exposure to high-growth opportunities. While this portfolio carries higher volatility, it has the potential to significantly outperform inflation over 10+ years. The minimal debt allocation (10%) provides some stability during market downturns. This strategy is ideal for young investors with high risk tolerance and long investment horizons.'
      }
    }

    return recommendations[riskLevel as keyof typeof recommendations]
  }

  const recommendation = getDummyRecommendation()

  const riskPreference = userDetails?.riskPreference ?? 'Medium'

  const getCategoryItems = useCallback(
    (keys: string[]) => {
      if (!recommendationResults) return []
      for (const key of keys) {
        const value = recommendationResults[key]
        if (Array.isArray(value) && value.length) {
          return value
        }
      }
      return []
    },
    [recommendationResults]
  )

  const getItemName = (item: any) => {
    return (
      item?.name ||
      item?.scheme_name ||
      item?.schemeName ||
      item?.fund_name ||
      'Unnamed Product'
    )
  }

  const getItemScore = (item: any) => {
    if (item?.score !== undefined) return item.score
    if (item?.combined_score !== undefined) return item.combined_score
    if (item?.rating !== undefined) return item.rating
    return null
  }

  const formatSingleMetricValue = (value: any) => {
    if (value === null || value === undefined) return 'NA'
    if (typeof value === 'number') {
      return value.toLocaleString('en-IN', { maximumFractionDigits: 2 })
    }
    if (typeof value === 'object') {
      return Object.entries(value)
        .map(([key, val]) => `${key}: ${val}`)
        .join(', ')
    }
    return value
  }

  const buildSingleItemExplanation = (item: any) => {
    const extras = item?.extra_metrics || {}
    const parts: string[] = []

    const returns5y = item?.['5y_return'] ?? item?.return_5yr
    const returns3y = item?.['3y_return'] ?? item?.return_3yr
    if (returns5y) {
      parts.push(`5Y CAGR ${returns5y}%`)
    } else if (returns3y) {
      parts.push(`3Y CAGR ${returns3y}%`)
    }

    if (typeof extras.yield === 'number') {
      parts.push(`Yield ${extras.yield}%`)
    }
    if (typeof extras.expense_ratio === 'number') {
      parts.push(`Expense Ratio ${extras.expense_ratio}%`)
    }
    if (typeof extras.consistency === 'number') {
      parts.push(`Consistency ${extras.consistency}%`)
    }
    if (typeof extras.volatility === 'number') {
      parts.push(`Volatility ${extras.volatility}%`)
    }
    if (typeof extras.duration === 'number') {
      parts.push(`Duration ${extras.duration} yrs`)
    }
    if (typeof extras.beta === 'number') {
      parts.push(`Beta ${extras.beta}`)
    }

    return parts.length ? parts.join(' • ') : undefined
  }

  const riskNarratives: Record<string, string> = {
    Low: 'prioritize stability, capital protection, and steady income.',
    Medium: 'balance long-term growth with reasonable stability.',
    High: 'maximize long-term growth even if short-term volatility increases.'
  }

  const buildExplanation = (categoryLabel: string, custom?: string) => {
    if (custom) return custom
    const narrative =
      riskNarratives[riskPreference as keyof typeof riskNarratives] ??
      'deliver a balanced mix of growth and stability.'
    return `${categoryLabel} are selected to ${narrative}`
  }

  const categoryConfigs = useMemo(
    () => [
      { label: 'Equity Funds', keys: ['equity', 'equity_funds'] },
      { label: 'Debt Funds', keys: ['debt', 'debt_funds'] },
      { label: 'Hybrid Funds', keys: ['hybrid', 'hybrid_funds'] },
      { label: 'Gold ETFs', keys: ['gold', 'gold_etf', 'gold_etfs'] },
      { label: 'Stocks', keys: ['stocks', 'equity_stocks'] }
    ],
    []
  )

  const recommendationSections = categoryConfigs.map((config) => {
    const items = getCategoryItems(config.keys)
    return {
      ...config,
      items
    }
  })

  const renderFullRecommendationSection = () => (
    <section className="card mb-8">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Automated Investment Insights (For Informational Purposes Only)
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 italic">
            This is not investment advice. The results shown are automated, data-based evaluations. Please consult a SEBI-registered investment advisor before making investment decisions.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
            Based on live market data and your {riskPreference.toLowerCase()} risk preference.
          </p>
        </div>
        {recommendationLoading && (
          <span className="text-sm text-gray-500 dark:text-gray-400">Refreshing data...</span>
        )}
      </div>

      {recommendationError && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {recommendationError}
        </div>
      )}

      {!recommendationError && recommendationSections.every((section) => section.items.length === 0) && (
        <p className="mt-4 text-sm text-gray-600 dark:text-gray-300">
          {recommendationLoading
            ? 'Fetching live recommendations...'
            : 'No live recommendations available. Please try again in a moment.'}
        </p>
      )}

      <div className="mt-6 space-y-6">
        {recommendationSections.map(
          (section) =>
            section.items.length > 0 && (
              <div key={section.label}>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                  {section.label}
                </h3>
                <div className="space-y-4">
                  {section.items.slice(0, 5).map((item: any, idx: number) => (
                    <RecommendationCard
                      key={`${section.label}-${idx}-${getItemName(item)}`}
                      name={getItemName(item)}
                      category={section.label}
                      score={getItemScore(item)}
                      explanation={buildExplanation(section.label, item?.explanation)}
                    />
                  ))}
                </div>
              </div>
            )
        )}
      </div>

      {recommendationResults?.explanation && (
        <div className="mt-6">
          <ExplanationBox text={recommendationResults.explanation} />
        </div>
      )}
    </section>
  )

  const renderSingleRecommendationSection = () => {
    if (!singleReportData) return null
    const insights = singleReportData.insights || {}
    const analytics = singleReportData.analytics || {}
    const label =
      singleReportData.label ||
      SINGLE_CATEGORY_LABELS[singleReportData.category as keyof typeof SINGLE_CATEGORY_LABELS] ||
      'Selected Category'
    const topItems = analytics.top_items || []

    return (
      <section className="card mb-8">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Detailed {label} Report
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Tailored to your {riskPreference.toLowerCase()} risk preference using data-backed metrics.
            </p>
          </div>
          {recommendationLoading && (
            <span className="text-sm text-gray-500 dark:text-gray-400">Refreshing data...</span>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-6 mt-6">
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Overview</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{insights.overview}</p>
            </div>
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Risk alignment</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{insights.risk_alignment}</p>
            </div>
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Expected return range</h3>
              <p className="text-sm text-gray-900 dark:text-gray-100 mt-2 font-semibold">
                {insights.expected_return_range}
              </p>
            </div>
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Suggested allocation</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{insights.suggested_allocation}</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Example types</h3>
              <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                {(insights.examples || []).map((example: string) => (
                  <li key={example}>{example}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Pros</h3>
              <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                {(insights.pros || []).map((pro: string) => (
                  <li key={pro}>{pro}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Cons</h3>
              <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                {(insights.cons || []).map((con: string) => (
                  <li key={con}>{con}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {analytics.metrics && (
          <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(analytics.metrics).map(([key, value]) => (
              <div
                key={key}
                className="p-4 rounded-xl border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60"
              >
                <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-1">
                  {formatSingleMetricValue(value)}
                </p>
              </div>
            ))}
          </div>
        )}

        {topItems.length > 0 && (
          <div className="mt-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Data-backed highlights
            </h3>
            <div className="space-y-4 mt-4">
              {topItems.map((item: any, idx: number) => (
                <RecommendationCard
                  key={`${label}-${idx}-${item.name}`}
                  name={item.name}
                  category={label}
                  score={item.score}
                  explanation={buildSingleItemExplanation(item)}
                />
              ))}
            </div>
          </div>
        )}

        {analytics.factors_analyzed && (
          <div className="mt-8">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Factors analyzed
            </h3>
            <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-300 space-y-1">
              {analytics.factors_analyzed.map((factor: string) => (
                <li key={factor}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-6">
          <ExplanationBox text={insights.disclaimer || analytics.disclaimer} />
        </div>
      </section>
    )
  }

  // Dummy SIP projection data
  const sipData = {
    labels: ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'],
    invested: [12000, 24000, 36000, 48000, 60000],
    returns: [13000, 27500, 43200, 60800, 81500]
  }

  const handleDownloadPDF = async () => {
    try {
      const response = await fetch('https://builder.empromptu.ai/api_tools/database/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer beb20e01818d025fb8b5a8c55fd12247',
          'X-Generated-App-ID': '6b451cdd-c751-4151-bf30-5751562c9a9b',
          'X-Usage-Key': 'c42100c7fbb5e7798f2d07e0a27737a2'
        },
        body: JSON.stringify({
          query: "INSERT INTO app_6b451cddc7514151bf305751562c9a9b.calculation_history (user_id, calculation_type, input_data, result_data, created_at) VALUES ($1, $2, $3, $4, NOW())",
          params: [1, 'recommendation', JSON.stringify(userDetails), JSON.stringify(recommendation)]
        })
      })
      
      alert('PDF download feature coming soon!')
    } catch (error) {
      console.error('Error saving calculation:', error)
      alert('PDF download feature coming soon!')
    }
  }

  if (!userDetails || !recommendation) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <BackButton to="/optional" />
        </div>

        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Your Personalized Investment Plan
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Based on your {userDetails.riskPreference.toLowerCase()} risk preference and ₹{parseInt(userDetails.investmentAmount).toLocaleString()} investment
          </p>
          {reportMode === 'single' && singleReportData && (
            <p className="text-sm text-primary-600 dark:text-primary-300 mt-3">
              Mode: Single-Investment Report — {singleReportData.label || SINGLE_CATEGORY_LABELS[(singleReportData.category || '') as keyof typeof SINGLE_CATEGORY_LABELS] || 'Selected Category'}
            </p>
          )}
        </div>

        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <SummaryCard
            title="Expected Returns"
            value={recommendation.expectedReturn}
            subtitle="Annual returns"
            icon={<BarChart3 className="h-6 w-6" />}
          />
          <SummaryCard
            title="Risk Level"
            value={userDetails.riskPreference}
            subtitle="Based on your preference"
          />
          <SummaryCard
            title="Investment Amount"
            value={`₹${parseInt(userDetails.investmentAmount).toLocaleString()}`}
            subtitle="Initial investment"
          />
        </div>

        {reportMode === 'single' ? renderSingleRecommendationSection() : renderFullRecommendationSection()}

        {reportMode === 'full' && (
          <>
            {/* Investment Strategy Explanation (before charts to satisfy flow) */}
            <div className="card mb-8">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Investment Strategy Explained
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-6">
                {recommendation.explanation}
              </p>
              
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Key Benefits of This Plan:
              </h3>
              <div className="grid md:grid-cols-2 gap-4">
                {recommendation.features.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                    <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Charts and Analytics */}
            <div className="grid lg:grid-cols-2 gap-8 mb-8">
              <div className="card">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Recommended Asset Allocation
                </h2>
                <AllocationDonutChart data={recommendation.allocation} />
              </div>
              <div className="card">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  SIP Growth Projection
                </h2>
                <SIPLineGraph data={sipData} />
              </div>
            </div>
          </>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate('/compare')}
            className="btn-secondary flex items-center justify-center space-x-2"
          >
            <BarChart3 className="h-4 w-4" />
            <span>Compare Plans</span>
          </button>
          
          <button
            onClick={handleDownloadPDF}
            className="btn-primary flex items-center justify-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Download Report</span>
          </button>
        </div>
      </div>
    </div>
  )
}
