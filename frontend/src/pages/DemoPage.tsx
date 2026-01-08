import React, { useState, useRef } from 'react';
import { ArrowLeft, Play } from 'lucide-react';

interface DemoPageProps {
  onBack: () => void;
}

export function DemoPage({ onBack }: DemoPageProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handlePlay = () => setIsPlaying(true);
  const handlePause = () => setIsPlaying(false);
  
  const handleVideoError = () => {
    setVideoError('Video file not found. Please ensure mina_oneai.mp4 is in the public folder.');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#191919] text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </button>
              <div>
                <h1 className="text-3xl">Demo</h1>
                <p className="text-gray-400 mt-1">
                  Watch the system demonstration video
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Supply Chain Risk Analysis System Demo
            </h2>
            <p className="text-gray-600">
              This video demonstrates the key features and functionality of the Supply Chain Risk Analysis Dashboard.
            </p>
          </div>

          {/* Video Player */}
          <div className="relative bg-black rounded-lg overflow-hidden shadow-lg">
            {videoError ? (
              <div className="p-12 text-center text-white">
                <p className="text-lg mb-4">{videoError}</p>
                <p className="text-sm text-gray-300">
                  Expected path: <code className="bg-gray-800 px-2 py-1 rounded">/mina_oneai.mp4</code>
                </p>
                <p className="text-sm text-gray-300 mt-2">
                  Please copy the video file to: <code className="bg-gray-800 px-2 py-1 rounded">frontend/public/mina_oneai.mp4</code>
                </p>
              </div>
            ) : (
              <video
                ref={videoRef}
                className="w-full h-auto"
                controls
                onPlay={handlePlay}
                onPause={handlePause}
                onEnded={handlePause}
                onError={handleVideoError}
              >
                <source src="/mina_oneai.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            )}
          </div>

          {/* Video Info */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Features Covered</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Risk Forecasting</li>
                <li>• Mitigation Strategies</li>
                <li>• Real-time Analysis</li>
                <li>• Dashboard Navigation</li>
              </ul>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">System Capabilities</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Multi-module Analysis</li>
                <li>• Prophet Forecasting</li>
                <li>• Risk Scoring</li>
                <li>• Action Plans</li>
              </ul>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Quick Tips</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Use fullscreen for better view</li>
                <li>• Adjust playback speed as needed</li>
                <li>• Pause to review details</li>
                <li>• Check video controls</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

