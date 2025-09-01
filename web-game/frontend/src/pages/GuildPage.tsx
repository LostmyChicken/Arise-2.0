import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  BuildingOfficeIcon,
  UserGroupIcon,
  TrophyIcon,
  StarIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  StarIcon as CrownIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';

interface Guild {
  id: string;
  name: string;
  description: string;
  owner: string;
  members: string[];
  level: number;
  points: number;
  gates: number;
  image?: string;
  allow_alliances: boolean;
}

interface PlayerProfile {
  guild?: string;
}

const GuildPage: React.FC = () => {
  const { user } = useAuth();
  const [playerGuild, setPlayerGuild] = useState<Guild | null>(null);
  const [availableGuilds, setAvailableGuilds] = useState<Guild[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'my-guild' | 'browse' | 'create'>('my-guild');
  const [searchTerm, setSearchTerm] = useState('');
  const [guildName, setGuildName] = useState('');
  const [guildDescription, setGuildDescription] = useState('');

  useEffect(() => {
    if (user) {
      loadGuildData();
    }
  }, [user]);

  const loadGuildData = async () => {
    try {
      // Load player profile to check guild membership
      const profile = await apiService.getPlayerProfile(user!.player_id);

      if (profile.guild) {
        // Load player's guild details
        const guildResponse = await apiService.get(`/guild/${profile.guild}`);
        setPlayerGuild(guildResponse.data);
      }

      // Load available guilds for browsing
      const guildsResponse = await apiService.get('/guilds');
      setAvailableGuilds(guildsResponse.data.guilds || []);
    } catch (error) {
      console.error('Failed to load guild data:', error);
      // Mock data for demo
      setAvailableGuilds([
        {
          id: 'guild1',
          name: 'Shadow Monarchs',
          description: 'Elite hunters seeking power',
          owner: 'SungJinWoo',
          members: ['member1', 'member2', 'member3'],
          level: 15,
          points: 125000,
          gates: 45,
          allow_alliances: true
        },
        {
          id: 'guild2',
          name: 'Hunters Association',
          description: 'Official hunters guild',
          owner: 'GoGunhee',
          members: ['member1', 'member2'],
          level: 12,
          points: 89000,
          gates: 32,
          allow_alliances: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getTierInfo = (points: number) => {
    if (points >= 1000000) return { tier: 'S-Tier', color: 'text-red-500' };
    if (points >= 500000) return { tier: 'A-Tier', color: 'text-orange-500' };
    if (points >= 250000) return { tier: 'B-Tier', color: 'text-yellow-500' };
    if (points >= 100000) return { tier: 'C-Tier', color: 'text-green-500' };
    if (points >= 50000) return { tier: 'D-Tier', color: 'text-blue-500' };
    return { tier: 'E-Tier', color: 'text-gray-500' };
  };

  const handleJoinGuild = async (guildId: string) => {
    try {
      await apiService.post(`/guild/${guildId}/join`, {});
      toast.success('Guild join request sent!');
      loadGuildData();
    } catch (error) {
      toast.error('Failed to join guild');
    }
  };

  const handleCreateGuild = async (name: string, description: string) => {
    try {
      await apiService.post('/guild/create', { name, description });
      toast.success('Guild created successfully!');
      loadGuildData();
      setActiveTab('my-guild');
    } catch (error) {
      toast.error('Failed to create guild');
    }
  };

  const filteredGuilds = availableGuilds.filter(guild =>
    guild.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    guild.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading guild data...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  const renderMyGuild = () => {
    if (!playerGuild) {
      return (
        <div className="card text-center">
          <BuildingOfficeIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-4">No Guild</h2>
          <p className="text-gray-400 mb-6">You're not a member of any guild yet.</p>
          <div className="space-x-4">
            <button
              onClick={() => setActiveTab('browse')}
              className="btn-primary"
            >
              Browse Guilds
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className="btn-secondary"
            >
              Create Guild
            </button>
          </div>
        </div>
      );
    }

    const tierInfo = getTierInfo(playerGuild.points);

    return (
      <div className="space-y-6">
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-3xl font-bold text-white">{playerGuild.name}</h2>
              <p className="text-gray-400 italic">"{playerGuild.description}"</p>
            </div>
            <div className={`text-2xl font-bold ${tierInfo.color}`}>
              {tierInfo.tier}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <CrownIcon className="w-5 h-5 mr-2 text-arise-gold" />
                Guild Info
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-300">Leader:</span>
                  <span className="text-white font-bold">{playerGuild.owner}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Members:</span>
                  <span className="text-white">{playerGuild.members.length}/50</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <TrophyIcon className="w-5 h-5 mr-2 text-arise-gold" />
                Guild Stats
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-300">Level:</span>
                  <span className="text-white font-bold">{playerGuild.level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Gates Cleared:</span>
                  <span className="text-white font-bold">{playerGuild.gates}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Guild Points:</span>
                  <span className="text-arise-gold font-bold">{playerGuild.points.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Guild Members */}
        <div className="card">
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
            <UserGroupIcon className="w-6 h-6 mr-2 text-arise-purple" />
            Guild Members ({playerGuild.members.length}/50)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {playerGuild.members.map((member, index) => (
              <div key={index} className="bg-gray-700 rounded-lg p-3">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-arise-purple rounded-full flex items-center justify-center mr-3">
                    <span className="text-white font-bold text-sm">{member[0]?.toUpperCase()}</span>
                  </div>
                  <span className="text-white">{member}</span>
                  {member === playerGuild.owner && (
                    <CrownIcon className="w-4 h-4 text-arise-gold ml-2" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderBrowseGuilds = () => (
    <div className="space-y-6">
      {/* Search */}
      <div className="card">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search guilds..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-arise-purple"
            />
          </div>
        </div>
      </div>

      {/* Guild List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredGuilds.map((guild) => {
          const tierInfo = getTierInfo(guild.points);
          return (
            <div key={guild.id} className="card hover:border-arise-purple/50 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white">{guild.name}</h3>
                  <p className="text-gray-400 text-sm italic">"{guild.description}"</p>
                </div>
                <div className={`text-sm font-bold ${tierInfo.color}`}>
                  {tierInfo.tier}
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Leader:</span>
                  <span className="text-white">{guild.owner}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Members:</span>
                  <span className="text-white">{guild.members.length}/50</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Level:</span>
                  <span className="text-white">{guild.level}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Points:</span>
                  <span className="text-arise-gold">{guild.points.toLocaleString()}</span>
                </div>
              </div>

              <button
                onClick={() => handleJoinGuild(guild.id)}
                className="w-full btn-primary"
                disabled={playerGuild !== null}
              >
                {playerGuild ? 'Already in Guild' : 'Request to Join'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderCreateGuild = () => {
    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      if (guildName.trim() && guildDescription.trim()) {
        handleCreateGuild(guildName.trim(), guildDescription.trim());
      }
    };

    return (
      <div className="max-w-2xl mx-auto">
        <div className="card">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">Create New Guild</h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-white font-semibold mb-2">Guild Name</label>
              <input
                type="text"
                value={guildName}
                onChange={(e) => setGuildName(e.target.value)}
                placeholder="Enter guild name..."
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-arise-purple"
                required
              />
            </div>

            <div>
              <label className="block text-white font-semibold mb-2">Guild Description</label>
              <textarea
                value={guildDescription}
                onChange={(e) => setGuildDescription(e.target.value)}
                placeholder="Enter guild description..."
                rows={4}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-arise-purple resize-none"
                required
              />
            </div>

            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-2">Guild Creation Requirements:</h3>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Cost: 10,000 Gold</li>
                <li>• Minimum Level: 10</li>
                <li>• Maximum 50 members</li>
                <li>• Guild name must be unique</li>
              </ul>
            </div>

            <button
              type="submit"
              className="w-full btn-primary"
              disabled={!guildName.trim() || !guildDescription.trim()}
            >
              Create Guild (10,000 Gold)
            </button>
          </form>
        </div>
      </div>
    );
  };

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 text-white">🏰 Guild System</h1>
            <p className="text-gray-400">Join forces with other hunters and conquer the gates together</p>
          </div>

          {/* Tab Navigation */}
          <div className="flex flex-wrap justify-center mb-8 space-x-2">
            <button
              onClick={() => setActiveTab('my-guild')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'my-guild'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🏰 My Guild
            </button>
            <button
              onClick={() => setActiveTab('browse')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'browse'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🔍 Browse Guilds
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'create'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              ➕ Create Guild
            </button>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'my-guild' && renderMyGuild()}
            {activeTab === 'browse' && renderBrowseGuilds()}
            {activeTab === 'create' && renderCreateGuild()}
          </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default GuildPage;