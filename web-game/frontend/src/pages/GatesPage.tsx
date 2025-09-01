import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  MapIcon,
  BoltIcon,
  HeartIcon,
  TrophyIcon,
  ClockIcon,
  FireIcon,
  BeakerIcon,
  SparklesIcon,
  ArrowRightIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';

interface Gate {
  id: string;
  name: string;
  description: string;
  rank: string;
  element: string;
  max_floors: number;
  stamina_cost: number;
  rewards: {
    gold: { min: number; max: number };
    xp: { min: number; max: number };
    items: string[];
    hunters: string[];
  };
  monsters: Array<{
    name: string;
    hp: number;
    attack: number;
    defense: number;
    level: number;
  }>;
}

interface GateSession {
  gate_id: string;
  current_floor: number;
  start_time: number;
  hp: number;
  mp: number;
  inventory_found: { [key: string]: number };
  monsters_defeated: number;
  floors_cleared: number;
  status: string;
  current_monster?: any;
}

interface PlayerProgress {
  gate_progress: { [key: string]: any };
  current_session: GateSession | null;
  stamina: number;
  max_stamina: number;
}

const GatesPage: React.FC = () => {
  const { user } = useAuth();
  const [gates, setGates] = useState<Gate[]>([]);
  const [playerProgress, setPlayerProgress] = useState<PlayerProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (user) {
      loadGatesData();
      loadPlayerProgress();
    }
  }, [user]);

  const loadGatesData = async () => {
    try {
      const response = await apiService.get('/gates/available');
      setGates(response.data.gates);
    } catch (error) {
      console.error('Failed to load gates:', error);
      toast.error('Failed to load gates data');
    }
  };

  const loadPlayerProgress = async () => {
    try {
      const response = await apiService.get('/gates/player-progress');
      setPlayerProgress(response.data);
    } catch (error) {
      console.error('Failed to load player progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const enterGate = async (gateId: string) => {
    try {
      setActionLoading(true);
      const response = await apiService.post('/gates/enter', { gate_id: gateId });
      toast.success(response.data.message);
      loadPlayerProgress();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to enter gate');
    } finally {
      setActionLoading(false);
    }
  };

  const performAction = async (action: string, target?: string) => {
    try {
      setActionLoading(true);
      const response = await apiService.post('/gates/action', { action, target });
      
      if (response.data.result === 'monster_encounter') {
        toast(response.data.message, { icon: '⚔️' });
      } else if (response.data.result === 'treasure_found') {
        toast.success(response.data.message);
      } else if (response.data.result === 'victory') {
        toast.success('Monster defeated!');
      } else if (response.data.result === 'defeat') {
        toast.error('You were defeated!');
      }
      
      loadPlayerProgress();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  const getRankColor = (rank: string) => {
    switch (rank) {
      case 'S': return 'text-red-500 bg-red-500/20';
      case 'A': return 'text-orange-500 bg-orange-500/20';
      case 'B': return 'text-yellow-500 bg-yellow-500/20';
      case 'C': return 'text-green-500 bg-green-500/20';
      case 'D': return 'text-blue-500 bg-blue-500/20';
      case 'E': return 'text-gray-500 bg-gray-500/20';
      default: return 'text-gray-500 bg-gray-500/20';
    }
  };

  const getElementIcon = (element: string) => {
    switch (element.toLowerCase()) {
      case 'fire': return <FireIcon className="w-5 h-5 text-red-500" />;
      case 'water': case 'ice': return <BeakerIcon className="w-5 h-5 text-blue-500" />;
      case 'earth': return <SparklesIcon className="w-5 h-5 text-green-500" />;
      case 'wind': return <BoltIcon className="w-5 h-5 text-yellow-500" />;
      case 'light': return <SparklesIcon className="w-5 h-5 text-yellow-300" />;
      case 'dark': return <SparklesIcon className="w-5 h-5 text-purple-500" />;
      default: return <SparklesIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading gates...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 text-white">🚪 Gates & Dungeons</h1>
            <p className="text-gray-400">Explore dangerous dungeons and claim their treasures</p>
            
            {playerProgress && (
              <div className="mt-4 flex items-center justify-center space-x-4">
                <div className="bg-arise-purple/20 rounded-lg px-4 py-2">
                  <span className="text-arise-purple font-bold text-lg">{playerProgress.stamina}</span>
                  <span className="text-gray-300 ml-2">/ {playerProgress.max_stamina} Stamina</span>
                </div>
              </div>
            )}
          </div>

          {/* Current Session */}
          {playerProgress?.current_session && (
            <div className="card mb-8 border-arise-purple/50">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center">
                <MapIcon className="w-6 h-6 mr-2 text-arise-purple" />
                Current Exploration
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {gates.find(g => g.id === playerProgress.current_session!.gate_id)?.name}
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Floor:</span>
                      <span className="text-white">{playerProgress.current_session.current_floor}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">HP:</span>
                      <span className="text-red-400">{playerProgress.current_session.hp}/100</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">MP:</span>
                      <span className="text-blue-400">{playerProgress.current_session.mp}/100</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Monsters Defeated:</span>
                      <span className="text-white">{playerProgress.current_session.monsters_defeated}</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  {playerProgress.current_session.status === 'combat' && playerProgress.current_session.current_monster && (
                    <div className="bg-red-600/20 border border-red-500/50 rounded-lg p-4">
                      <h4 className="text-red-400 font-semibold mb-2">In Combat!</h4>
                      <p className="text-white">
                        Fighting: {playerProgress.current_session.current_monster.name}
                      </p>
                      <p className="text-gray-300 text-sm">
                        HP: {playerProgress.current_session.current_monster.current_hp}/{playerProgress.current_session.current_monster.hp}
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => performAction('explore')}
                      disabled={actionLoading || playerProgress.current_session.status === 'combat'}
                      className="btn-primary disabled:opacity-50"
                    >
                      🔍 Explore
                    </button>
                    
                    {playerProgress.current_session.status === 'combat' && (
                      <button
                        onClick={() => performAction('fight')}
                        disabled={actionLoading}
                        className="btn-secondary bg-red-600 hover:bg-red-700 disabled:opacity-50"
                      >
                        ⚔️ Fight
                      </button>
                    )}
                    
                    <button
                      onClick={() => performAction('rest')}
                      disabled={actionLoading || playerProgress.current_session.status === 'combat'}
                      className="btn-secondary disabled:opacity-50"
                    >
                      😴 Rest
                    </button>
                    
                    <button
                      onClick={() => performAction('exit')}
                      disabled={actionLoading}
                      className="btn-secondary bg-gray-600 hover:bg-gray-700 disabled:opacity-50"
                    >
                      🚪 Exit
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Available Gates */}
          {!playerProgress?.current_session && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {gates.map((gate) => (
                <div key={gate.id} className="card hover:border-arise-purple/50 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center">
                      {getElementIcon(gate.element)}
                      <h3 className="text-lg font-bold text-white ml-2">{gate.name}</h3>
                    </div>
                    <span className={`px-2 py-1 rounded text-sm font-bold ${getRankColor(gate.rank)}`}>
                      {gate.rank}-Rank
                    </span>
                  </div>

                  <p className="text-gray-300 text-sm mb-4">{gate.description}</p>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Floors:</span>
                      <span className="text-white">{gate.max_floors}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Stamina Cost:</span>
                      <span className="text-arise-purple font-bold">{gate.stamina_cost}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Element:</span>
                      <span className="text-white">{gate.element}</span>
                    </div>
                  </div>

                  {/* Rewards Preview */}
                  <div className="bg-gray-700 rounded-lg p-3 mb-4">
                    <h4 className="text-white font-semibold text-sm mb-2">Rewards:</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-400">Gold:</span>
                        <span className="text-arise-gold ml-1">
                          {gate.rewards.gold.min.toLocaleString()}-{gate.rewards.gold.max.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">XP:</span>
                        <span className="text-blue-400 ml-1">
                          {gate.rewards.xp.min}-{gate.rewards.xp.max}
                        </span>
                      </div>
                    </div>
                    <div className="mt-2">
                      <span className="text-gray-400 text-xs">Items:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {gate.rewards.items.slice(0, 3).map((item, index) => (
                          <span key={index} className="bg-gray-600 text-xs px-2 py-1 rounded">
                            {item}
                          </span>
                        ))}
                        {gate.rewards.items.length > 3 && (
                          <span className="text-gray-400 text-xs">+{gate.rewards.items.length - 3} more</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Monsters Preview */}
                  <div className="bg-gray-700 rounded-lg p-3 mb-4">
                    <h4 className="text-white font-semibold text-sm mb-2">Monsters:</h4>
                    <div className="space-y-1">
                      {gate.monsters.slice(0, 2).map((monster, index) => (
                        <div key={index} className="flex justify-between text-xs">
                          <span className="text-gray-300">{monster.name}</span>
                          <span className="text-gray-400">Lv.{monster.level}</span>
                        </div>
                      ))}
                      {gate.monsters.length > 2 && (
                        <div className="text-gray-400 text-xs">+{gate.monsters.length - 2} more</div>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => enterGate(gate.id)}
                    disabled={actionLoading || !playerProgress || playerProgress.stamina < gate.stamina_cost}
                    className={`w-full py-2 px-4 rounded-lg font-semibold transition-colors ${
                      !playerProgress || playerProgress.stamina < gate.stamina_cost
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-arise-purple hover:bg-arise-purple/80 text-white'
                    }`}
                  >
                    {!playerProgress || playerProgress.stamina < gate.stamina_cost ? (
                      <div className="flex items-center justify-center">
                        <ExclamationTriangleIcon className="w-4 h-4 mr-2" />
                        Not Enough Stamina
                      </div>
                    ) : (
                      <div className="flex items-center justify-center">
                        <ArrowRightIcon className="w-4 h-4 mr-2" />
                        Enter Gate
                      </div>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {gates.length === 0 && (
            <div className="text-center py-12">
              <MapIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No Gates Available</h3>
              <p className="text-gray-400">Gates are currently being prepared. Check back later!</p>
            </div>
          )}
        </div>
      </div>
    </GameBackground>
  );
};

export default GatesPage;
