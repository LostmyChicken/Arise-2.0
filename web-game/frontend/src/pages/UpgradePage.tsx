import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  ArrowUpIcon,
  StarIcon,
  SparklesIcon,
  CurrencyDollarIcon,
  SparklesIcon as GemIcon,
  BeakerIcon,
  FireIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';

interface UpgradeableItem {
  id: string;
  name: string;
  rarity: string;
  level: number;
  limit_break: number;
  awaken: number;
  base_stats: { [key: string]: number };
  current_stats: { [key: string]: number };
  can_level_up: boolean;
  can_limit_break: boolean;
  can_awaken: boolean;
  quantity?: number;
}

interface UpgradeData {
  hunters: UpgradeableItem[];
  weapons: UpgradeableItem[];
}

interface UpgradeCosts {
  level: { [key: number]: { [key: string]: number } };
  limit_break: { [key: number]: { [key: string]: number } };
  awaken: { [key: number]: { [key: string]: number } };
}

const UpgradePage: React.FC = () => {
  const { user } = useAuth();
  const [upgradeData, setUpgradeData] = useState<UpgradeData | null>(null);
  const [upgradeCosts, setUpgradeCosts] = useState<UpgradeCosts | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [activeTab, setActiveTab] = useState<'hunters' | 'weapons'>('hunters');
  const [selectedItem, setSelectedItem] = useState<UpgradeableItem | null>(null);

  useEffect(() => {
    if (user) {
      loadUpgradeData();
      loadUpgradeCosts();
    }
  }, [user]);

  const loadUpgradeData = async () => {
    try {
      const response = await apiService.get('/upgrade/player-items');
      setUpgradeData(response.data);
    } catch (error) {
      console.error('Failed to load upgrade data:', error);
      toast.error('Failed to load upgrade data');
    } finally {
      setLoading(false);
    }
  };

  const loadUpgradeCosts = async () => {
    try {
      const response = await apiService.get('/upgrade/costs');
      setUpgradeCosts(response.data.costs);
    } catch (error) {
      console.error('Failed to load upgrade costs:', error);
    }
  };

  const performUpgrade = async (itemId: string, itemType: string, upgradeType: string) => {
    try {
      setUpgrading(true);
      const response = await apiService.post('/upgrade/upgrade-item', {
        item_id: itemId,
        item_type: itemType,
        upgrade_type: upgradeType
      });
      
      toast.success(response.data.message);
      loadUpgradeData();
      setSelectedItem(null);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upgrade failed');
    } finally {
      setUpgrading(false);
    }
  };

  const getRarityColor = (rarity: string) => {
    switch (rarity.toLowerCase()) {
      case 'legendary': case 'ssr': return 'text-red-500 bg-red-500/20';
      case 'epic': case 'sr': return 'text-purple-500 bg-purple-500/20';
      case 'rare': case 'r': return 'text-blue-500 bg-blue-500/20';
      case 'common': case 'n': return 'text-green-500 bg-green-500/20';
      default: return 'text-gray-500 bg-gray-500/20';
    }
  };

  const getUpgradeCost = (upgradeType: string, currentLevel: number) => {
    if (!upgradeCosts) return null;
    const nextLevel = currentLevel + 1;
    return upgradeCosts[upgradeType as keyof UpgradeCosts]?.[nextLevel];
  };

  const renderUpgradeModal = () => {
    if (!selectedItem || !upgradeCosts) return null;

    const levelCost = selectedItem.can_level_up ? getUpgradeCost('level', selectedItem.level) : null;
    const limitBreakCost = selectedItem.can_limit_break ? getUpgradeCost('limit_break', selectedItem.limit_break) : null;
    const awakenCost = selectedItem.can_awaken ? getUpgradeCost('awaken', selectedItem.awaken) : null;

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
          <h3 className="text-xl font-bold text-white mb-4">Upgrade {selectedItem.name}</h3>
          
          <div className="space-y-4">
            {/* Current Stats */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-white font-semibold mb-2">Current Stats</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(selectedItem.current_stats).map(([stat, value]) => (
                  <div key={stat} className="flex justify-between">
                    <span className="text-gray-400 capitalize">{stat}:</span>
                    <span className="text-white">{value}</span>
                  </div>
                ))}
              </div>
              <div className="mt-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Level:</span>
                  <span className="text-white">{selectedItem.level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Limit Break:</span>
                  <span className="text-white">{selectedItem.limit_break}/5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Awaken:</span>
                  <span className="text-white">{selectedItem.awaken}/3</span>
                </div>
              </div>
            </div>

            {/* Upgrade Options */}
            <div className="space-y-3">
              {/* Level Up */}
              {selectedItem.can_level_up && levelCost && (
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-white font-semibold flex items-center">
                      <ArrowUpIcon className="w-4 h-4 mr-2 text-green-500" />
                      Level Up ({selectedItem.level} → {selectedItem.level + 1})
                    </h5>
                  </div>
                  <div className="text-sm space-y-1 mb-3">
                    {Object.entries(levelCost).map(([resource, cost]) => (
                      <div key={resource} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{resource}:</span>
                        <span className="text-arise-gold">{cost.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => performUpgrade(selectedItem.id, activeTab === 'hunters' ? 'hunter' : 'weapon', 'level')}
                    disabled={upgrading}
                    className="w-full btn-primary disabled:opacity-50"
                  >
                    Level Up
                  </button>
                </div>
              )}

              {/* Limit Break */}
              {selectedItem.can_limit_break && limitBreakCost && (
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-white font-semibold flex items-center">
                      <StarIcon className="w-4 h-4 mr-2 text-blue-500" />
                      Limit Break ({selectedItem.limit_break} → {selectedItem.limit_break + 1})
                    </h5>
                  </div>
                  <div className="text-sm space-y-1 mb-3">
                    {Object.entries(limitBreakCost).map(([resource, cost]) => (
                      <div key={resource} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{resource}:</span>
                        <span className="text-blue-400">{cost.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => performUpgrade(selectedItem.id, activeTab === 'hunters' ? 'hunter' : 'weapon', 'limit_break')}
                    disabled={upgrading}
                    className="w-full btn-secondary bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    Limit Break
                  </button>
                </div>
              )}

              {/* Awaken */}
              {selectedItem.can_awaken && awakenCost && (
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-white font-semibold flex items-center">
                      <SparklesIcon className="w-4 h-4 mr-2 text-purple-500" />
                      Awaken ({selectedItem.awaken} → {selectedItem.awaken + 1})
                    </h5>
                  </div>
                  <div className="text-sm space-y-1 mb-3">
                    {Object.entries(awakenCost).map(([resource, cost]) => (
                      <div key={resource} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{resource}:</span>
                        <span className="text-purple-400">{cost.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => performUpgrade(selectedItem.id, activeTab === 'hunters' ? 'hunter' : 'weapon', 'awaken')}
                    disabled={upgrading}
                    className="w-full btn-secondary bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
                  >
                    Awaken
                  </button>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => setSelectedItem(null)}
            className="w-full mt-4 btn-secondary bg-gray-600 hover:bg-gray-700"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading upgrade data...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  if (!upgradeData) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 text-lg mb-4">Failed to load upgrade data</p>
            <button onClick={loadUpgradeData} className="btn-primary">
              Retry
            </button>
          </div>
        </div>
      </GameBackground>
    );
  }

  const currentItems = activeTab === 'hunters' ? upgradeData.hunters : upgradeData.weapons;

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 text-white">⚡ Upgrade & Enhancement</h1>
            <p className="text-gray-400">Strengthen your hunters and weapons to reach new heights</p>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8 space-x-2">
            <button
              onClick={() => setActiveTab('hunters')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'hunters'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🦸 Hunters ({upgradeData.hunters.length})
            </button>
            <button
              onClick={() => setActiveTab('weapons')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'weapons'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              ⚔️ Weapons ({upgradeData.weapons.length})
            </button>
          </div>

          {/* Items Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {currentItems.map((item) => (
              <div key={item.id} className="card hover:border-arise-purple/50 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-bold text-white">{item.name}</h3>
                  <span className={`px-2 py-1 rounded text-sm font-bold ${getRarityColor(item.rarity)}`}>
                    {item.rarity}
                  </span>
                </div>

                {/* Current Stats */}
                <div className="bg-gray-700 rounded-lg p-3 mb-4">
                  <h4 className="text-white font-semibold text-sm mb-2">Current Stats</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(item.current_stats).map(([stat, value]) => (
                      <div key={stat} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{stat}:</span>
                        <span className="text-white">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Enhancement Levels */}
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Level:</span>
                    <span className="text-white">{item.level}/10</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Limit Break:</span>
                    <span className="text-blue-400">{item.limit_break}/5</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Awaken:</span>
                    <span className="text-purple-400">{item.awaken}/3</span>
                  </div>
                  {item.quantity && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Quantity:</span>
                      <span className="text-white">{item.quantity}</span>
                    </div>
                  )}
                </div>

                {/* Upgrade Options */}
                <div className="space-y-2">
                  {(item.can_level_up || item.can_limit_break || item.can_awaken) ? (
                    <button
                      onClick={() => setSelectedItem(item)}
                      className="w-full btn-primary"
                    >
                      <ArrowUpIcon className="w-4 h-4 mr-2" />
                      Upgrade Options
                    </button>
                  ) : (
                    <div className="text-center py-2">
                      <span className="text-gray-400 text-sm">Max Level Reached</span>
                    </div>
                  )}
                </div>

                {/* Quick Upgrade Indicators */}
                <div className="flex justify-center space-x-2 mt-3">
                  {item.can_level_up && (
                    <div className="w-2 h-2 bg-green-500 rounded-full" title="Can Level Up"></div>
                  )}
                  {item.can_limit_break && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full" title="Can Limit Break"></div>
                  )}
                  {item.can_awaken && (
                    <div className="w-2 h-2 bg-purple-500 rounded-full" title="Can Awaken"></div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Empty State */}
          {currentItems.length === 0 && (
            <div className="text-center py-12">
              <SparklesIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">
                No {activeTab === 'hunters' ? 'Hunters' : 'Weapons'} Available
              </h3>
              <p className="text-gray-400">
                {activeTab === 'hunters' 
                  ? 'Summon hunters to upgrade them!'
                  : 'Collect weapons to upgrade them!'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Upgrade Modal */}
      {renderUpgradeModal()}
    </GameBackground>
  );
};

export default UpgradePage;
