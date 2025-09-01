import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  UserIcon,
  TrophyIcon,
  HeartIcon,
  BoltIcon,
  ShieldCheckIcon,
  StarIcon,
  BuildingOfficeIcon,
  WrenchScrewdriverIcon as SwordIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';
import { IMAGES } from '../constants/images';

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
  gold: number;
  diamond: number;
  stone: number;
  tos: number;
  crystals: number;
  guild?: string;
  equipped: { [key: string]: any };
  hunters: { [key: string]: number };
  inventory: { [key: string]: number };
  skillPoints: number;
  premium: boolean;
}

const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadProfile();
    }
  }, [user]);

  const loadProfile = async () => {
    try {
      const response = await apiService.getPlayerProfile(user!.player_id);

      // Handle both API response formats
      const profileData = response.profile || response;
      const stats = profileData.stats || {};
      const resources = profileData.resources || {};
      const points = profileData.points || {};

      setProfile({
        id: profileData.id,
        username: profileData.username || user!.username,
        level: profileData.level || 1,
        xp: profileData.xp || 0,
        stats: {
          attack: stats.attack || profileData.attack || 15,
          defense: stats.defense || profileData.defense || 12,
          hp: stats.hp || profileData.hp || 150,
          mp: stats.mp || profileData.mp || 75,
          precision: stats.precision || profileData.precision || 10
        },
        gold: resources.gold || profileData.gold || 10000,
        diamond: resources.diamonds || resources.diamond || profileData.diamond || 100,
        stone: resources.stones || resources.stone || profileData.stone || 50,
        tos: resources.tickets || resources.ticket || profileData.ticket || 10,
        crystals: resources.crystals || profileData.crystals || 25,
        guild: profileData.guild_id,
        equipped: typeof profileData.equipped === 'string' ? JSON.parse(profileData.equipped || '{}') : (profileData.equipped || {}),
        hunters: typeof profileData.hunters === 'string' ? JSON.parse(profileData.hunters || '{}') : (profileData.hunters || {}),
        inventory: typeof profileData.inventory === 'string' ? JSON.parse(profileData.inventory || '{}') : (profileData.inventory || {}),
        skillPoints: points.skillPoints || profileData.skillPoints || 3,
        premium: profileData.premium || false
      });
    } catch (error) {
      console.error('Failed to load profile:', error);
      toast.error('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const calculateXPProgress = () => {
    if (!profile) return 0;
    const xpForNextLevel = profile.level * 100;
    return Math.min((profile.xp / xpForNextLevel) * 100, 100);
  };

  const calculatePowerLevel = () => {
    if (!profile) return 0;
    return profile.stats.attack + profile.stats.defense + profile.stats.hp + profile.stats.mp + profile.stats.precision;
  };

  const getRankString = (powerLevel: number) => {
    if (powerLevel >= 10000) return "S-Rank";
    if (powerLevel >= 5000) return "A-Rank";
    if (powerLevel >= 2500) return "B-Rank";
    if (powerLevel >= 1000) return "C-Rank";
    if (powerLevel >= 500) return "D-Rank";
    return "E-Rank";
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading profile...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  if (!profile) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 text-lg mb-4">Failed to load profile</p>
            <button onClick={loadProfile} className="btn-primary">
              Retry
            </button>
          </div>
        </div>
      </GameBackground>
    );
  }

  const powerLevel = calculatePowerLevel();
  const rankString = getRankString(powerLevel);

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <img
                src={IMAGES.PROFILES.DEFAULT_PROFILE}
                alt="Profile"
                className="w-20 h-20 profile-image mr-4"
              />
              <div>
                <h1 className="text-4xl font-bold text-white">{profile.username}'s Profile</h1>
                {profile.premium && (
                  <div className="flex items-center justify-center mt-2">
                    <StarIcon className="w-5 h-5 text-arise-gold mr-1" />
                    <span className="text-arise-gold font-semibold">Premium Hunter</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Profile Info */}
            <div className="lg:col-span-2 space-y-6">
              {/* Level and XP */}
              <div className="card">
                <h2 className="text-xl font-semibold text-white mb-4">📊 Hunter Status</h2>
                <div className="mb-4">
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

                {/* Guild Info */}
                <div className="mb-4">
                  <div className="flex items-center mb-2">
                    <BuildingOfficeIcon className="w-5 h-5 text-arise-purple mr-2" />
                    <span className="text-white font-semibold">Guild</span>
                  </div>
                  <p className="text-gray-300 ml-7">
                    {profile.guild ? `Member of ${profile.guild}` : 'No Guild'}
                  </p>
                </div>

                {/* Hunter Rank */}
                <div>
                  <div className="flex items-center mb-2">
                    <TrophyIcon className="w-5 h-5 text-arise-gold mr-2" />
                    <span className="text-white font-semibold">Hunter Rank</span>
                  </div>
                  <p className="text-arise-gold font-bold ml-7">
                    🏆 {rankString} - Power Level: {powerLevel.toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Combat Stats */}
              <div className="card">
                <h2 className="text-xl font-semibold text-white mb-4">⚔️ Combat Stats</h2>
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
              </div>
            </div>

            {/* Side Panel */}
            <div className="space-y-6">
              {/* Resources */}
              <div className="card">
                <h2 className="text-xl font-semibold text-white mb-4">💰 Resources</h2>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-300">🪙 Gold:</span>
                    <span className="text-arise-gold font-bold">{profile.gold.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">💎 Diamonds:</span>
                    <span className="text-blue-400 font-bold">{profile.diamond.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">🪨 Stones:</span>
                    <span className="text-gray-400 font-bold">{profile.stone.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">👤 Shadow Traces:</span>
                    <span className="text-purple-400 font-bold">{profile.tos.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Collection Stats */}
              <div className="card">
                <h2 className="text-xl font-semibold text-white mb-4">📊 Collection</h2>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-300">🦸 Hunters:</span>
                    <span className="text-white font-bold">{Object.keys(profile.hunters).length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">⚔️ Items:</span>
                    <span className="text-white font-bold">{Object.keys(profile.inventory).length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">🔮 Skill Points:</span>
                    <span className="text-arise-purple font-bold">{profile.skillPoints}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default ProfilePage;