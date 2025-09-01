import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  TrophyIcon,
  ShieldCheckIcon,
  BoltIcon,
  UserGroupIcon,
  StarIcon,
  FireIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';
import { IMAGES } from '../constants/images';

// Custom SwordIcon
const SwordIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

interface ArenaRanking {
  rank: number;
  player_id: string;
  username: string;
  level: number;
  power_level: number;
  arena_points: number;
  last_active: string;
}

interface ArenaOpponent {
  player_id: string;
  username: string;
  level: number;
  arena_rank: number;
  arena_points: number;
  power_level: number;
  win_chance: number;
  last_active: string;
}

interface PlayerRank {
  arena_rank: number;
  arena_points: number;
  power_level: number;
  current_rank: number;
}

const ArenaPage: React.FC = () => {
  const { user } = useAuth();
  const [rankings, setRankings] = useState<ArenaRanking[]>([]);
  const [opponents, setOpponents] = useState<ArenaOpponent[]>([]);
  const [playerRank, setPlayerRank] = useState<PlayerRank | null>(null);
  const [loading, setLoading] = useState(true);
  const [battling, setBattling] = useState(false);
  const [activeTab, setActiveTab] = useState<'battle' | 'rankings' | 'rewards'>('battle');

  useEffect(() => {
    if (user) {
      loadArenaData();
    }
  }, [user]);

  const loadArenaData = async () => {
    try {
      const [rankingsResponse, opponentsResponse, playerRankResponse] = await Promise.all([
        apiService.get('/arena/rankings'),
        apiService.get('/arena/opponents'),
        apiService.get('/arena/my-rank')
      ]);
      
      setRankings(rankingsResponse.data.rankings);
      setOpponents(opponentsResponse.data.opponents);
      setPlayerRank(playerRankResponse.data);
    } catch (error) {
      console.error('Failed to load arena data:', error);
      toast.error('Failed to load arena data');
    } finally {
      setLoading(false);
    }
  };

  const challengePlayer = async (targetPlayerId: string) => {
    try {
      setBattling(true);
      const response = await apiService.post('/arena/challenge', {
        target_player_id: targetPlayerId
      });
      
      const result = response.data;
      
      if (result.battle_result.challenger_wins) {
        toast.success(`🎉 ${result.message} You dealt ${result.battle_result.damage_dealt.toLocaleString()} damage!`);
      } else {
        toast.error(`💀 ${result.message} You took ${result.battle_result.damage_taken.toLocaleString()} damage!`);
      }
      
      // Refresh data
      loadArenaData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Battle failed');
    } finally {
      setBattling(false);
    }
  };

  const getTierInfo = (points: number) => {
    if (points >= 20000) return { tier: 'Master', color: 'text-red-500', bg: 'bg-red-500/20' };
    if (points >= 10000) return { tier: 'Diamond', color: 'text-blue-400', bg: 'bg-blue-400/20' };
    if (points >= 5000) return { tier: 'Platinum', color: 'text-gray-300', bg: 'bg-gray-300/20' };
    if (points >= 2500) return { tier: 'Gold', color: 'text-yellow-500', bg: 'bg-yellow-500/20' };
    if (points >= 1000) return { tier: 'Silver', color: 'text-gray-400', bg: 'bg-gray-400/20' };
    return { tier: 'Bronze', color: 'text-orange-600', bg: 'bg-orange-600/20' };
  };

  const getWinChanceColor = (chance: number) => {
    if (chance >= 70) return 'text-green-400';
    if (chance >= 50) return 'text-yellow-400';
    if (chance >= 30) return 'text-orange-400';
    return 'text-red-400';
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading arena...</p>
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
            <h1 className="text-4xl font-bold mb-4 text-white">⚔️ Arena</h1>
            <p className="text-gray-400">Test your strength against other hunters</p>
            
            {playerRank && (
              <div className="mt-4 flex items-center justify-center space-x-6">
                <div className="bg-arise-purple/20 rounded-lg px-4 py-2">
                  <span className="text-arise-purple font-bold text-lg">#{playerRank.current_rank || 'Unranked'}</span>
                  <span className="text-gray-300 ml-2">Rank</span>
                </div>
                <div className="bg-arise-gold/20 rounded-lg px-4 py-2">
                  <span className="text-arise-gold font-bold text-lg">{playerRank.arena_points}</span>
                  <span className="text-gray-300 ml-2">Points</span>
                </div>
                <div className="bg-red-500/20 rounded-lg px-4 py-2">
                  <span className="text-red-400 font-bold text-lg">{(playerRank.power_level || 0).toLocaleString()}</span>
                  <span className="text-gray-300 ml-2">Power</span>
                </div>
              </div>
            )}
          </div>

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
              onClick={() => setActiveTab('rankings')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'rankings'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🏆 Rankings
            </button>
            <button
              onClick={() => setActiveTab('rewards')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'rewards'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🎁 Rewards
            </button>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'battle' && (
              <div className="space-y-6">
                <div className="card">
                  <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                    <SwordIcon className="w-6 h-6 mr-2 text-red-500" />
                    Available Opponents
                  </h2>
                  
                  {opponents.length === 0 ? (
                    <div className="text-center py-8">
                      <UserGroupIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-400">No opponents available at your level</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {opponents.map((opponent) => {
                        const tierInfo = getTierInfo(opponent.arena_points);
                        return (
                          <div key={opponent.player_id} className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition-colors">
                            <div className="flex items-center justify-between mb-3">
                              <h3 className="text-white font-semibold">{opponent.username}</h3>
                              <span className={`px-2 py-1 rounded text-xs font-bold ${tierInfo.color} ${tierInfo.bg}`}>
                                {tierInfo.tier}
                              </span>
                            </div>
                            
                            <div className="space-y-2 text-sm mb-4">
                              <div className="flex justify-between">
                                <span className="text-gray-400">Level:</span>
                                <span className="text-white">{opponent.level}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Rank:</span>
                                <span className="text-white">#{opponent.arena_rank}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Power:</span>
                                <span className="text-white">{(opponent.power_level || 0).toLocaleString()}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Win Chance:</span>
                                <span className={`font-bold ${getWinChanceColor(opponent.win_chance)}`}>
                                  {opponent.win_chance}%
                                </span>
                              </div>
                            </div>
                            
                            <button
                              onClick={() => challengePlayer(opponent.player_id)}
                              disabled={battling}
                              className="w-full btn-primary disabled:opacity-50"
                            >
                              {battling ? 'Battling...' : 'Challenge'}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'rankings' && (
              <div className="card">
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                  <TrophyIcon className="w-6 h-6 mr-2 text-arise-gold" />
                  Arena Rankings
                </h2>
                
                {rankings.length === 0 ? (
                  <div className="text-center py-8">
                    <TrophyIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-400">No ranked players yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {rankings.map((ranking, index) => {
                      const tierInfo = getTierInfo(ranking.arena_points);
                      return (
                        <div
                          key={ranking.player_id}
                          className={`flex items-center justify-between p-4 rounded-lg ${
                            index === 0 ? 'bg-arise-gold/20 border border-arise-gold/50' :
                            index === 1 ? 'bg-gray-400/20 border border-gray-400/50' :
                            index === 2 ? 'bg-orange-500/20 border border-orange-500/50' :
                            'bg-gray-700/50'
                          }`}
                        >
                          <div className="flex items-center">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold mr-4 ${
                              index === 0 ? 'bg-arise-gold text-black' :
                              index === 1 ? 'bg-gray-400 text-black' :
                              index === 2 ? 'bg-orange-500 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {ranking.rank}
                            </div>
                            <div>
                              <div className="text-white font-semibold">{ranking.username}</div>
                              <div className="text-sm text-gray-400">Level {ranking.level}</div>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-6">
                            <div className="text-right">
                              <div className="text-white font-bold">{(ranking.power_level || 0).toLocaleString()}</div>
                              <div className="text-sm text-gray-400">Power</div>
                            </div>
                            <div className="text-right">
                              <div className="text-arise-gold font-bold">{ranking.arena_points}</div>
                              <div className="text-sm text-gray-400">Points</div>
                            </div>
                            <div className={`px-3 py-1 rounded text-sm font-bold ${tierInfo.color} ${tierInfo.bg}`}>
                              {tierInfo.tier}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'rewards' && (
              <div className="space-y-6">
                <div className="card">
                  <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                    <StarIcon className="w-6 h-6 mr-2 text-arise-gold" />
                    Ranking Tiers & Rewards
                  </h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[
                      { tier: 'Master', points: '20,000+', color: 'text-red-500', bg: 'bg-red-500/20', rewards: '12,000 Gold, 60 Crystals' },
                      { tier: 'Diamond', points: '10,000+', color: 'text-blue-400', bg: 'bg-blue-400/20', rewards: '8,000 Gold, 40 Crystals' },
                      { tier: 'Platinum', points: '5,000+', color: 'text-gray-300', bg: 'bg-gray-300/20', rewards: '5,000 Gold, 25 Crystals' },
                      { tier: 'Gold', points: '2,500+', color: 'text-yellow-500', bg: 'bg-yellow-500/20', rewards: '3,000 Gold, 15 Crystals' },
                      { tier: 'Silver', points: '1,000+', color: 'text-gray-400', bg: 'bg-gray-400/20', rewards: '2,000 Gold, 10 Crystals' },
                      { tier: 'Bronze', points: '0+', color: 'text-orange-600', bg: 'bg-orange-600/20', rewards: '1,000 Gold, 5 Crystals' }
                    ].map((tier) => (
                      <div key={tier.tier} className={`rounded-lg p-4 ${tier.bg} border border-gray-600`}>
                        <h3 className={`text-lg font-bold ${tier.color} mb-2`}>{tier.tier}</h3>
                        <div className="text-sm space-y-1">
                          <div className="text-gray-300">Points: {tier.points}</div>
                          <div className="text-gray-300">Daily Rewards:</div>
                          <div className="text-white font-semibold">{tier.rewards}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <h2 className="text-xl font-bold text-white mb-4 flex items-center">
                    <FireIcon className="w-5 h-5 mr-2 text-red-500" />
                    Battle Rewards
                  </h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-green-600/20 rounded-lg p-4">
                      <h3 className="text-green-400 font-semibold mb-2">🏆 Victory</h3>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li>• +25 Arena Points (base)</li>
                        <li>• 1,000-5,000 Gold</li>
                        <li>• 100-500 XP</li>
                        <li>• Power difference bonus</li>
                      </ul>
                    </div>
                    
                    <div className="bg-red-600/20 rounded-lg p-4">
                      <h3 className="text-red-400 font-semibold mb-2">💀 Defeat</h3>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li>• -12 Arena Points</li>
                        <li>• No gold/XP reward</li>
                        <li>• Reduced point loss vs stronger opponents</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default ArenaPage;
