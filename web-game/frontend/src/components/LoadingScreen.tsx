import React from 'react';

const LoadingScreen: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-game-bg">
      <div className="text-center">
        <div className="game-title mb-8 animate-pulse">
          ARISE
        </div>
        <div className="loading-spinner mx-auto mb-4"></div>
        <p className="text-gray-300 text-lg">Loading your adventure...</p>
      </div>
    </div>
  );
};

export default LoadingScreen;