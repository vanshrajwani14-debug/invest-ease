import React, { useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { AlertTriangle, BarChart3, Loader2 } from 'lucide-react'
import { BackButton } from '../components/BackButton'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const CATEGORY_OPTIONS = [
  { label: 'Mutual Funds', value: 'mutualfunds', description: 'NAV trends, risk and cost metrics' },
  { label: 'Stocks', value: 'stocks', description: 'Large-cap equities with volatility and beta' },
  { label: 'Government Bonds', value: 'bonds', description: 'Sovereign yield curve snapshots' },
  { label: 'Gold', value: 'gold', description: 'Listed gold ETFs with price behaviour' },
  { label: 'SIP', value: 'sip', description: 'Formula-based SIP projections' },
]

const metricLabelMap = {
  risk_score: 'Risk Score',
  volatility: 'Volatility (%)',
  avg_return_5y: '5Y CAGR (%)',
  consistency_score: 'Consistency (%)',
  category_avg_expense_ratio: 'Average Expense Ratio (%)',
  avg_beta_vs_nifty: 'Average Beta vs Nifty',
  avg_yield: 'Average Yield (%)',
  avg_duration: 'Average Duration (Years)',
  monthly_investment: 'Monthly Contribution (₹)',
  assumed_return: 'Assumed Annual Return (%)',
  projection_values: 'Projection',
}

const formatNumber = (value, suffix = '') => {
  if (value === null || value === undefined) return 'NA'
  if (typeof value !== 'number') return value
  return `${value.toLocaleString('en-IN', {
    maximumFractionDigits: 2,
  })}${suffix}`
}

const DetailedReportSelector = () => {
  const [selectedCategory, setSelectedCategory] = useState('')
  const [reportData, setReportData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const apiBaseUrl =
    (import.meta?.env?.VITE_API_BASE_URL) || 'http://localhost:8000'

  const fetchReport = async () => {
    if (!selectedCategory) {
      setError('Please select a category')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${apiBaseUrl}/report/${selectedCategory}`)
      if (!response.ok) {
        throw new Error('Unable to fetch report')
      }
      const data = await response.json()
      setReportData(data)
    } catch (err) {
      setReportData(null)
      setError(err.message || 'Failed to fetch report')
    } finally {
      setLoading(false)
    }
  }

  const chartConfig = useMemo(() => {
    if (!reportData?.chart_data || !reportData.chart_data.dates?.length) return null

    const datasets = [
      {
        label: 'Category Trend',
        data: reportData.chart_data.values || [],
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.08)',
        tension: 0.25,
      },
    ]

    if (reportData.chart_data.invested) {
      datasets.push({
        label: 'Amount Invested',
        data: reportData.chart_data.invested,
        borderColor: '#059669',
        backgroundColor: 'rgba(5, 150, 105, 0.08)',
        tension: 0.25,
      })
    }

    return {
      data: {
        labels: reportData.chart_data.dates,
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              usePointStyle: true,
            },
          },
        },
        scales: {
          x: {
            ticks: {
              maxTicksLimit: 6,
            },
          },
          y: {
            beginAtZero: false,
          },
        },
      },
    }
  }, [reportData])

  const renderMetricValue = (key, value) => {
    if (value === null || value === undefined) return 'NA'
    if (typeof value === 'number') {
      if (key === 'monthly_investment') return `₹${value.toLocaleString('en-IN')}`
      if (key === 'assumed_return' || key.includes('return') || key.includes('yield')) {
        return `${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}%`
      }
      if (key.toLowerCase().includes('score')) {
        return `${value.toFixed(2)} / 100`
      }
      return value.toLocaleString('en-IN', { maximumFractionDigits: 2 })
    }

    if (typeof value === 'object') {
      return (
        <div className="space-y-1">
          {Object.entries(value).map(([subKey, subValue]) => (
            <div key={subKey} className="flex justify-between text-sm">
              <span className="text-gray-500 capitalize">{subKey.replace(/_/g, ' ')}:</span>
              <span className="font-semibold">{formatNumber(subValue)}</span>
            </div>
          ))}
        </div>
      )
    }

    return value
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-10 space-y-8">
      <div className="flex items-center justify-between">
        <BackButton label="Back" />
        <div className="text-right">
          <p className="text-sm text-gray-500">SEBI-compliant analytics</p>
          <p className="text-xs text-gray-400">No personalised advice displayed</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-xl p-6 border border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="text-primary-600" />
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
              Detailed Category Report
            </h1>
            <p className="text-gray-500 text-sm">
              Select one investment category to view historical analytics, top-ranked instruments, and methodology.
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          {CATEGORY_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedCategory(option.value)}
              className={`text-left p-4 rounded-lg border transition ${
                selectedCategory === option.value
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-primary-300'
              }`}
            >
              <p className="font-semibold">{option.label}</p>
              <p className="text-sm text-gray-500">{option.description}</p>
            </button>
          ))}
        </div>

        <div className="mt-6 flex items-center gap-4">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="border border-gray-300 rounded-lg px-4 py-2 flex-1"
          >
            <option value="">Select category</option>
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            onClick={fetchReport}
            disabled={!selectedCategory || loading}
            className="px-6 py-2 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 disabled:opacity-60"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading
              </span>
            ) : (
              'Generate report'
            )}
          </button>
        </div>
        {error && (
          <div className="mt-4 flex items-center gap-2 text-sm text-red-600">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}
      </div>

      {reportData && (
        <div className="space-y-8">
          <section className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-xl font-semibold mb-2">Category Overview</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">{reportData.overview}</p>
          </section>

          <section className="grid md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-4">Data Insights</h3>
              <div className="grid sm:grid-cols-2 gap-4">
                {Object.entries(reportData.metrics || {}).map(([key, value]) => (
                  <div key={key} className="p-4 border border-gray-100 dark:border-gray-700 rounded-lg">
                    <p className="text-xs uppercase text-gray-500 tracking-wide mb-1">
                      {metricLabelMap[key] || key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {renderMetricValue(key, value)}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-4">Historical Performance</h3>
              {chartConfig ? (
                <div className="h-72">
                  <Line data={chartConfig.data} options={chartConfig.options} />
                </div>
              ) : (
                <p className="text-sm text-gray-500">Chart data not available for this category.</p>
              )}
            </div>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Top-ranked instruments</h3>
              <span className="text-sm text-gray-500">Sorted by score/metrics</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-700">
                    <th className="py-2 pr-4">Instrument</th>
                    <th className="py-2 px-4">Score</th>
                    <th className="py-2 px-4">Returns</th>
                    <th className="py-2 px-4">Key Metrics</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.top_items?.map((item, index) => (
                    <tr key={`${item.name}-${index}`} className="border-b border-gray-50 dark:border-gray-700/40">
                      <td className="py-3 pr-4">
                        <p className="font-semibold text-gray-900 dark:text-gray-100">{item.name}</p>
                        {item.scheme_code && (
                          <p className="text-xs text-gray-500">Scheme #{item.scheme_code}</p>
                        )}
                        {item.ticker && (
                          <p className="text-xs text-gray-500 uppercase">{item.ticker}</p>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {item.score !== null && item.score !== undefined ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full bg-primary-100 text-primary-700 text-xs font-semibold">
                            {item.score.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-gray-500 text-xs">NA</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <p>3Y: {formatNumber(item['3y_return'] ?? item.return_3yr, '%')}</p>
                        <p>5Y: {formatNumber(item['5y_return'] ?? item.return_5yr, '%')}</p>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-2">
                          {item.extra_metrics &&
                            Object.entries(item.extra_metrics).map(([metricKey, metricValue]) => (
                              <span
                                key={metricKey}
                                className="px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-xs text-gray-700 dark:text-gray-200"
                              >
                                {metricKey.replace(/_/g, ' ')}: {formatNumber(metricValue)}
                              </span>
                            ))}
                      </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="grid md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-3">Factors analyzed</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-300">
                {reportData.factors_analyzed?.map((factor) => (
                  <li key={factor}>{factor}</li>
                ))}
              </ul>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-3">Mandatory disclaimer</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                {reportData.disclaimer}
              </p>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

export { DetailedReportSelector }

