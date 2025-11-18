import React from 'react'
import { Play, ExternalLink } from 'lucide-react'

interface Video {
  id: string
  title: string
  url: string
  duration: string
  thumbnail: string
}

interface VideoCardProps {
  video: Video
}

/**
 * Reusable VideoCard component for displaying video information
 * Shows thumbnail, title, duration, and a button to watch the video
 */
export const VideoCard: React.FC<VideoCardProps> = ({ video }) => {
  const handleWatchVideo = () => {
    window.open(video.url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="card hover:shadow-md transition-shadow duration-200">
      <div className="relative mb-4 rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 aspect-video">
        {video.thumbnail ? (
          <img
            src={video.thumbnail}
            alt={video.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback to placeholder if image fails to load
              const target = e.target as HTMLImageElement
              target.style.display = 'none'
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900 dark:to-primary-800">
            <Play className="h-12 w-12 text-primary-600 dark:text-primary-400" />
          </div>
        )}
        <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
          {video.duration}
        </div>
      </div>
      
      <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
        {video.title}
      </h4>
      
      <button
        onClick={handleWatchVideo}
        className="btn-primary w-full flex items-center justify-center space-x-2"
      >
        <Play className="h-4 w-4" />
        <span>Watch Video</span>
        <ExternalLink className="h-4 w-4" />
      </button>
    </div>
  )
}

