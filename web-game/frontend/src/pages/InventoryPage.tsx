import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  ArchiveBoxIcon as BackpackIcon,
  CurrencyDollarIcon,
  GiftIcon,
  StarIcon,
  ShieldCheckIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';
import { IMAGES } from '../constants/images';

interface InventoryData {
  gold: number;
  diamond: number;
  stone: number;
  tos: number; // Shadow Traces
  crystals: number;
  ticket: number;
  premiumT: number;
  inventory: { [key: string]: number };
  hunters: { [key: string]: number };
  equipped: { [key: string]: any };
}

const InventoryPage: React.FC = () => {
  const { user } = useAuth();
  const [inventoryData, setInventoryData] = useState<InventoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'items' | 'hunters' | 'shards'>('overview');

  useEffect(() => {
    if (user) {
      loadInventoryData();
    }
  }, [user]);

  const loadInventoryData = async () => {
    try {
      const response = await apiService.getPlayerProfile(user!.player_id);
      setInventoryData({
        gold: response.gold || 0,
        diamond: response.diamond || 0,
        stone: response.stone || 0,
        tos: response.tos || 0,
        crystals: response.crystals || 0,
        ticket: response.ticket || 0,
        premiumT: response.premiumT || 0,
        inventory: JSON.parse(response.inventory || '{}'),
        hunters: JSON.parse(response.hunters || '{}'),
        equipped: JSON.parse(response.equipped || '{}')
      });
    } catch (error) {
      console.error('Failed to load inventory:', error);
      toast.error('Failed to load inventory data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading inventory...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  if (!inventoryData) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 text-lg mb-4">Failed to load inventory</p>
            <button onClick={loadInventoryData} className="btn-primary">
              Retry
            </button>
          </div>
        </div>
      </GameBackground>
    );
  }

  const renderOverview = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Currency Overview */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
          <CurrencyDollarIcon className="w-6 h-6 mr-2 text-arise-gold" />
          💰 WALLET
        </h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-300">🪙 Gold:</span>
            <span className="text-arise-gold font-bold">{inventoryData.gold.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">💎 Diamonds:</span>
            <span className="text-blue-400 font-bold">{inventoryData.diamond.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">🪨 Stones:</span>
            <span className="text-gray-400 font-bold">{inventoryData.stone.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">👤 Shadow Traces:</span>
            <span className="text-purple-400 font-bold">{inventoryData.tos.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">💠 Crystals:</span>
            <span className="text-cyan-400 font-bold">{inventoryData.crystals.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Collection Stats */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
          <BackpackIcon className="w-6 h-6 mr-2 text-arise-purple" />
          📊 Collection Stats
        </h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-300">⚔️ Items:</span>
            <span className="text-white font-bold">{Object.keys(inventoryData.inventory).length}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">🦸 Hunters:</span>
            <span className="text-white font-bold">{Object.keys(inventoryData.hunters).length}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">🎫 Tickets:</span>
            <span className="text-yellow-400 font-bold">{inventoryData.ticket.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">🎟️ Premium Tickets:</span>
            <span className="text-gold-400 font-bold">{inventoryData.premiumT.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 text-white">🎒 {user?.username}'s Inventory</h1>
            <p className="text-gray-400">Your complete collection of items and resources</p>
          </div>

          {/* Tab Navigation */}
          <div className="flex flex-wrap justify-center mb-8 space-x-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'overview'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              📊 Overview
            </button>
            <button
              onClick={() => setActiveTab('items')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'items'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              ⚔️ Items
            </button>
            <button
              onClick={() => setActiveTab('hunters')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'hunters'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🦸 Hunters
            </button>
            <button
              onClick={() => setActiveTab('shards')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'shards'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              💎 Shards
            </button>
          </div>

          {/* Tab Content */}
          <div className="mb-8">
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'items' && (
              <div className="card text-center">
                <h2 className="text-2xl font-bold text-white mb-4">⚔️ Items Collection</h2>
                <p className="text-gray-400">Items system coming soon!</p>
              </div>
            )}
            {activeTab === 'hunters' && (
              <div className="card text-center">
                <h2 className="text-2xl font-bold text-white mb-4">🦸 Hunters Collection</h2>
                <p className="text-gray-400">Hunters gallery coming soon!</p>
              </div>
            )}
            {activeTab === 'shards' && (
              <div className="card text-center">
                <h2 className="text-2xl font-bold text-white mb-4">💎 Shards Collection</h2>
                <p className="text-gray-400">Shards system coming soon!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default InventoryPage;