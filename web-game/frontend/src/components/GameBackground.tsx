import React from 'react';
import { getRandomCharacter } from '../constants/images';

interface GameBackgroundProps {
  children: React.ReactNode;
  variant?: 'default' | 'battle' | 'gacha' | 'story';
}

const GameBackground: React.FC<GameBackgroundProps> = ({ children, variant = 'default' }) => {
  const getBackgroundStyle = () => {
    switch (variant) {
      case 'battle':
        return {
          backgroundImage: `
            linear-gradient(rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.85)),
            url('${getRandomCharacter()}')
          `,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        };
      case 'gacha':
        return {
          backgroundImage: `
            linear-gradient(135deg, rgba(147, 51, 234, 0.1) 0%, rgba(79, 70, 229, 0.1) 50%, rgba(245, 158, 11, 0.1) 100%),
            radial-gradient(circle at 25% 25%, rgba(147, 51, 234, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(245, 158, 11, 0.2) 0%, transparent 50%)
          `,
          backgroundSize: '100% 100%, 200px 200px, 300px 300px',
          backgroundPosition: 'center, top left, bottom right'
        };
      case 'story':
        return {
          backgroundImage: `
            linear-gradient(rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9)),
            linear-gradient(45deg, transparent 49%, rgba(255, 255, 255, 0.01) 50%, transparent 51%)
          `,
          backgroundSize: '100% 100%, 50px 50px'
        };
      default:
        return {
          backgroundImage: `
            linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%),
            radial-gradient(circle at 25% 25%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(168, 85, 247, 0.1) 0%, transparent 50%)
          `,
          backgroundSize: '100% 100%, 150px 150px, 200px 200px'
        };
    }
  };

  return (
    <div 
      className="min-h-screen bg-pattern relative overflow-hidden"
      style={getBackgroundStyle()}
    >
      {/* Animated particles overlay */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-arise-gold rounded-full opacity-30 animate-ping"></div>
        <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-purple-400 rounded-full opacity-40 animate-pulse"></div>
        <div className="absolute top-1/2 left-3/4 w-1.5 h-1.5 bg-blue-400 rounded-full opacity-25 animate-bounce"></div>
        <div className="absolute top-1/3 right-1/3 w-1 h-1 bg-arise-gold rounded-full opacity-35 animate-ping" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-1/4 left-1/2 w-2 h-2 bg-purple-500 rounded-full opacity-20 animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default GameBackground;
