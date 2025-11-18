import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { Footer } from './components/Footer'
import { LandingPage } from './pages/LandingPage'
import { AuthPage } from './pages/AuthPage'
import { MandatoryDetailsPage } from './pages/MandatoryDetailsPage'
import { OptionalDetailsPage } from './pages/OptionalDetailsPage'
import { RecommendationPage } from './pages/RecommendationPage'
import { ComparePlansPage } from './pages/ComparePlansPage'
import { SIPCalculatorPage } from './pages/SIPCalculatorPage'
import { LearningHubPage } from './pages/LearningHubPage'
import { NotFoundPage } from './pages/NotFoundPage'
<<<<<<< HEAD
// @ts-ignore - JS module
import { DetailedReportSelector } from './pages/DetailedReportSelector.jsx'
=======
import { FeedbackPage } from './pages/FeedbackPage'
>>>>>>> 734bbeb6dc137c0c71f15e05cf68bfe1fc6acec3

function App() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/details" element={<MandatoryDetailsPage />} />
          <Route path="/optional" element={<OptionalDetailsPage />} />
          <Route path="/recommendation" element={<RecommendationPage />} />
          <Route path="/compare" element={<ComparePlansPage />} />
          <Route path="/sip-calculator" element={<SIPCalculatorPage />} />
<<<<<<< HEAD
          <Route path="/detailed-report" element={<DetailedReportSelector />} />
=======
          <Route path="/learning-hub" element={<LearningHubPage />} />
          <Route path="/feedback" element={<FeedbackPage />} />
>>>>>>> 734bbeb6dc137c0c71f15e05cf68bfe1fc6acec3
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App
