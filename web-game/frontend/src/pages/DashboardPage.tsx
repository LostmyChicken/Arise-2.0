import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import { IMAGES, getRandomCharacter } from '../constants/images';
import GameBackground from '../components/GameBackground';
import {
  GiftIcon,
  BookOpenIcon,
  BuildingOfficeIcon,
  TrophyIcon,
  BoltIcon,
  HeartIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,

  TicketIcon
} from '@heroicons/react/24/outline';

// Custom icons since they don't exist in heroicons
const SwordIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

const GemIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

interface PlayerProfile {
  id: string;
  username: string;
  level: number;
  xp: number;
  stats: {
    attack: number;
    defense: number;
    hp: number;
    mp: number;
    precision: number;
  };
  resources: {
    gold: number;
    diamond: number;
    stone: number;
    ticket: number;
    crystals: number;
  };
  points: {
    statPoints: number;
    skillPoints: number;
  };
  current_title?: string;
  guild_id?: string;
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    if (!user) return;

    try {
      const response = await apiService.getPlayerProfile(user.player_id);
      setProfile(response);
    } catch (error: any) {
      console.error('Error loading profile:', error);
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const calculateXPProgress = () => {
    if (!profile) return 0;
    const currentLevelXP = (profile.level - 1) * 100;
    const nextLevelXP = profile.level * 100;
    const progress = ((profile.xp - currentLevelXP) / (nextLevelXP - currentLevelXP)) * 100;
    return Math.max(0, Math.min(100, progress));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">Failed to load profile</p>
          <button onClick={loadProfile} className="btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const quickActions = [
    {
      name: 'Battle',
      description: 'Fight monsters and players',
      icon: SwordIcon,
      href: '/battle',
      color: 'bg-red-600 hover:bg-red-700'
    },
    {
      name: 'Gacha',
      description: 'Pull for rare hunters',
      icon: GiftIcon,
      href: '/gacha',
      color: 'bg-purple-600 hover:bg-purple-700'
    },
    {
      name: 'Story',
      description: 'Continue your journey',
      icon: BookOpenIcon,
      href: '/story',
      color: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      name: 'Guild',
      description: 'Manage your guild',
      icon: BuildingOfficeIcon,
      href: '/guild',
      color: 'bg-green-600 hover:bg-green-700'
    }
  ];

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
            Welcome back, <span className="text-arise-gold">{profile.username}</span>!
          </h1>
          <p className="text-gray-400">Ready to continue your Solo Leveling journey?</p>
        </div>

        {/* Player Stats Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Main Stats */}
          <div className="lg:col-span-2 card">
            <div className="flex items-center mb-6">
              <img
                src={IMAGES.PROFILES.DEFAULT_PROFILE}
                alt="Hunter Profile"
                className="w-16 h-16 profile-image mr-4"
              />
              <div>
                <h2 className="text-xl font-semibold text-white">Hunter Profile</h2>
                <p className="text-arise-gold font-medium">{profile.username}</p>
              </div>
            </div>

            {/* Level and XP */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg font-semibold text-white">Level {profile.level}</span>
                <span className="text-sm text-gray-400">
                  {profile.xp} / {profile.level * 100} XP
                </span>
              </div>
              <div className="stat-bar">
                <div 
                  className="stat-fill xp-bar"
                  style={{ width: `${calculateXPProgress()}%` }}
                ></div>
              </div>
            </div>

            {/* Combat Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <SwordIcon className="h-8 w-8 text-red-400 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{profile.stats.attack}</div>
                <div className="text-sm text-gray-400">Attack</div>
              </div>
              <div className="text-center">
                <ShieldCheckIcon className="h-8 w-8 text-blue-400 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{profile.stats.defense}</div>
                <div className="text-sm text-gray-400">Defense</div>
              </div>
              <div className="text-center">
                <HeartIcon className="h-8 w-8 text-red-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{profile.stats.hp}</div>
                <div className="text-sm text-gray-400">HP</div>
              </div>
              <div className="text-center">
                <BoltIcon className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{profile.stats.mp}</div>
                <div className="text-sm text-gray-400">MP</div>
              </div>
              <div className="text-center">
                <TrophyIcon className="h-8 w-8 text-yellow-400 mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{profile.stats.precision}</div>
                <div className="text-sm text-gray-400">Precision</div>
              </div>
            </div>

            {/* Available Points */}
            {(profile.points.statPoints > 0 || profile.points.skillPoints > 0) && (
              <div className="mt-6 p-4 bg-arise-purple bg-opacity-20 rounded-lg border border-arise-purple">
                <h3 className="text-lg font-semibold text-white mb-2">Available Points</h3>
                <div className="flex items-center space-x-6">
                  {profile.points.statPoints > 0 && (
                    <div>
                      <span className="text-arise-gold font-semibold">{profile.points.statPoints}</span>
                      <span className="text-gray-300 ml-1">Stat Points</span>
                    </div>
                  )}
                  {profile.points.skillPoints > 0 && (
                    <div>
                      <span className="text-arise-purple font-semibold">{profile.points.skillPoints}</span>
                      <span className="text-gray-300 ml-1">Skill Points</span>
                    </div>
                  )}
                  <Link to="/profile" className="btn-primary text-sm px-3 py-1">
                    Upgrade
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Resources */}
          <div className="card">
            <h2 className="text-xl font-semibold text-white mb-4">Resources</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CurrencyDollarIcon className="h-5 w-5 text-yellow-400" />
                  <span className="text-gray-300">Gold</span>
                </div>
                <span className="text-white font-semibold">{profile.resources.gold.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <GemIcon className="h-5 w-5 text-blue-400" />
                  <span className="text-gray-300">Diamonds</span>
                </div>
                <span className="text-white font-semibold">{profile.resources.diamond}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <TicketIcon className="h-5 w-5 text-purple-400" />
                  <span className="text-gray-300">Tickets</span>
                </div>
                <span className="text-white font-semibold">{profile.resources.ticket}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-5 w-5 bg-green-400 rounded-full"></div>
                  <span className="text-gray-300">Crystals</span>
                </div>
                <span className="text-white font-semibold">{profile.resources.crystals}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Link
                  key={action.name}
                  to={action.href}
                  className={`card-hover ${action.color} text-white p-6 text-center`}
                >
                  <Icon className="h-12 w-12 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold mb-2">{action.name}</h3>
                  <p className="text-sm opacity-90">{action.description}</p>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent Activity / News */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
            <div className="space-y-3 text-sm">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-gray-300">Logged in successfully</span>
                <span className="text-gray-500 ml-auto">Just now</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="text-gray-300">Profile loaded</span>
                <span className="text-gray-500 ml-auto">Just now</span>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold text-white mb-4">Game News</h2>
            <div className="space-y-3 text-sm">
              <div>
                <h3 className="text-white font-semibold">🎉 Welcome to Arise Web!</h3>
                <p className="text-gray-400">The Solo Leveling experience is now available in your browser!</p>
              </div>
              <div>
                <h3 className="text-white font-semibold">⚔️ Battle System Active</h3>
                <p className="text-gray-400">Challenge monsters and other players in real-time battles.</p>
              </div>
              <div>
                <h3 className="text-white font-semibold">🎲 Gacha System Ready</h3>
                <p className="text-gray-400">Pull for rare hunters and powerful weapons!</p>
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default DashboardPage;