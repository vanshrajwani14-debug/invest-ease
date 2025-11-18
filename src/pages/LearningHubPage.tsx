import React from 'react'
import { BookOpen, CheckCircle } from 'lucide-react'
import { VideoCard } from '../components/VideoCard'

/**
 * TypeScript interfaces for Learning Hub data structure
 */
interface Video {
  id: string
  title: string
  url: string
  duration: string
  thumbnail: string
}

interface Topic {
  id: string
  title: string
  description: string
  keyPoints: string[]
  videos: Video[]
}

/**
 * Learning Hub content data structure
 * Easy to extend with more topics and videos
 */
const learningHubContent: Topic[] = [
  {
    id: 'sip',
    title: 'SIP (Systematic Investment Plan)',
    description: 'SIP is a disciplined approach to investing where you invest a fixed amount regularly (monthly) in mutual funds. It helps you build wealth gradually through the power of compounding and rupee cost averaging.',
    keyPoints: [
      'Start with as little as ₹500 per month',
      'Automatically invest on a fixed date each month',
      'Benefit from rupee cost averaging (buy more units when prices are low)',
      'Ideal for long-term wealth creation (5+ years)',
      'No need to time the market'
    ],
    videos: [
      {
        id: 'sip-1',
        title: 'What is SIP? Complete Guide for Beginners',
        url: 'https://youtu.be/PbldLCsspgE',
        duration: '19:31',
        thumbnail: 'https://img.youtube.com/vi/PbldLCsspgE/maxresdefault.jpg'
      },
      {
        id: 'sip-2',
        title: 'How SIP Works: Power of Compounding',
        url: 'https://www.youtube.com/watch?v=6yY6Y6Y6Y6Y',
        duration: '10:15',
        thumbnail: 'https://img.youtube.com/vi/6yY6Y6Y6Y6Y/mqdefault.jpg'
      },
      {
        id: 'sip-3',
        title: 'SIP vs Lump Sum Investment: Which is Better?',
        url: 'https://www.youtube.com/watch?v=7zZ7Z7Z7Z7Z',
        duration: '12:00',
        thumbnail: 'https://img.youtube.com/vi/7zZ7Z7Z7Z7Z/mqdefault.jpg'
      }
    ]
  },
  {
    id: 'mutual-funds',
    title: 'Mutual Funds',
    description: 'Mutual funds pool money from multiple investors to invest in a diversified portfolio of stocks, bonds, or other securities. They are managed by professional fund managers, making them ideal for beginners who want expert management.',
    keyPoints: [
      'Professional fund management by experts',
      'Diversification across multiple stocks/bonds',
      'Low minimum investment (₹100-₹5000)',
      'Liquidity - can redeem anytime (except ELSS)',
      'Types: Equity, Debt, Hybrid, and more'
    ],
    videos: [
      {
        id: 'mf-1',
        title: 'What is a Mutual Fund and How Does It Work?',
        url: 'https://youtu.be/PbldLCsspgE',
        duration: '19:31',
        thumbnail: 'https://img.youtube.com/vi/PbldLCsspgE/maxresdefault.jpg'
      },
      {
        id: 'mf-2',
        title: 'Mutual Fund Categories Explained',
        url: 'https://youtu.be/V5wn0oGe2Ss',
        duration: '6:49',
        thumbnail: 'https://img.youtube.com/vi/V5wn0oGe2Ss/maxresdefault.jpg'
      },
      {
        id: 'mf-3',
        title: 'Mutual Funds vs Index Funds vs ETFs vs Hedge Funds Explained',
        url: 'https://youtu.be/BxNxnj_JWTY',
        duration: '15:11',
        thumbnail: 'https://img.youtube.com/vi/BxNxnj_JWTY/maxresdefault.jpg'
      }
    ]
  },
  {
    id: 'stocks',
    title: 'Stocks',
    description: 'Stocks represent ownership in a company. When you buy a stock, you become a shareholder and can benefit from the company\'s growth through price appreciation and dividends. Stocks offer higher returns but come with higher risk.',
    keyPoints: [
      'Ownership stake in a company',
      'Potential for high returns over long term',
      'Higher risk compared to mutual funds',
      'Requires research and market knowledge',
      'Best for investors with high risk tolerance'
    ],
    videos: [
      {
        id: 'stocks-1',
        title: 'Stock Market Basics: How Stocks Work',
        url: 'https://www.youtube.com/watch?v=1d1d1d1d1d1',
        duration: '12:30',
        thumbnail: 'https://img.youtube.com/vi/1d1d1d1d1d1/mqdefault.jpg'
      },
      {
        id: 'stocks-2',
        title: 'How to Start Investing in Stocks: Step by Step',
        url: 'https://www.youtube.com/watch?v=2e2e2e2e2e2',
        duration: '16:45',
        thumbnail: 'https://img.youtube.com/vi/2e2e2e2e2e2/mqdefault.jpg'
      },
      {
        id: 'stocks-3',
        title: 'Stock Market vs Mutual Funds: Which Should You Choose?',
        url: 'https://www.youtube.com/watch?v=3f3f3f3f3f3',
        duration: '13:20',
        thumbnail: 'https://img.youtube.com/vi/3f3f3f3f3f3/mqdefault.jpg'
      }
    ]
  },
  {
    id: 'gold',
    title: 'Gold',
    description: 'Gold is a traditional safe-haven investment that acts as a hedge against inflation and economic uncertainty. You can invest in gold through physical gold, Gold ETFs, Gold Mutual Funds, or Sovereign Gold Bonds. Gold typically performs well during market downturns and currency devaluation.',
    keyPoints: [
      'Acts as a hedge against inflation and economic uncertainty',
      'Low correlation with stocks - provides portfolio diversification',
      'Multiple ways to invest: Physical, ETFs, Mutual Funds, SGBs',
      'Sovereign Gold Bonds offer 2.5% annual interest plus gold price appreciation',
      'Ideal for 5-10% of your portfolio allocation',
      'Liquidity varies by investment method (ETFs are most liquid)'
    ],
    videos: [
      {
        id: 'gold-1',
        title: 'Gold Investment Guide: Physical vs Digital Gold',
        url: 'https://www.youtube.com/watch?v=4g4g4g4g4g4',
        duration: '11:20',
        thumbnail: 'https://img.youtube.com/vi/4g4g4g4g4g4/mqdefault.jpg'
      },
      {
        id: 'gold-2',
        title: 'Sovereign Gold Bonds (SGB) Explained: Complete Guide',
        url: 'https://www.youtube.com/watch?v=5h5h5h5h5h5',
        duration: '14:30',
        thumbnail: 'https://img.youtube.com/vi/5h5h5h5h5h5/mqdefault.jpg'
      },
      {
        id: 'gold-3',
        title: 'Gold ETFs vs Gold Mutual Funds: Which is Better?',
        url: 'https://www.youtube.com/watch?v=6i6i6i6i6i6',
        duration: '9:45',
        thumbnail: 'https://img.youtube.com/vi/6i6i6i6i6i6/mqdefault.jpg'
      }
    ]
  },
  {
    id: 'government-bonds',
    title: 'Government Bonds',
    description: 'Government bonds are debt securities issued by the government to raise funds. They are considered one of the safest investments as they are backed by the government. You can invest through Government Securities (G-Secs), State Development Loans (SDLs), or bond mutual funds. They provide steady, predictable returns with minimal default risk.',
    keyPoints: [
      'Highest safety - backed by the government (virtually no default risk)',
      'Fixed interest payments (coupon) at regular intervals',
      'Suitable for conservative investors seeking capital preservation',
      'Lower returns compared to equity but more stable',
      'Ideal for short to medium-term goals (1-5 years)',
      'Can invest directly or through debt mutual funds',
      'Tax benefits available on certain government bonds'
    ],
    videos: [
      {
        id: 'bonds-1',
        title: 'Government Bonds Explained: Safe Investment Option',
        url: 'https://www.youtube.com/watch?v=7j7j7j7j7j7',
        duration: '13:15',
        thumbnail: 'https://img.youtube.com/vi/7j7j7j7j7j7/mqdefault.jpg'
      },
      {
        id: 'bonds-2',
        title: 'How to Invest in Government Bonds: Step by Step',
        url: 'https://www.youtube.com/watch?v=8k8k8k8k8k8',
        duration: '16:20',
        thumbnail: 'https://img.youtube.com/vi/8k8k8k8k8k8/mqdefault.jpg'
      },
      {
        id: 'bonds-3',
        title: 'Government Bonds vs Fixed Deposits: Which is Better?',
        url: 'https://www.youtube.com/watch?v=9l9l9l9l9l9',
        duration: '12:40',
        thumbnail: 'https://img.youtube.com/vi/9l9l9l9l9l9/mqdefault.jpg'
      }
    ]
  }
]

