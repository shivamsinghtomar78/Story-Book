import React from 'react';

const ProgressIndicator = ({ 
  currentStep = 1, 
  totalSteps = 4, 
  stepName = 'Processing',
  estimatedTime = null,
  progress = 0
}) => {
  const steps = [
    { id: 1, name: 'Generating Story', icon: '📝' },
    { id: 2, name: 'Creating Images', icon: '🎨' },
    { id: 3, name: 'Generating Audio', icon: '🎵' },
    { id: 4, name: 'Creating PDF', icon: '📄' }
  ];

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>{stepName}</span>
          {estimatedTime && (
            <span>~{estimatedTime}s remaining</span>
          )}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          >
            <div className="h-full w-full bg-white/20 animate-pulse" />
          </div>
        </div>
        <div className="text-right text-sm text-gray-500 mt-1">
          {progress}%
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step) => (
          <div 
            key={step.id}
            className={`flex items-center p-3 rounded-lg transition-all duration-300 ${
              currentStep === step.id 
                ? 'bg-blue-50 border-2 border-blue-500 scale-105' 
                : currentStep > step.id
                ? 'bg-green-50 border-2 border-green-500'
                : 'bg-gray-50 border-2 border-gray-200'
            }`}
          >
            <div className={`text-3xl mr-4 ${
              currentStep === step.id ? 'animate-bounce' : ''
            }`}>
              {step.icon}
            </div>
            <div className="flex-1">
              <div className={`font-semibold ${
                currentStep === step.id 
                  ? 'text-blue-700' 
                  : currentStep > step.id
                  ? 'text-green-700'
                  : 'text-gray-500'
              }`}>
                {step.name}
              </div>
            </div>
            <div className="ml-4">
              {currentStep === step.id && (
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
              {currentStep > step.id && (
                <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressIndicator;
