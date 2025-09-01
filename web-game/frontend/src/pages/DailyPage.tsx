import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  CalendarDaysIcon,
  GiftIcon,
  CheckCircleIcon,
  ClockIcon,
  TrophyIcon,
  StarIcon,
  FireIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';

interface Mission {
  id: string;
  name: string;
  description: string;
  type: string;
  target: number;
  progress: number;
  completed: boolean;
  claimed?: boolean;
  rewards: { [key: string]: number };
  expires_at: number;
}

interface LoginReward {
  day: number;
  rewards: { [key: string]: number };
}

interface LoginRewardsData {
  login_streak: number;
  current_day: number;
  can_claim: boolean;
  rewards: LoginReward[];
  next_reward?: LoginReward;
}

const DailyPage: React.FC = () => {
  const { user } = useAuth();
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loginRewards, setLoginRewards] = useState<LoginRewardsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [activeTab, setActiveTab] = useState<'missions' | 'login' | 'achievements'>('missions');

  useEffect(() => {
    if (user) {
      loadDailyData();
    }
  }, [user]);

  const loadDailyData = async () => {
    try {
      const [missionsResponse, loginResponse] = await Promise.all([
        apiService.get('/daily/missions'),
        apiService.get('/daily/login-rewards')
      ]);
      
      setMissions(missionsResponse.data.missions);
      setLoginRewards(loginResponse.data);
    } catch (error) {
      console.error('Failed to load daily data:', error);
      toast.error('Failed to load daily data');
    } finally {
      setLoading(false);
    }
  };

  const claimMissionReward = async (missionId: string) => {
    try {
      setClaiming(true);
      const response = await apiService.post(`/daily/missions/${missionId}/claim`);
      toast.success(response.data.message);
      loadDailyData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to claim reward');
    } finally {
      setClaiming(false);
    }
  };

  const claimLoginReward = async () => {
    try {
      setClaiming(true);
      const response = await apiService.post('/daily/login-rewards/claim');
      toast.success(response.data.message);
      loadDailyData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to claim login reward');
    } finally {
      setClaiming(false);
    }
  };

  const formatTimeRemaining = (expiresAt: number) => {
    const now = Math.floor(Date.now() / 1000);
    const remaining = expiresAt - now;
    
    if (remaining <= 0) return 'Expired';
    
    const hours = Math.floor(remaining / 3600);
    const minutes = Math.floor((remaining % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getMissionTypeIcon = (type: string) => {
    switch (type) {
      case 'battle': return <FireIcon className="w-5 h-5 text-red-500" />;
      case 'gacha': return <GiftIcon className="w-5 h-5 text-purple-500" />;
      case 'gates': return <StarIcon className="w-5 h-5 text-blue-500" />;
      case 'skills': return <StarIcon className="w-5 h-5 text-yellow-500" />;
      case 'upgrade': return <TrophyIcon className="w-5 h-5 text-green-500" />;
      case 'worldboss': return <FireIcon className="w-5 h-5 text-orange-500" />;
      case 'arena': return <TrophyIcon className="w-5 h-5 text-red-400" />;
      default: return <StarIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const renderRewards = (rewards: { [key: string]: number }) => {
    const rewardIcons: { [key: string]: string } = {
      gold: '🪙',
      diamonds: '💎',
      crystals: '💠',
      stones: '🪨',
      tos: '👤',
      tickets: '🎫',
      premiumT: '🎟️',
      xp: '⭐',
      skill_points: '🔮',
      arena_points: '🏆',
      stamina: '⚡'
    };

    return (
      <div className="flex flex-wrap gap-2">
        {Object.entries(rewards).map(([resource, amount]) => (
          <span key={resource} className="bg-arise-purple/20 text-arise-purple px-2 py-1 rounded text-sm font-semibold">
            {rewardIcons[resource] || '🎁'} {amount.toLocaleString()}
          </span>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading daily content...</p>
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
            <h1 className="text-4xl font-bold mb-4 text-white">📅 Daily Activities</h1>
            <p className="text-gray-400">Complete missions and claim daily rewards</p>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8 space-x-2">
            <button
              onClick={() => setActiveTab('missions')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'missions'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🎯 Daily Missions
            </button>
            <button
              onClick={() => setActiveTab('login')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'login'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🎁 Login Rewards
            </button>
            <button
              onClick={() => setActiveTab('achievements')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'achievements'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🏆 Achievements
            </button>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'missions' && (
              <div className="space-y-6">
                <div className="card">
                  <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                    <CalendarDaysIcon className="w-6 h-6 mr-2 text-arise-purple" />
                    Today's Missions
                  </h2>
                  
                  {missions.length === 0 ? (
                    <div className="text-center py-8">
                      <CalendarDaysIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-400">No missions available today</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {missions.map((mission) => (
                        <div key={mission.id} className="bg-gray-700 rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center">
                              {getMissionTypeIcon(mission.type)}
                              <div className="ml-3">
                                <h3 className="text-white font-semibold">{mission.name}</h3>
                                <p className="text-gray-400 text-sm">{mission.description}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-gray-400 flex items-center">
                                <ClockIcon className="w-3 h-3 mr-1" />
                                {formatTimeRemaining(mission.expires_at)}
                              </div>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="mb-3">
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-400">Progress</span>
                              <span className="text-white">{mission.progress}/{mission.target}</span>
                            </div>
                            <div className="stat-bar">
                              <div 
                                className="stat-fill xp-bar"
                                style={{ width: `${Math.min((mission.progress / mission.target) * 100, 100)}%` }}
                              ></div>
                            </div>
                          </div>

                          {/* Rewards */}
                          <div className="mb-4">
                            <span className="text-gray-400 text-sm">Rewards:</span>
                            <div className="mt-2">
                              {renderRewards(mission.rewards)}
                            </div>
                          </div>

                          {/* Action Button */}
                          <div className="flex justify-end">
                            {mission.claimed ? (
                              <span className="text-green-400 font-semibold flex items-center">
                                <CheckCircleIcon className="w-4 h-4 mr-2" />
                                Claimed
                              </span>
                            ) : mission.completed ? (
                              <button
                                onClick={() => claimMissionReward(mission.id)}
                                disabled={claiming}
                                className="btn-primary disabled:opacity-50"
                              >
                                <GiftIcon className="w-4 h-4 mr-2" />
                                Claim Reward
                              </button>
                            ) : (
                              <span className="text-gray-400 text-sm">
                                {mission.progress}/{mission.target} completed
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'login' && loginRewards && (
              <div className="space-y-6">
                <div className="card">
                  <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                    <GiftIcon className="w-6 h-6 mr-2 text-arise-gold" />
                    Daily Login Rewards
                  </h2>
                  
                  <div className="text-center mb-6">
                    <div className="text-3xl font-bold text-white mb-2">
                      Day {loginRewards.current_day} of 7
                    </div>
                    <div className="text-gray-400">
                      Login Streak: {loginRewards.login_streak} days
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-7 gap-4 mb-6">
                    {loginRewards.rewards.map((reward, index) => {
                      const isToday = reward.day === loginRewards.current_day;
                      const isPast = reward.day < loginRewards.current_day || 
                                   (reward.day === loginRewards.current_day && !loginRewards.can_claim);
                      
                      return (
                        <div
                          key={reward.day}
                          className={`rounded-lg p-4 text-center border-2 transition-colors ${
                            isToday && loginRewards.can_claim
                              ? 'border-arise-gold bg-arise-gold/20 animate-pulse'
                              : isPast
                              ? 'border-green-500 bg-green-500/20'
                              : 'border-gray-600 bg-gray-700'
                          }`}
                        >
                          <div className="text-lg font-bold text-white mb-2">
                            Day {reward.day}
                          </div>
                          <div className="space-y-1">
                            {renderRewards(reward.rewards)}
                          </div>
                          {isPast && (
                            <div className="mt-2">
                              <CheckCircleIcon className="w-5 h-5 text-green-400 mx-auto" />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {loginRewards.can_claim && (
                    <div className="text-center">
                      <button
                        onClick={claimLoginReward}
                        disabled={claiming}
                        className="btn-primary text-lg px-8 py-3 disabled:opacity-50"
                      >
                        <GiftIcon className="w-5 h-5 mr-2" />
                        Claim Day {loginRewards.current_day} Reward
                      </button>
                    </div>
                  )}

                  {!loginRewards.can_claim && (
                    <div className="text-center">
                      <p className="text-gray-400">
                        Come back tomorrow for your next login reward!
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'achievements' && (
              <div className="card">
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                  <TrophyIcon className="w-6 h-6 mr-2 text-arise-gold" />
                  Achievements
                </h2>
                
                <div className="text-center py-12">
                  <TrophyIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">Achievements Coming Soon</h3>
                  <p className="text-gray-400">
                    Track your progress and unlock special rewards for completing challenges!
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default DailyPage;