/**
 * Learning Hub Page Component
 * Displays educational content about SIPs, Mutual Funds, Stocks, Gold, and Government Bonds
 */
export const LearningHubPage: React.FC = () => {
  return (
    <div className="min-h-screen py-12 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Section */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <BookOpen className="h-12 w-12 text-primary-600" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Learning Hub
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Understand the basics before you start investing. Learn at your own pace with simple explanations and helpful videos.
          </p>
        </div>

        {/* Topics Section */}
        <div className="space-y-12">
          {learningHubContent.map((topic) => (
            <section key={topic.id} className="card">
              {/* Topic Header */}
              <div className="mb-6">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-3">
                  {topic.title}
                </h2>
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  {topic.description}
                </p>
              </div>

              {/* Key Points */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Key Points:
                </h3>
                <ul className="space-y-2">
                  {topic.keyPoints.map((point, index) => (
                    <li key={index} className="flex items-start space-x-3">
                      <CheckCircle className="h-5 w-5 text-primary-600 dark:text-primary-400 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recommended Videos */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Recommended Videos:
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {topic.videos.map((video) => (
                    <VideoCard key={video.id} video={video} />
                  ))}
                </div>
              </div>
            </section>
          ))}
        </div>

        {/* Footer Note */}
        <div className="mt-12 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            Continue learning and make informed investment decisions. Remember, investing involves risk, and past performance doesn't guarantee future results.
          </p>
        </div>
      </div>
    </div>
  )
}

