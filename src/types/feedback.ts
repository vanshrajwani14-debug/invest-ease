export type FeedbackCategory =
  | 'Bug'
  | 'Feature Request'
  | 'Usability Issue'
  | 'General Feedback'
  | 'Other'

export interface FeedbackPayload {
  name?: string
  email?: string
  category: FeedbackCategory
  rating: number
  message: string
  contactConsent: boolean
}

export interface FeedbackResponse extends FeedbackPayload {
  id: string
  createdAt: string
}

