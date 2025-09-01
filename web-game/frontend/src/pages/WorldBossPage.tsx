import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  FireIcon,
  BoltIcon,
  ShieldCheckIcon,
  TrophyIcon,
  ClockIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';

import GameBackground from '../components/GameBackground';
import { IMAGES } from '../constants/images';

// Custom SwordIcon
const SwordIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

interface WorldBoss {
  id: string;
  name: string;
  description: string;
  max_hp: number;
  current_hp: number;
  level: number;
  element: string;
  image: string;
  spawn_time: number;
  despawn_time: number;
  participants: { [key: string]: any };
  rewards: { [key: string]: any };
  status: string;
}

interface WorldBossData {
  boss: WorldBoss | null;
  time_remaining: number;
  hp_percentage: number;
}

interface LeaderboardEntry {
  player_id: string;
  username: string;
  total_damage: number;
  attacks: number;
  last_attack: number;
}

const WorldBossPage: React.FC = () => {
  const { user } = useAuth();
  const [bossData, setBossData] = useState<WorldBossData | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [attacking, setAttacking] = useState(false);
  const [activeTab, setActiveTab] = useState<'battle' | 'leaderboard'>('battle');

  useEffect(() => {
    if (user) {
      loadWorldBossData();
      loadLeaderboard();
      
      // Auto-refresh every 5 seconds
      const interval = setInterval(() => {
        loadWorldBossData();
        if (activeTab === 'leaderboard') {
          loadLeaderboard();
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [user, activeTab]);

  const loadWorldBossData = async () => {
    try {
      const response = await apiService.get('/worldboss/current');
      setBossData(response.data);
    } catch (error) {
      console.error('Failed to load world boss:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadLeaderboard = async () => {
    try {
      const response = await apiService.get('/worldboss/leaderboard');
      setLeaderboard(response.data.leaderboard || []);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    }
  };

  const attackBoss = async () => {
    if (!bossData?.boss || attacking) return;

    setAttacking(true);
    try {
      const response = await apiService.post('/worldboss/attack', {
        damage: 1000, // This would be calculated based on player stats
        skill_used: null
      });

      toast.success(`Dealt ${response.data.damage_dealt.toLocaleString()} damage!`);
      
      if (response.data.boss_defeated) {
        toast.success('🎉 World Boss Defeated! Rewards distributed!');
      }

      loadWorldBossData();
      if (activeTab === 'leaderboard') {
        loadLeaderboard();
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to attack boss');
    } finally {
      setAttacking(false);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const getElementColor = (element: string) => {
    switch (element.toLowerCase()) {
      case 'fire': return 'text-red-500';
      case 'water': case 'ice': return 'text-blue-500';
      case 'earth': return 'text-green-500';
      case 'wind': return 'text-yellow-500';
      case 'light': return 'text-yellow-300';
      case 'dark': return 'text-purple-500';
      default: return 'text-gray-500';
    }
  };

  const getBossImage = (bossId: string) => {
    // Map boss IDs to character images
    const bossImageMap: { [key: string]: string } = {
      'shadow_monarch': IMAGES.CHARACTERS.RYOMEN_SUKUNA,
      'ice_monarch': IMAGES.CHARACTERS.THOMAS_ANDRE,
      'flame_monarch': IMAGES.CHARACTERS.BAEK_YOONHO,
      'beast_monarch': IMAGES.CHARACTERS.CHOI_JONG_IN
    };
    
    return bossImageMap[bossId] || IMAGES.CHARACTERS.GO_GUNHEE;
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading world boss...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  return (
    <GameBackground variant="battle">
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 text-white">🌍 World Boss</h1>
            <p className="text-gray-400">Unite with hunters worldwide to defeat legendary bosses</p>
          </div>

          {!bossData?.boss ? (
            <div className="card text-center">
              <div className="text-6xl mb-4">😴</div>
              <h2 className="text-2xl font-bold text-white mb-4">No Active World Boss</h2>
              <p className="text-gray-400 mb-6">
                World bosses spawn periodically. Check back later or wait for the next spawn!
              </p>
              <button onClick={loadWorldBossData} className="btn-primary">
                Check for Boss
              </button>
            </div>
          ) : (
            <>
              {/* Tab Navigation */}
              <div className="flex justify-center mb-8 space-x-2">
                <button
                  onClick={() => setActiveTab('battle')}
                  className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                    activeTab === 'battle'
                      ? 'bg-arise-purple text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  ⚔️ Battle
                </button>
                <button
                  onClick={() => setActiveTab('leaderboard')}
                  className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                    activeTab === 'leaderboard'
                      ? 'bg-arise-purple text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  🏆 Leaderboard
                </button>
              </div>

              {activeTab === 'battle' && (
                <div className="space-y-6">
                  {/* Boss Info */}
                  <div className="card">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Boss Image */}
                      <div className="text-center">
                        <img
                          src={getBossImage(bossData.boss.id)}
                          alt={bossData.boss.name}
                          className="w-64 h-64 mx-auto character-image boss-glow mb-4"
                        />
                        <h2 className="text-3xl font-bold text-white mb-2">
                          {bossData.boss.name}
                        </h2>
                        <p className="text-gray-400 italic mb-4">
                          "{bossData.boss.description}"
                        </p>
                        <div className="flex items-center justify-center space-x-4">
                          <span className="text-lg font-semibold text-white">
                            Level {bossData.boss.level}
                          </span>
                          <span className={`text-lg font-semibold ${getElementColor(bossData.boss.element)}`}>
                            {bossData.boss.element}
                          </span>
                        </div>
                      </div>

                      {/* Boss Stats */}
                      <div className="space-y-4">
                        {/* HP Bar */}
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-white font-semibold">Boss HP</span>
                            <span className="text-white">
                              {bossData.boss.current_hp.toLocaleString()} / {bossData.boss.max_hp.toLocaleString()}
                            </span>
                          </div>
                          <div className="stat-bar">
                            <div 
                              className="stat-fill hp-bar"
                              style={{ width: `${bossData.hp_percentage}%` }}
                            ></div>
                          </div>
                          <div className="text-center mt-2">
                            <span className="text-lg font-bold text-white">
                              {bossData.hp_percentage.toFixed(1)}% HP Remaining
                            </span>
                          </div>
                        </div>

                        {/* Time Remaining */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <ClockIcon className="w-5 h-5 text-arise-gold mr-2" />
                              <span className="text-white font-semibold">Time Remaining</span>
                            </div>
                            <span className="text-arise-gold font-bold text-lg">
                              {formatTime(bossData.time_remaining)}
                            </span>
                          </div>
                        </div>

                        {/* Participants */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <UserGroupIcon className="w-5 h-5 text-arise-purple mr-2" />
                              <span className="text-white font-semibold">Participants</span>
                            </div>
                            <span className="text-arise-purple font-bold text-lg">
                              {Object.keys(bossData.boss.participants).length}
                            </span>
                          </div>
                        </div>

                        {/* Attack Button */}
                        <button
                          onClick={attackBoss}
                          disabled={attacking || bossData.boss.status !== 'active'}
                          className={`w-full py-4 px-6 rounded-lg font-bold text-lg transition-colors ${
                            attacking || bossData.boss.status !== 'active'
                              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                              : 'bg-red-600 hover:bg-red-700 text-white boss-attack-btn'
                          }`}
                        >
                          {attacking ? (
                            <div className="flex items-center justify-center">
                              <div className="loading-spinner mr-2"></div>
                              Attacking...
                            </div>
                          ) : bossData.boss.status !== 'active' ? (
                            'Boss Defeated'
                          ) : (
                            <div className="flex items-center justify-center">
                              <SwordIcon className="w-6 h-6 mr-2" />
                              ATTACK BOSS
                            </div>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Rewards Preview */}
                  <div className="card">
                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                      <TrophyIcon className="w-6 h-6 mr-2 text-arise-gold" />
                      Potential Rewards
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl mb-2">🪙</div>
                        <div className="text-sm text-gray-400">Gold</div>
                        <div className="text-arise-gold font-bold">
                          {bossData.boss.rewards.gold?.min.toLocaleString()} - {bossData.boss.rewards.gold?.max.toLocaleString()}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-2">💎</div>
                        <div className="text-sm text-gray-400">Diamonds</div>
                        <div className="text-blue-400 font-bold">
                          {bossData.boss.rewards.diamonds?.min} - {bossData.boss.rewards.diamonds?.max}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-2">💠</div>
                        <div className="text-sm text-gray-400">Crystals</div>
                        <div className="text-cyan-400 font-bold">
                          {bossData.boss.rewards.crystals?.min} - {bossData.boss.rewards.crystals?.max}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-2">👤</div>
                        <div className="text-sm text-gray-400">Shadow Traces</div>
                        <div className="text-purple-400 font-bold">
                          {bossData.boss.rewards.tos?.min} - {bossData.boss.rewards.tos?.max}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'leaderboard' && (
                <div className="card">
                  <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
                    <TrophyIcon className="w-6 h-6 mr-2 text-arise-gold" />
                    Damage Leaderboard
                  </h3>
                  
                  {leaderboard.length === 0 ? (
                    <div className="text-center py-8">
                      <UserGroupIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-400">No participants yet. Be the first to attack!</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {leaderboard.map((entry, index) => (
                        <div
                          key={entry.player_id}
                          className={`flex items-center justify-between p-4 rounded-lg ${
                            index === 0 ? 'bg-arise-gold/20 border border-arise-gold/50' :
                            index === 1 ? 'bg-gray-600/50 border border-gray-500/50' :
                            index === 2 ? 'bg-orange-600/20 border border-orange-500/50' :
                            'bg-gray-700/50'
                          }`}
                        >
                          <div className="flex items-center">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold mr-4 ${
                              index === 0 ? 'bg-arise-gold text-black' :
                              index === 1 ? 'bg-gray-400 text-black' :
                              index === 2 ? 'bg-orange-500 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {index + 1}
                            </div>
                            <div>
                              <div className="text-white font-semibold">{entry.username}</div>
                              <div className="text-sm text-gray-400">{entry.attacks} attacks</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-white font-bold">
                              {entry.total_damage.toLocaleString()}
                            </div>
                            <div className="text-sm text-gray-400">damage</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </GameBackground>
  );
};

export default WorldBossPage;
