import React, { useState, useEffect } from 'react';
import {
  HeartIcon,
  ShieldCheckIcon,
  FireIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import { IMAGES, getRandomBoss, getRandomCharacter } from '../constants/images';
import GameBackground from '../components/GameBackground';

// Custom SwordIcon for attacks
const SwordIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

interface Monster {
  id: number;
  name: string;
  level: number;
  rank: string;
  health: number;
  attack: number;
  defense: number;
  experience_reward: number;
  gold_reward: number;
  image_url: string;
}

interface BattleState {
  battle_id: number;
  status: string;
  turn: number;
  hunter_health: number;
  monster_health: number;
  hunter: any;
  monster: any;
  battle_log: any[];
}

const BattlePage: React.FC = () => {
  const { user } = useAuth();
  const [monsters, setMonsters] = useState<Monster[]>([]);
  const [battleState, setBattleState] = useState<BattleState | null>(null);
  const [loading, setLoading] = useState(false);
  const [battleLog, setBattleLog] = useState<string[]>([]);
  const [animating, setAnimating] = useState(false);

  useEffect(() => {
    loadMonsters();
  }, []);

  const loadMonsters = async () => {
    try {
      const response = await api.get('/battle/monsters');
      setMonsters(response.data.monsters);
    } catch (error) {
      console.error('Failed to load monsters:', error);
      // Mock data for demo
      setMonsters([
        {
          id: 1,
          name: "Goblin Warrior",
          level: 5,
          rank: "E",
          health: 80,
          attack: 15,
          defense: 8,
          experience_reward: 25,
          gold_reward: 50,
          image_url: "/images/monsters/goblin.png"
        },
        {
          id: 2,
          name: "Orc Berserker",
          level: 8,
          rank: "D",
          health: 120,
          attack: 25,
          defense: 12,
          experience_reward: 40,
          gold_reward: 80,
          image_url: "/images/monsters/orc.png"
        },
        {
          id: 3,
          name: "Shadow Beast",
          level: 12,
          rank: "C",
          health: 180,
          attack: 35,
          defense: 18,
          experience_reward: 60,
          gold_reward: 120,
          image_url: "/images/monsters/shadow_beast.png"
        }
      ]);
    }
  };

  const startBattle = async (monsterId: number) => {
    setLoading(true);
    try {
      const response = await api.post('/battle/start', {
        monster_id: monsterId
      });
      
      setBattleState(response.data);
      setBattleLog([response.data.message]);
    } catch (error: any) {
      console.error('Failed to start battle:', error);
      setBattleLog([error.response?.data?.detail || 'Failed to start battle']);
      
      // Mock battle for demo
      const monster = monsters.find(m => m.id === monsterId);
      if (monster) {
        setBattleState({
          battle_id: Date.now(),
          status: 'active',
          turn: 1,
          hunter_health: 100,
          monster_health: monster.health,
          hunter: {
            id: 1,
            name: user?.username || 'Hunter',
            level: 10,
            max_health: 100,
            attack: 20,
            defense: 10
          },
          monster: {
            id: monster.id,
            name: monster.name,
            level: monster.level,
            rank: monster.rank,
            max_health: monster.health,
            attack: monster.attack,
            defense: monster.defense
          },
          battle_log: []
        });
        setBattleLog([`Battle started against ${monster.name}!`]);
      }
    }
    setLoading(false);
  };

  const performAction = async (action: string) => {
    if (!battleState || animating) return;
    
    setAnimating(true);
    try {
      const response = await api.post(`/battle/${battleState.battle_id}/action`, {
        action: action
      });
      
      setBattleState(response.data);
      
      // Add battle actions to log
      if (response.data.last_actions) {
        const newLogs = response.data.last_actions.map((action: any) => action.message);
        setBattleLog(prev => [...prev, ...newLogs]);
      }
      
      // Check if battle ended
      if (response.data.status !== 'active') {
        if (response.data.rewards) {
          setBattleLog(prev => [...prev, 
            `Battle ended! Rewards: ${response.data.rewards.experience} EXP, ${response.data.rewards.gold} Gold`
          ]);
        }
      }
      
    } catch (error: any) {
      console.error('Failed to perform action:', error);
      
      // Mock battle action for demo
      const newState = { ...battleState };
      let actionMessage = '';
      
      if (action === 'attack') {
        const damage = Math.floor(Math.random() * 20) + 10;
        newState.monster_health = Math.max(0, newState.monster_health - damage);
        actionMessage = `You attack ${newState.monster.name} for ${damage} damage!`;
        
        if (newState.monster_health <= 0) {
          newState.status = 'won';
          setBattleLog(prev => [...prev, actionMessage, 'Victory! You defeated the monster!']);
        } else {
          // Monster counter-attack
          const monsterDamage = Math.floor(Math.random() * 15) + 5;
          newState.hunter_health = Math.max(0, newState.hunter_health - monsterDamage);
          setBattleLog(prev => [...prev, actionMessage, `${newState.monster.name} attacks you for ${monsterDamage} damage!`]);
          
          if (newState.hunter_health <= 0) {
            newState.status = 'lost';
            setBattleLog(prev => [...prev, 'Defeat! You have been defeated...']);
          }
        }
      } else if (action === 'skill') {
        const damage = Math.floor(Math.random() * 30) + 20;
        newState.monster_health = Math.max(0, newState.monster_health - damage);
        actionMessage = `You use Shadow Strike for ${damage} damage!`;
        setBattleLog(prev => [...prev, actionMessage]);
      } else if (action === 'item') {
        const heal = Math.min(50, 100 - newState.hunter_health);
        newState.hunter_health += heal;
        actionMessage = `You use a Health Potion and recover ${heal} HP!`;
        setBattleLog(prev => [...prev, actionMessage]);
      } else if (action === 'flee') {
        newState.status = 'fled';
        setBattleLog(prev => [...prev, 'You fled from battle!']);
      }
      
      newState.turn += 1;
      setBattleState(newState);
    }
    
    setTimeout(() => setAnimating(false), 1000);
  };

  const resetBattle = () => {
    setBattleState(null);
    setBattleLog([]);
  };

  const getRankColor = (rank: string) => {
    const colors = {
      'E': 'text-gray-400',
      'D': 'text-green-400',
      'C': 'text-blue-400',
      'B': 'text-purple-400',
      'A': 'text-yellow-400',
      'S': 'text-red-400'
    };
    return colors[rank as keyof typeof colors] || 'text-gray-400';
  };

  const getHealthPercentage = (current: number, max: number) => {
    return Math.max(0, (current / max) * 100);
  };

  if (battleState) {
    return (
      <div className="min-h-screen p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Battle Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-2 text-white">⚔️ Battle Arena</h1>
            <p className="text-purple-300">Turn {battleState.turn}</p>
          </div>

          {/* Battle Field */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Hunter */}
            <div className="card bg-gradient-to-br from-blue-800/20 to-blue-900/20 border-blue-500/30">
              <div className="text-center mb-4">
                <div className={`w-24 h-24 mx-auto mb-4 rounded-full bg-blue-600 flex items-center justify-center ${animating ? 'animate-pulse' : ''}`}>
                  <SwordIcon className="w-12 h-12 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">{battleState.hunter.name}</h3>
                <p className="text-blue-300">Level {battleState.hunter.level}</p>
              </div>
              
              {/* Hunter Health */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1 text-gray-300">
                  <span>Health</span>
                  <span>{battleState.hunter_health}/{battleState.hunter.max_health}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className="bg-green-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${getHealthPercentage(battleState.hunter_health, battleState.hunter.max_health)}%` }}
                  ></div>
                </div>
              </div>

              {/* Hunter Stats */}
              <div className="grid grid-cols-2 gap-2 text-sm text-gray-300">
                <div className="flex items-center">
                  <SwordIcon className="w-4 h-4 mr-1 text-red-400" />
                  <span>{battleState.hunter.attack}</span>
                </div>
                <div className="flex items-center">
                  <ShieldCheckIcon className="w-4 h-4 mr-1 text-blue-400" />
                  <span>{battleState.hunter.defense}</span>
                </div>
              </div>
            </div>

            {/* Battle Actions */}
            <div className="card bg-gradient-to-br from-purple-800/20 to-purple-900/20 border-purple-500/30">
              <h3 className="text-xl font-bold mb-4 text-center text-white">Actions</h3>
              
              {battleState.status === 'active' ? (
                <div className="space-y-3">
                  <button
                    onClick={() => performAction('attack')}
                    disabled={animating}
                    className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center text-white"
                  >
                    <SwordIcon className="w-5 h-5 mr-2" />
                    Attack
                  </button>
                  
                  <button
                    onClick={() => performAction('skill')}
                    disabled={animating}
                    className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center text-white"
                  >
                    <SparklesIcon className="w-5 h-5 mr-2" />
                    Shadow Strike (20 MP)
                  </button>
                  
                  <button
                    onClick={() => performAction('item')}
                    disabled={animating}
                    className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center text-white"
                  >
                    <HeartIcon className="w-5 h-5 mr-2" />
                    Health Potion (50 Gold)
                  </button>
                  
                  <button
                    onClick={() => performAction('flee')}
                    disabled={animating}
                    className="w-full bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors text-white"
                  >
                    Flee Battle
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-xl mb-4 text-white">
                    {battleState.status === 'won' ? '🎉 Victory!' : 
                     battleState.status === 'lost' ? '💀 Defeat!' : 
                     battleState.status === 'fled' ? '🏃 Fled!' : 'Battle Ended'}
                  </p>
                  <button
                    onClick={resetBattle}
                    className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition-colors text-white"
                  >
                    New Battle
                  </button>
                </div>
              )}
            </div>

            {/* Monster */}
            <div className="card bg-gradient-to-br from-red-800/20 to-red-900/20 border-red-500/30">
              <div className="text-center mb-4">
                <div className={`w-24 h-24 mx-auto mb-4 rounded-full bg-red-600 flex items-center justify-center ${animating ? 'animate-bounce' : ''}`}>
                  <FireIcon className="w-12 h-12 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">{battleState.monster.name}</h3>
                <p className={`${getRankColor(battleState.monster.rank)} font-semibold`}>
                  Rank {battleState.monster.rank} • Level {battleState.monster.level}
                </p>
              </div>
              
              {/* Monster Health */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1 text-gray-300">
                  <span>Health</span>
                  <span>{battleState.monster_health}/{battleState.monster.max_health}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className="bg-red-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${getHealthPercentage(battleState.monster_health, battleState.monster.max_health)}%` }}
                  ></div>
                </div>
              </div>

              {/* Monster Stats */}
              <div className="grid grid-cols-2 gap-2 text-sm text-gray-300">
                <div className="flex items-center">
                  <SwordIcon className="w-4 h-4 mr-1 text-red-400" />
                  <span>{battleState.monster.attack}</span>
                </div>
                <div className="flex items-center">
                  <ShieldCheckIcon className="w-4 h-4 mr-1 text-blue-400" />
                  <span>{battleState.monster.defense}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Battle Log */}
          <div className="card">
            <h3 className="text-xl font-bold mb-4 text-white">Battle Log</h3>
            <div className="bg-gray-900/50 rounded-lg p-4 h-40 overflow-y-auto">
              {battleLog.map((log, index) => (
                <p key={index} className="text-sm text-gray-300 mb-1">
                  {log}
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <GameBackground variant="battle">
      <div className="p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 text-white">⚔️ Battle Arena</h1>
          <p className="text-purple-300 text-lg">Choose your opponent and prove your strength!</p>
        </div>

        {/* Monster Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {monsters.map((monster) => (
            <div key={monster.id} className="card hover:border-purple-500/50 transition-colors">
              <div className="text-center mb-4">
                <div className="w-20 h-20 mx-auto mb-4">
                  <img
                    src={getRandomBoss()}
                    alt={monster.name}
                    className="w-full h-full character-image battle-character object-cover"
                  />
                </div>
                <h3 className="text-xl font-bold mb-2 text-white">{monster.name}</h3>
                <p className={`${getRankColor(monster.rank)} font-semibold mb-1`}>
                  Rank {monster.rank}
                </p>
                <p className="text-gray-400">Level {monster.level}</p>
              </div>

              {/* Monster Stats */}
              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div className="flex items-center justify-center bg-gray-700/50 rounded-lg p-2">
                  <HeartIcon className="w-4 h-4 mr-1 text-green-400" />
                  <span className="text-gray-300">{monster.health} HP</span>
                </div>
                <div className="flex items-center justify-center bg-gray-700/50 rounded-lg p-2">
                  <SwordIcon className="w-4 h-4 mr-1 text-red-400" />
                  <span className="text-gray-300">{monster.attack} ATK</span>
                </div>
              </div>

              {/* Rewards */}
              <div className="bg-gray-700/30 rounded-lg p-3 mb-4">
                <p className="text-xs text-gray-400 mb-1">Rewards:</p>
                <div className="flex justify-between text-sm">
                  <span className="text-blue-400">{monster.experience_reward} EXP</span>
                  <span className="text-yellow-400">{monster.gold_reward} Gold</span>
                </div>
              </div>

              {/* Battle Button */}
              <button
                onClick={() => startBattle(monster.id)}
                disabled={loading}
                className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition-colors text-white"
              >
                {loading ? 'Starting...' : 'Challenge'}
              </button>
            </div>
          ))}
        </div>

        {monsters.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">Loading monsters...</p>
          </div>
        )}
        </div>
      </div>
    </GameBackground>
  );
};

export default BattlePage;