import React from 'react';

const SimpleApp: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold mb-4 text-purple-400">ARISE</h1>
        <h2 className="text-2xl mb-8">Solo Leveling Web Game</h2>
        <p className="text-gray-300">Welcome to the world of hunters!</p>
      </div>
    </div>
  );
};

export default SimpleApp;