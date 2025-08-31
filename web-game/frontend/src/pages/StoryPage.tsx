import React, { useState, useEffect } from 'react';
import { 
  BookOpenIcon, 
  PlayIcon,
  CheckCircleIcon,
  LockClosedIcon,
  StarIcon,
  GiftIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

interface StoryChapter {
  id: number;
  chapter_number: number;
  title: string;
  description: string;
  required_level: number;
  required_rank: string;
  experience_reward: number;
  gold_reward: number;
  item_rewards: any[];
  story_text: string;
  choices: any[];
  completed: boolean;
  unlocked: boolean;
}

interface StoryProgress {
  current_chapter: number;
  completed_chapters: number[];
  total_experience: number;
  total_gold: number;
}

const StoryPage: React.FC = () => {
  const { user } = useAuth();
  const [chapters, setChapters] = useState<StoryChapter[]>([]);
  const [progress, setProgress] = useState<StoryProgress | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<StoryChapter | null>(null);
  const [showStoryModal, setShowStoryModal] = useState(false);
  const [currentStoryText, setCurrentStoryText] = useState('');
  const [storyChoices, setStoryChoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStoryData();
  }, []);

  const loadStoryData = async () => {
    try {
      const [chaptersResponse, progressResponse] = await Promise.all([
        api.get('/api/story/chapters'),
        api.get('/api/story/progress')
      ]);
      
      setChapters(chaptersResponse.data.chapters);
      setProgress(progressResponse.data);
    } catch (error) {
      console.error('Failed to load story data:', error);
      
      // Mock data for demo
      const mockChapters: StoryChapter[] = [
        {
          id: 1,
          chapter_number: 1,
          title: "The Weakest Hunter",
          description: "Sung Jin-Woo's first dungeon raid as an E-rank hunter",
          required_level: 1,
          required_rank: "E",
          experience_reward: 100,
          gold_reward: 200,
          item_rewards: [{ name: "Basic Dagger", rarity: "common" }],
          story_text: "You are Sung Jin-Woo, known as the weakest hunter in the world. Despite your E-rank status, you continue to enter dungeons to support your family. Today, you join a raid team for what seems like a routine dungeon...",
          choices: [
            { id: 1, text: "Stay close to the team", consequence: "safe" },
            { id: 2, text: "Scout ahead", consequence: "brave" }
          ],
          completed: false,
          unlocked: true
        },
        {
          id: 2,
          chapter_number: 2,
          title: "The Double Dungeon",
          description: "A mysterious second dungeon appears within the first",
          required_level: 3,
          required_rank: "E",
          experience_reward: 150,
          gold_reward: 300,
          item_rewards: [{ name: "System Key", rarity: "legendary" }],
          story_text: "The raid takes an unexpected turn when a hidden door reveals a second dungeon. Ancient statues line the walls, and an ominous feeling fills the air. This is no ordinary dungeon...",
          choices: [
            { id: 1, text: "Warn the team to retreat", consequence: "cautious" },
            { id: 2, text: "Investigate the statues", consequence: "curious" }
          ],
          completed: false,
          unlocked: false
        },
        {
          id: 3,
          chapter_number: 3,
          title: "The System Awakens",
          description: "Jin-Woo receives the mysterious leveling system",
          required_level: 5,
          required_rank: "D",
          experience_reward: 200,
          gold_reward: 500,
          item_rewards: [{ name: "System Interface", rarity: "legendary" }],
          story_text: "After a near-death experience, you awaken to find strange messages floating before your eyes. A 'System' has chosen you as its player. This is the beginning of your transformation...",
          choices: [
            { id: 1, text: "Accept the System", consequence: "power" },
            { id: 2, text: "Try to ignore it", consequence: "denial" }
          ],
          completed: false,
          unlocked: false
        },
        {
          id: 4,
          chapter_number: 4,
          title: "First Level Up",
          description: "Jin-Woo completes his first system quest",
          required_level: 8,
          required_rank: "D",
          experience_reward: 250,
          gold_reward: 600,
          item_rewards: [{ name: "Enhanced Dagger", rarity: "rare" }],
          story_text: "The System gives you your first quest: complete 100 push-ups, 100 sit-ups, and run 10km. It seems impossible for someone as weak as you, but the promise of power drives you forward...",
          choices: [
            { id: 1, text: "Complete the training", consequence: "growth" },
            { id: 2, text: "Look for shortcuts", consequence: "lazy" }
          ],
          completed: false,
          unlocked: false
        },
        {
          id: 5,
          chapter_number: 5,
          title: "The Shadow Extraction",
          description: "Jin-Woo discovers his unique shadow extraction ability",
          required_level: 12,
          required_rank: "C",
          experience_reward: 300,
          gold_reward: 800,
          item_rewards: [{ name: "Shadow Soldier", rarity: "epic" }],
          story_text: "During a dungeon raid, you witness the death of a powerful monster. Suddenly, the System presents you with a new option: 'Extract Shadow'. This ability will change everything...",
          choices: [
            { id: 1, text: "Extract the shadow", consequence: "shadow_army" },
            { id: 2, text: "Leave it alone", consequence: "missed_opportunity" }
          ],
          completed: false,
          unlocked: false
        }
      ];

      // Determine which chapters are unlocked based on mock player level
      const playerLevel = 10; // Mock player level
      mockChapters.forEach(chapter => {
        chapter.unlocked = playerLevel >= chapter.required_level;
      });

      setChapters(mockChapters);
      setProgress({
        current_chapter: 1,
        completed_chapters: [],
        total_experience: 0,
        total_gold: 0
      });
    }
  };

  const startChapter = (chapter: StoryChapter) => {
    if (!chapter.unlocked) return;
    
    setSelectedChapter(chapter);
    setCurrentStoryText(chapter.story_text);
    setStoryChoices(chapter.choices);
    setShowStoryModal(true);
  };

  const makeChoice = async (choiceId: number) => {
    if (!selectedChapter) return;
    
    setLoading(true);
    
    try {
      const response = await api.post('/api/story/complete', {
        chapter_id: selectedChapter.id,
        choice_id: choiceId
      });
      
      // Update chapter as completed
      setChapters(prev => prev.map(ch => 
        ch.id === selectedChapter.id ? { ...ch, completed: true } : ch
      ));
      
      // Update progress
      if (progress) {
        setProgress({
          ...progress,
          completed_chapters: [...progress.completed_chapters, selectedChapter.id],
          total_experience: progress.total_experience + selectedChapter.experience_reward,
          total_gold: progress.total_gold + selectedChapter.gold_reward
        });
      }
      
      setShowStoryModal(false);
      
    } catch (error) {
      console.error('Failed to complete chapter:', error);
      
      // Mock completion for demo
      setChapters(prev => prev.map(ch => {
        if (ch.id === selectedChapter.id) {
          return { ...ch, completed: true };
        }
        // Unlock next chapter
        if (ch.chapter_number === selectedChapter.chapter_number + 1) {
          return { ...ch, unlocked: true };
        }
        return ch;
      }));
      
      if (progress) {
        setProgress({
          ...progress,
          completed_chapters: [...progress.completed_chapters, selectedChapter.id],
          total_experience: progress.total_experience + selectedChapter.experience_reward,
          total_gold: progress.total_gold + selectedChapter.gold_reward
        });
      }
      
      setShowStoryModal(false);
    }
    
    setLoading(false);
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

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 text-white">📖 Story Campaign</h1>
          <p className="text-purple-300 text-lg">Follow Sung Jin-Woo's journey from E-rank to Shadow Monarch!</p>
        </div>

        {/* Progress Summary */}
        {progress && (
          <div className="card mb-8">
            <h3 className="text-xl font-bold mb-4 text-white">Campaign Progress</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-700/30 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-400">{progress.completed_chapters.length}</div>
                <div className="text-sm text-gray-400">Chapters Completed</div>
              </div>
              <div className="bg-gray-700/30 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-green-400">{progress.total_experience.toLocaleString()}</div>
                <div className="text-sm text-gray-400">Total EXP Earned</div>
              </div>
              <div className="bg-gray-700/30 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-yellow-400">{progress.total_gold.toLocaleString()}</div>
                <div className="text-sm text-gray-400">Total Gold Earned</div>
              </div>
            </div>
          </div>
        )}

        {/* Chapter List */}
        <div className="space-y-4">
          {chapters.map((chapter) => (
            <div 
              key={chapter.id} 
              className={`card ${
                chapter.completed ? 'border-green-500/30 bg-green-900/10' :
                chapter.unlocked ? 'border-purple-500/30 hover:border-purple-400/50' :
                'border-gray-600/30 bg-gray-800/50'
              } transition-colors`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {/* Chapter Status Icon */}
                  <div className="flex-shrink-0">
                    {chapter.completed ? (
                      <CheckCircleIcon className="w-12 h-12 text-green-400" />
                    ) : chapter.unlocked ? (
                      <PlayIcon className="w-12 h-12 text-purple-400" />
                    ) : (
                      <LockClosedIcon className="w-12 h-12 text-gray-500" />
                    )}
                  </div>

                  {/* Chapter Info */}
                  <div className="flex-grow">
                    <div className="flex items-center space-x-2 mb-1">
                      <h3 className="text-xl font-bold text-white">
                        Chapter {chapter.chapter_number}: {chapter.title}
                      </h3>
                      {chapter.completed && (
                        <StarIcon className="w-5 h-5 text-yellow-400" />
                      )}
                    </div>
                    <p className="text-gray-300 mb-2">{chapter.description}</p>
                    
                    {/* Requirements */}
                    <div className="flex items-center space-x-4 text-sm">
                      <span className="text-gray-400">
                        Level {chapter.required_level}+
                      </span>
                      <span className={`${getRankColor(chapter.required_rank)} font-semibold`}>
                        Rank {chapter.required_rank}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Rewards & Action */}
                <div className="flex items-center space-x-6">
                  {/* Rewards */}
                  <div className="text-right text-sm">
                    <div className="text-blue-400">{chapter.experience_reward} EXP</div>
                    <div className="text-yellow-400">{chapter.gold_reward} Gold</div>
                    {chapter.item_rewards.length > 0 && (
                      <div className="text-purple-400 flex items-center justify-end">
                        <GiftIcon className="w-4 h-4 mr-1" />
                        {chapter.item_rewards.length} Items
                      </div>
                    )}
                  </div>

                  {/* Action Button */}
                  <button
                    onClick={() => startChapter(chapter)}
                    disabled={!chapter.unlocked}
                    className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                      chapter.completed 
                        ? 'bg-green-600 hover:bg-green-700 text-white'
                        : chapter.unlocked
                        ? 'bg-purple-600 hover:bg-purple-700 text-white'
                        : 'bg-gray-600 cursor-not-allowed text-gray-400'
                    }`}
                  >
                    {chapter.completed ? 'Replay' : chapter.unlocked ? 'Start' : 'Locked'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Story Modal */}
        {showStoryModal && selectedChapter && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
            <div className="card max-w-4xl w-full max-h-[80vh] overflow-y-auto">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-white mb-2">
                  Chapter {selectedChapter.chapter_number}: {selectedChapter.title}
                </h2>
                <div className="w-full h-1 bg-gray-700 rounded-full">
                  <div className="h-1 bg-purple-500 rounded-full" style={{ width: '100%' }}></div>
                </div>
              </div>

              {/* Story Text */}
              <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
                <BookOpenIcon className="w-8 h-8 text-purple-400 mb-4" />
                <p className="text-gray-300 leading-relaxed text-lg">
                  {currentStoryText}
                </p>
              </div>

              {/* Choices */}
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-white mb-4">Choose your action:</h3>
                {storyChoices.map((choice) => (
                  <button
                    key={choice.id}
                    onClick={() => makeChoice(choice.id)}
                    disabled={loading}
                    className="w-full bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 p-4 rounded-lg text-left transition-colors text-white"
                  >
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center mr-3 text-sm font-bold">
                        {choice.id}
                      </div>
                      <span>{choice.text}</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Close Button */}
              <div className="mt-6 text-center">
                <button
                  onClick={() => setShowStoryModal(false)}
                  className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg transition-colors text-white"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StoryPage;