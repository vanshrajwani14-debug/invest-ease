import React from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, Shield, Target, Zap, BookOpen } from 'lucide-react'

export const LandingPage: React.FC = () => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'

  const features = [
    {
      icon: <Target className="h-8 w-8" />,
      title: 'Personalized Recommendations',
      description: 'Get investment plans tailored to your risk profile and financial goals.'
    },
    {
      icon: <Shield className="h-8 w-8" />,
      title: 'Risk Assessment',
      description: 'Smart risk analysis to match your comfort level with suitable investments.'
    },
    {
      icon: <Zap className="h-8 w-8" />,
      title: 'Quick Setup',
      description: 'Start investing in minutes with our streamlined onboarding process.'
    }
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-blue-100 dark:from-gray-900 dark:to-gray-800 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <TrendingUp className="h-16 w-16 text-primary-600" />
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
              Smart Investing
              <span className="text-primary-600 block">Made Simple</span>
            </h1>
            
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
              Get personalized investment recommendations based on your age, risk tolerance, 
              and financial goals. Start your investment journey with confidence.
            </p>
            
            <Link
              to={isAuthenticated ? "/details" : "/auth"}
              className="inline-flex items-center px-8 py-4 text-lg font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-xl transition-colors duration-200 shadow-lg hover:shadow-xl"
            >
              Start Investing
              <TrendingUp className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Why Choose InvestEase?
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              We make investing accessible and straightforward for everyone, 
              regardless of your experience level.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-4 text-primary-600">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Learning Hub Section */}
      <section className="py-20 bg-gray-50 dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="card max-w-3xl mx-auto text-center">
            <div className="flex justify-center mb-6">
              <BookOpen className="h-16 w-16 text-primary-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Learn the Basics
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
              New to investing? Start with our Learning Hub to understand SIPs, mutual funds, stocks, and more. 
              Learn at your own pace with simple explanations and helpful videos.
            </p>
            <Link
              to="/learning-hub"
              className="inline-flex items-center px-8 py-4 text-lg font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-xl transition-colors duration-200 shadow-lg hover:shadow-xl"
            >
              <BookOpen className="mr-2 h-5 w-5" />
              Explore Learning Hub
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Start Your Investment Journey?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Join thousands of smart investors who trust InvestEase
          </p>
          <Link
            to={isAuthenticated ? "/details" : "/auth"}
            className="inline-flex items-center px-8 py-4 text-lg font-medium text-primary-600 bg-white hover:bg-gray-50 rounded-xl transition-colors duration-200 shadow-lg hover:shadow-xl"
          >
            Get Started Now
          </Link>
        </div>
      </section>
    </div>
  )
}
