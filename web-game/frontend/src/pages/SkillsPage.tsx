import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  SparklesIcon,
  BoltIcon,
  FireIcon,
  BeakerIcon,
  StarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';

interface Skill {
  id: string;
  name: string;
  description: string;
  type: string;
  element: string;
  cost: number;
  prerequisites: string[];
  effects: { [key: string]: any };
  cooldown: number;
  charges: number;
}

interface PlayerSkill {
  level: number;
  charges: number;
  max_charges: number;
  cooldown_end: number;
}

interface SkillsData {
  learned_skills: { [key: string]: PlayerSkill };
  skill_points: number;
  available_skills: Skill[];
}

const SkillsPage: React.FC = () => {
  const { user } = useAuth();
  const [skillsData, setSkillsData] = useState<SkillsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'learned' | 'available'>('learned');

  useEffect(() => {
    if (user) {
      loadSkillsData();
    }
  }, [user]);

  const loadSkillsData = async () => {
    try {
      const response = await apiService.get('/skills/player');
      setSkillsData(response.data);
    } catch (error) {
      console.error('Failed to load skills:', error);
      toast.error('Failed to load skills data');
    } finally {
      setLoading(false);
    }
  };

  const learnSkill = async (skillId: string) => {
    try {
      await apiService.post('/skills/learn', { skill_id: skillId });
      toast.success('Skill learned successfully!');
      loadSkillsData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to learn skill');
    }
  };

  const activateSkill = async (skillId: string) => {
    try {
      const response = await apiService.post(`/skills/use?skill_id=${skillId}`);
      toast.success(`Used ${response.data.message}`);
      loadSkillsData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to use skill');
    }
  };

  const getElementIcon = (element: string) => {
    switch (element.toLowerCase()) {
      case 'fire': return <FireIcon className="w-5 h-5 text-red-500" />;
      case 'water': case 'ice': return <BeakerIcon className="w-5 h-5 text-blue-500" />;
      case 'earth': return <SparklesIcon className="w-5 h-5 text-green-500" />;
      case 'wind': return <BoltIcon className="w-5 h-5 text-yellow-500" />;
      case 'light': return <StarIcon className="w-5 h-5 text-yellow-300" />;
      case 'dark': return <SparklesIcon className="w-5 h-5 text-purple-500" />;
      default: return <SparklesIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'basic': return 'text-green-400';
      case 'qte': return 'text-blue-400';
      case 'ultimate': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const canLearnSkill = (skill: Skill) => {
    if (!skillsData) return false;
    if (skillsData.skill_points < skill.cost) return false;
    if (skill.id in skillsData.learned_skills) return false;

    // Check prerequisites
    const prerequisites = skill.prerequisites || [];
    for (const prereq of prerequisites) {
      if (!(prereq in skillsData.learned_skills)) return false;
    }

    return true;
  };

  const isSkillOnCooldown = (skillId: string) => {
    if (!skillsData?.learned_skills[skillId]) return false;
    const currentTime = Math.floor(Date.now() / 1000);
    return currentTime < skillsData.learned_skills[skillId].cooldown_end;
  };

  const getCooldownRemaining = (skillId: string) => {
    if (!skillsData?.learned_skills[skillId]) return 0;
    const currentTime = Math.floor(Date.now() / 1000);
    return Math.max(0, skillsData.learned_skills[skillId].cooldown_end - currentTime);
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading skills...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  if (!skillsData) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 text-lg mb-4">Failed to load skills</p>
            <button onClick={loadSkillsData} className="btn-primary">
              Retry
            </button>
          </div>
        </div>
      </GameBackground>
    );
  }

  const learnedSkills = skillsData.available_skills.filter(skill => skill.id in skillsData.learned_skills);
  const availableSkills = skillsData.available_skills.filter(skill => !(skill.id in skillsData.learned_skills));

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 text-white">🔮 Skills & Abilities</h1>
            <p className="text-gray-400">Master powerful skills to become the ultimate hunter</p>
            <div className="mt-4 flex items-center justify-center space-x-4">
              <div className="bg-arise-purple/20 rounded-lg px-4 py-2">
                <span className="text-arise-purple font-bold text-lg">{skillsData.skill_points}</span>
                <span className="text-gray-300 ml-2">Skill Points</span>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8 space-x-2">
            <button
              onClick={() => setActiveTab('learned')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'learned'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              ✨ Learned Skills ({learnedSkills.length})
            </button>
            <button
              onClick={() => setActiveTab('available')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'available'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              📚 Available Skills ({availableSkills.length})
            </button>
          </div>

          {/* Skills Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {activeTab === 'learned' && learnedSkills.map((skill) => {
              const playerSkill = skillsData.learned_skills[skill.id];
              const onCooldown = isSkillOnCooldown(skill.id);
              const cooldownRemaining = getCooldownRemaining(skill.id);
              
              return (
                <div key={skill.id} className="card hover:border-arise-purple/50 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center">
                      {getElementIcon(skill.element)}
                      <h3 className="text-lg font-bold text-white ml-2">{skill.name}</h3>
                    </div>
                    <span className={`text-sm font-semibold ${getTypeColor(skill.type)}`}>
                      {skill.type}
                    </span>
                  </div>

                  <p className="text-gray-300 text-sm mb-4">{skill.description}</p>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Level:</span>
                      <span className="text-white">{playerSkill.level}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Charges:</span>
                      <span className="text-white">{playerSkill.charges}/{playerSkill.max_charges}</span>
                    </div>
                    {onCooldown && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Cooldown:</span>
                        <span className="text-red-400">{cooldownRemaining}s</span>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => activateSkill(skill.id)}
                    disabled={onCooldown || playerSkill.charges <= 0}
                    className={`w-full py-2 px-4 rounded-lg font-semibold transition-colors ${
                      onCooldown || playerSkill.charges <= 0
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-arise-purple hover:bg-arise-purple/80 text-white'
                    }`}
                  >
                    {onCooldown ? (
                      <div className="flex items-center justify-center">
                        <ClockIcon className="w-4 h-4 mr-2" />
                        On Cooldown
                      </div>
                    ) : playerSkill.charges <= 0 ? (
                      <div className="flex items-center justify-center">
                        <XCircleIcon className="w-4 h-4 mr-2" />
                        No Charges
                      </div>
                    ) : (
                      <div className="flex items-center justify-center">
                        <BoltIcon className="w-4 h-4 mr-2" />
                        Use Skill
                      </div>
                    )}
                  </button>
                </div>
              );
            })}

            {activeTab === 'available' && availableSkills.map((skill) => {
              const canLearn = canLearnSkill(skill);
              
              return (
                <div key={skill.id} className="card hover:border-arise-purple/50 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center">
                      {getElementIcon(skill.element)}
                      <h3 className="text-lg font-bold text-white ml-2">{skill.name}</h3>
                    </div>
                    <span className={`text-sm font-semibold ${getTypeColor(skill.type)}`}>
                      {skill.type}
                    </span>
                  </div>

                  <p className="text-gray-300 text-sm mb-4">{skill.description}</p>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Cost:</span>
                      <span className="text-arise-purple font-bold">{skill.cost} SP</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Cooldown:</span>
                      <span className="text-white">{skill.cooldown}s</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Charges:</span>
                      <span className="text-white">{skill.charges}</span>
                    </div>
                    {(skill.prerequisites || []).length > 0 && (
                      <div className="text-sm">
                        <span className="text-gray-400">Prerequisites:</span>
                        <div className="mt-1">
                          {(skill.prerequisites || []).map((prereq) => (
                            <span
                              key={prereq}
                              className={`inline-block text-xs px-2 py-1 rounded mr-1 mb-1 ${
                                prereq in skillsData.learned_skills
                                  ? 'bg-green-600 text-white'
                                  : 'bg-red-600 text-white'
                              }`}
                            >
                              {prereq}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => learnSkill(skill.id)}
                    disabled={!canLearn}
                    className={`w-full py-2 px-4 rounded-lg font-semibold transition-colors ${
                      canLearn
                        ? 'bg-arise-gold hover:bg-arise-gold/80 text-black'
                        : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {canLearn ? (
                      <div className="flex items-center justify-center">
                        <CheckCircleIcon className="w-4 h-4 mr-2" />
                        Learn Skill
                      </div>
                    ) : (
                      <div className="flex items-center justify-center">
                        <XCircleIcon className="w-4 h-4 mr-2" />
                        Cannot Learn
                      </div>
                    )}
                  </button>
                </div>
              );
            })}
          </div>

          {/* Empty State */}
          {((activeTab === 'learned' && learnedSkills.length === 0) ||
            (activeTab === 'available' && availableSkills.length === 0)) && (
            <div className="text-center py-12">
              <SparklesIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">
                {activeTab === 'learned' ? 'No Skills Learned' : 'No Skills Available'}
              </h3>
              <p className="text-gray-400">
                {activeTab === 'learned' 
                  ? 'Learn your first skill to begin your journey!'
                  : 'All skills have been learned!'}
              </p>
            </div>
          )}
        </div>
      </div>
    </GameBackground>
  );
};

export default SkillsPage;
