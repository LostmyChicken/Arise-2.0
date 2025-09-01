import React, { useState, useEffect } from 'react';
import { 
  SparklesIcon, 
  StarIcon,
  GiftIcon,
  TicketIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import { IMAGES, CHARACTER_RARITY, getRandomCharacter } from '../constants/images';
import GameBackground from '../components/GameBackground';

// Custom GemIcon
const GemIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

interface GachaResult {
  id: string;
  type: string;
  name: string;
  rarity: string;
  stats?: any;
  description?: string;
  is_new: boolean;
}

interface GachaRates {
  rates: {
    common: number;
    rare: number;
    epic: number;
    legendary: number;
  };
  pity_system: {
    legendary_pity: number;
    epic_pity: number;
  };
  costs: {
    single_pull_gems: number;
    ten_pull_gems: number;
    single_pull_tickets: number;
    ten_pull_tickets: number;
  };
}

const GachaPage: React.FC = () => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { user } = useAuth();
  const [rates, setRates] = useState<GachaRates | null>(null);
  const [pulling, setPulling] = useState(false);
  const [results, setResults] = useState<GachaResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [animationPhase, setAnimationPhase] = useState<'idle' | 'pulling' | 'revealing'>('idle');
  const [currentReveal, setCurrentReveal] = useState(0);
  const [playerResources, setPlayerResources] = useState({ gems: 0, tickets: 0 });

  useEffect(() => {
    loadGachaRates();
    loadPlayerResources();
  }, []);

  const loadGachaRates = async () => {
    try {
      const response = await api.get('/gacha/rates');
      setRates(response.data);
    } catch (error) {
      console.error('Failed to load gacha rates:', error);
      // Mock data for demo
      setRates({
        rates: {
          common: 60,
          rare: 25,
          epic: 12,
          legendary: 3
        },
        pity_system: {
          legendary_pity: 100,
          epic_pity: 20
        },
        costs: {
          single_pull_gems: 100,
          ten_pull_gems: 900,
          single_pull_tickets: 1,
          ten_pull_tickets: 9
        }
      });
    }
  };

  const loadPlayerResources = async () => {
    try {
      const response = await api.get('/player/profile');
      const profileData = response.data.profile || response.data;
      const resources = profileData.resources || {};

      setPlayerResources({
        gems: resources.diamonds || resources.diamond || profileData.diamond || 5000,
        tickets: resources.tickets || resources.ticket || profileData.ticket || 20
      });
    } catch (error) {
      console.error('Failed to load player resources:', error);
      // Mock data for demo with generous amounts for testing
      setPlayerResources({ gems: 5000, tickets: 20 });
    }
  };

  const performPull = async (pullType: 'single' | 'ten', currency: 'gems' | 'tickets') => {
    if (pulling) return;
    
    setPulling(true);
    setAnimationPhase('pulling');
    setResults([]);
    setShowResults(false);
    setCurrentReveal(0);

    try {
      const response = await api.post('/gacha/pull', {
        pull_type: pullType,
        currency: currency
      });
      
      const pullResults = pullType === 'single' ? [response.data.result] : response.data.results;
      setResults(pullResults);
      
      // Update player resources
      setPlayerResources(prev => ({
        ...prev,
        [currency]: response.data.remaining_currency
      }));
      
      // Start reveal animation
      setTimeout(() => {
        setAnimationPhase('revealing');
        setShowResults(true);
        startRevealAnimation(pullResults);
      }, 2000);
      
    } catch (error: any) {
      console.error('Failed to perform gacha pull:', error);
      
      // Mock pull for demo
      const mockResults = generateMockResults(pullType === 'ten' ? 10 : 1);
      setResults(mockResults);
      
      // Deduct mock resources
      const cost = pullType === 'single' ? 
        (currency === 'gems' ? 100 : 1) : 
        (currency === 'gems' ? 900 : 9);
      
      setPlayerResources(prev => ({
        ...prev,
        [currency]: Math.max(0, prev[currency] - cost)
      }));
      
      setTimeout(() => {
        setAnimationPhase('revealing');
        setShowResults(true);
        startRevealAnimation(mockResults);
      }, 2000);
    }
  };

  const generateMockResults = (count: number): GachaResult[] => {
    const mockItems = {
      legendary: [
        { id: 'sung_jinwoo', name: 'Sung Jin-Woo', type: 'hunter', description: 'The Shadow Monarch himself!' },
        { id: 'shadow_blade', name: 'Shadow Blade', type: 'weapon', description: 'A legendary weapon of immense power' }
      ],
      epic: [
        { id: 'cha_haein', name: 'Cha Hae-In', type: 'hunter', description: 'S-Rank Hunter with sword mastery' },
        { id: 'demon_sword', name: 'Demon Sword', type: 'weapon', description: 'A powerful demonic weapon' }
      ],
      rare: [
        { id: 'skilled_hunter', name: 'Skilled Hunter', type: 'hunter', description: 'An experienced hunter' },
        { id: 'steel_sword', name: 'Steel Sword', type: 'weapon', description: 'A well-crafted weapon' }
      ],
      common: [
        { id: 'basic_hunter', name: 'Basic Hunter', type: 'hunter', description: 'A novice hunter' },
        { id: 'iron_sword', name: 'Iron Sword', type: 'weapon', description: 'A basic weapon' }
      ]
    };

    const results: GachaResult[] = [];
    
    for (let i = 0; i < count; i++) {
      const rand = Math.random() * 100;
      let rarity: keyof typeof mockItems;
      
      if (rand < 3) rarity = 'legendary';
      else if (rand < 15) rarity = 'epic';
      else if (rand < 40) rarity = 'rare';
      else rarity = 'common';
      
      const items = mockItems[rarity];
      const item = items[Math.floor(Math.random() * items.length)];
      
      results.push({
        ...item,
        rarity,
        is_new: Math.random() > 0.3 // 70% chance of being new
      });
    }
    
    return results;
  };

  const startRevealAnimation = (pullResults: GachaResult[]) => {
    let index = 0;
    const revealInterval = setInterval(() => {
      setCurrentReveal(index);
      index++;
      
      if (index >= pullResults.length) {
        clearInterval(revealInterval);
        setTimeout(() => {
          setPulling(false);
          setAnimationPhase('idle');
        }, 1000);
      }
    }, 800);
  };

  const getRarityColor = (rarity: string) => {
    const colors = {
      common: 'from-gray-500 to-gray-600',
      rare: 'from-blue-500 to-blue-600',
      epic: 'from-purple-500 to-purple-600',
      legendary: 'from-yellow-500 to-yellow-600'
    };
    return colors[rarity as keyof typeof colors] || colors.common;
  };

  const getRarityBorder = (rarity: string) => {
    const colors = {
      common: 'border-gray-400',
      rare: 'border-blue-400',
      epic: 'border-purple-400',
      legendary: 'border-yellow-400'
    };
    return colors[rarity as keyof typeof colors] || colors.common;
  };

  const getCharacterImageByRarity = (rarity: string) => {
    const rarityKey = rarity.toUpperCase() as keyof typeof CHARACTER_RARITY;
    const characters = CHARACTER_RARITY[rarityKey];
    if (characters && characters.length > 0) {
      return characters[Math.floor(Math.random() * characters.length)];
    }
    return getRandomCharacter();
  };

  const canAfford = (pullType: 'single' | 'ten', currency: 'gems' | 'tickets') => {
    if (!rates || !rates.costs) return false;

    // Provide default values if rates properties are undefined
    const defaultCosts = {
      single_pull_gems: 300,
      single_pull_tickets: 1,
      ten_pull_gems: 2700,
      ten_pull_tickets: 10
    };

    const costKey = `single_pull_${currency}` as keyof typeof rates.costs;
    const tenCostKey = `ten_pull_${currency}` as keyof typeof rates.costs;

    const cost = pullType === 'single' ?
      (rates.costs[costKey] || defaultCosts[costKey]) :
      (rates.costs[tenCostKey] || defaultCosts[tenCostKey]);

    return playerResources[currency] >= cost;
  };

  const resetResults = () => {
    setResults([]);
    setShowResults(false);
    setCurrentReveal(0);
    setAnimationPhase('idle');
  };

  return (
    <GameBackground variant="gacha">
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 text-white">🎲 Gacha Summons</h1>
          <p className="text-purple-300 text-lg">Summon powerful hunters and legendary weapons!</p>
        </div>

        {/* Player Resources */}
        <div className="flex justify-center gap-6 mb-8">
          <div className="card bg-gradient-to-r from-purple-800/20 to-purple-900/20 border-purple-500/30 px-6 py-3">
            <div className="flex items-center">
              <GemIcon className="w-6 h-6 text-purple-400 mr-2" />
              <span className="text-white font-semibold">{playerResources.gems.toLocaleString()}</span>
              <span className="text-gray-400 ml-1">Gems</span>
            </div>
          </div>
          <div className="card bg-gradient-to-r from-yellow-800/20 to-yellow-900/20 border-yellow-500/30 px-6 py-3">
            <div className="flex items-center">
              <TicketIcon className="w-6 h-6 text-yellow-400 mr-2" />
              <span className="text-white font-semibold">{playerResources.tickets}</span>
              <span className="text-gray-400 ml-1">Tickets</span>
            </div>
          </div>
        </div>

        {/* Gacha Animation Area */}
        <div className="card mb-8 min-h-96 flex items-center justify-center">
          {animationPhase === 'idle' && !showResults && (
            <div className="text-center">
              <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center">
                <SparklesIcon className="w-16 h-16 text-white" />
              </div>
              <p className="text-gray-400 text-lg">Choose your summon type below</p>
            </div>
          )}

          {animationPhase === 'pulling' && (
            <div className="text-center">
              <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center animate-spin">
                <SparklesIcon className="w-16 h-16 text-white" />
              </div>
              <p className="text-white text-xl font-semibold animate-pulse">Summoning...</p>
            </div>
          )}

          {showResults && (
            <div className="w-full">
              <h3 className="text-2xl font-bold text-center mb-6 text-white">Summon Results!</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {results.map((result, index) => (
                  <div
                    key={index}
                    className={`card bg-gradient-to-br ${getRarityColor(result.rarity)} ${getRarityBorder(result.rarity)} border-2 transform transition-all duration-500 ${
                      index <= currentReveal ? 'scale-100 opacity-100' : 'scale-75 opacity-50'
                    } ${index === currentReveal ? 'animate-bounce' : ''}`}
                  >
                    <div className="text-center p-4">
                      <div className="w-16 h-16 mx-auto mb-3">
                        {result.type === 'hunter' ? (
                          <img
                            src={getCharacterImageByRarity(result.rarity)}
                            alt={result.name}
                            className={`w-full h-full character-image rarity-${result.rarity.toLowerCase()}-glow object-cover`}
                          />
                        ) : (
                          <div className="w-full h-full rounded-full bg-white/20 flex items-center justify-center">
                            <GiftIcon className="w-8 h-8 text-white" />
                          </div>
                        )}
                      </div>
                      <h4 className="font-bold text-white text-sm mb-1">{result.name}</h4>
                      <p className="text-xs text-white/80 capitalize">{result.rarity}</p>
                      {result.is_new && (
                        <div className="mt-2">
                          <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">NEW!</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              
              {currentReveal >= results.length - 1 && (
                <div className="text-center mt-6">
                  <button
                    onClick={resetResults}
                    className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition-colors text-white"
                  >
                    Summon Again
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Summon Options */}
        {!showResults && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Single Pull */}
            <div className="card">
              <h3 className="text-xl font-bold mb-4 text-center text-white">Single Summon</h3>
              <div className="space-y-4">
                <button
                  onClick={() => performPull('single', 'gems')}
                  disabled={pulling || !canAfford('single', 'gems')}
                  className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center text-white"
                >
                  <GemIcon className="w-5 h-5 mr-2" />
                  {rates?.costs?.single_pull_gems || 300} Gems
                </button>
                
                <button
                  onClick={() => performPull('single', 'tickets')}
                  disabled={pulling || !canAfford('single', 'tickets')}
                  className="w-full bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center text-white"
                >
                  <TicketIcon className="w-5 h-5 mr-2" />
                  {rates?.costs?.single_pull_tickets || 1} Ticket
                </button>
              </div>
            </div>

            {/* Ten Pull */}
            <div className="card border-yellow-500/30">
              <h3 className="text-xl font-bold mb-4 text-center text-white">10x Summon</h3>
              <p className="text-sm text-yellow-300 text-center mb-4">Guaranteed Rare or better!</p>
              <div className="space-y-4">
                <button
                  onClick={() => performPull('ten', 'gems')}
                  disabled={pulling || !canAfford('ten', 'gems')}
                  className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center text-white"
                >
                  <GemIcon className="w-5 h-5 mr-2" />
                  {rates?.costs?.ten_pull_gems || 2700} Gems
                </button>
                
                <button
                  onClick={() => performPull('ten', 'tickets')}
                  disabled={pulling || !canAfford('ten', 'tickets')}
                  className="w-full bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center text-white"
                >
                  <TicketIcon className="w-5 h-5 mr-2" />
                  {rates?.costs?.ten_pull_tickets || 10} Tickets
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Rates Information */}
        {rates && (
          <div className="card">
            <h3 className="text-xl font-bold mb-4 text-white">Summon Rates</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">{rates.rates.legendary}%</div>
                <div className="text-sm text-gray-400">Legendary</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">{rates.rates.epic}%</div>
                <div className="text-sm text-gray-400">Epic</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{rates.rates.rare}%</div>
                <div className="text-sm text-gray-400">Rare</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-400">{rates.rates.common}%</div>
                <div className="text-sm text-gray-400">Common</div>
              </div>
            </div>
            
            <div className="bg-gray-700/30 rounded-lg p-4">
              <h4 className="font-semibold mb-2 text-white">Pity System</h4>
              <p className="text-sm text-gray-300 mb-1">
                • Guaranteed Legendary after {rates.pity_system.legendary_pity} pulls without one
              </p>
              <p className="text-sm text-gray-300">
                • Guaranteed Epic after {rates.pity_system.epic_pity} pulls without one
              </p>
            </div>
          </div>
        )}
        </div>
      </div>
    </GameBackground>
  );
};

export default GachaPage;