#!/usr/bin/env python3
"""
Enhanced Solo Leveling Web Game Frontend
Complete game interface with all systems
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
from pathlib import Path

class EnhancedGameHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/workspace/arise-fixed/web-game/frontend/public", **kwargs)
    
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        elif self.path == '/':
            self.serve_complete_game()
        elif self.path.startswith('/images/'):
            self.serve_image()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def serve_complete_game(self):
        """Serve the complete game interface"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solo Leveling - Arise</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        body { 
            background: linear-gradient(135deg, #0f0f23, #1a1a2e, #16213e); 
            font-family: 'Arial', sans-serif;
        }
        .glow { box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
        .glow-purple { box-shadow: 0 0 20px rgba(147, 51, 234, 0.5); }
        .glow-red { box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }
        .glow-green { box-shadow: 0 0 20px rgba(34, 197, 94, 0.5); }
        .glow-yellow { box-shadow: 0 0 20px rgba(234, 179, 8, 0.5); }
        .card { 
            background: rgba(17, 24, 39, 0.8); 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .legendary { border-color: #fbbf24; background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.1)); }
        .epic { border-color: #a855f7; background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(147, 51, 234, 0.1)); }
        .rare { border-color: #3b82f6; background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1)); }
        .common { border-color: #6b7280; background: linear-gradient(135deg, rgba(107, 114, 128, 0.1), rgba(75, 85, 99, 0.1)); }
    </style>
</head>
<body class="min-h-screen text-white" x-data="gameData()">
    
    <!-- Navigation -->
    <nav class="bg-gray-900 border-b border-blue-500 p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold text-blue-400">Solo Leveling - Arise</h1>
            <div class="flex space-x-4">
                <button @click="currentTab = 'dashboard'" :class="currentTab === 'dashboard' ? 'text-blue-400' : 'text-gray-400'" class="hover:text-blue-300">Dashboard</button>
                <button @click="currentTab = 'battle'" :class="currentTab === 'battle' ? 'text-red-400' : 'text-gray-400'" class="hover:text-red-300">Battle</button>
                <button @click="currentTab = 'gacha'" :class="currentTab === 'gacha' ? 'text-purple-400' : 'text-gray-400'" class="hover:text-purple-300">Gacha</button>
                <button @click="currentTab = 'inventory'" :class="currentTab === 'inventory' ? 'text-green-400' : 'text-gray-400'" class="hover:text-green-300">Inventory</button>
                <button @click="currentTab = 'skills'" :class="currentTab === 'skills' ? 'text-yellow-400' : 'text-gray-400'" class="hover:text-yellow-300">Skills</button>
                <button @click="currentTab = 'market'" :class="currentTab === 'market' ? 'text-cyan-400' : 'text-gray-400'" class="hover:text-cyan-300">Market</button>
                <button @click="currentTab = 'guild'" :class="currentTab === 'guild' ? 'text-indigo-400' : 'text-gray-400'" class="hover:text-indigo-300">Guild</button>
            </div>
        </div>
    </nav>

    <!-- Player Status Bar -->
    <div class="bg-gray-800 border-b border-gray-700 p-3">
        <div class="container mx-auto flex justify-between items-center text-sm">
            <div class="flex space-x-6">
                <span class="text-blue-400">Level: <span x-text="player.level"></span></span>
                <span class="text-green-400">HP: <span x-text="player.hp + '/' + player.max_hp"></span></span>
                <span class="text-purple-400">MP: <span x-text="player.mp + '/' + player.max_mp"></span></span>
                <span class="text-yellow-400">Gold: <span x-text="player.gold.toLocaleString()"></span></span>
            </div>
            <div class="text-orange-400">
                Rank: <span x-text="player.rank"></span>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="container mx-auto p-6">
        
        <!-- Dashboard Tab -->
        <div x-show="currentTab === 'dashboard'" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div class="card p-6 rounded-lg glow">
                    <h3 class="text-xl font-bold mb-4 text-blue-400">Player Stats</h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between"><span>Attack:</span><span x-text="player.attack"></span></div>
                        <div class="flex justify-between"><span>Defense:</span><span x-text="player.defense"></span></div>
                        <div class="flex justify-between"><span>Agility:</span><span x-text="player.agility"></span></div>
                        <div class="flex justify-between"><span>Intelligence:</span><span x-text="player.intelligence"></span></div>
                    </div>
                </div>
                
                <div class="card p-6 rounded-lg glow-green">
                    <h3 class="text-xl font-bold mb-4 text-green-400">Daily Quests</h3>
                    <div class="space-y-2" x-show="dailyQuests.length > 0">
                        <template x-for="quest in dailyQuests.slice(0, 3)">
                            <div class="flex justify-between text-sm">
                                <span x-text="quest.name"></span>
                                <span x-text="quest.progress + '/' + quest.target" :class="quest.completed ? 'text-green-400' : 'text-yellow-400'"></span>
                            </div>
                        </template>
                    </div>
                </div>
                
                <div class="card p-6 rounded-lg glow-purple">
                    <h3 class="text-xl font-bold mb-4 text-purple-400">Recent Activity</h3>
                    <div class="space-y-2 text-sm">
                        <div class="text-green-400">✅ Defeated Iron Knight</div>
                        <div class="text-blue-400">📈 Reached Level 25</div>
                        <div class="text-purple-400">🎰 Summoned Legendary Hunter</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Battle Tab -->
        <div x-show="currentTab === 'battle'" class="space-y-6">
            <h2 class="text-3xl font-bold text-red-400 mb-6">⚔️ Battle Arena</h2>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="card p-6 rounded-lg glow-red">
                    <h3 class="text-xl font-bold mb-4 text-red-400">Available Monsters</h3>
                    <div class="space-y-3" x-show="monsters.length > 0">
                        <template x-for="monster in monsters.slice(0, 5)">
                            <div class="flex justify-between items-center p-3 bg-gray-700 rounded">
                                <div>
                                    <div class="font-bold" x-text="monster.name"></div>
                                    <div class="text-sm text-gray-400">Level <span x-text="monster.level"></span> • <span x-text="monster.element"></span></div>
                                </div>
                                <button @click="startBattle(monster)" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-sm">
                                    Battle
                                </button>
                            </div>
                        </template>
                    </div>
                </div>
                
                <div class="card p-6 rounded-lg glow">
                    <h3 class="text-xl font-bold mb-4 text-blue-400">Battle Results</h3>
                    <div x-show="battleResult" class="space-y-3">
                        <div class="text-green-400" x-text="battleResult"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gacha Tab -->
        <div x-show="currentTab === 'gacha'" class="space-y-6">
            <h2 class="text-3xl font-bold text-purple-400 mb-6">🎰 Hunter Summoning</h2>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="card p-6 rounded-lg glow-purple">
                    <h3 class="text-xl font-bold mb-4 text-purple-400">Summon Hunters</h3>
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <button @click="pullGacha('single')" class="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded font-bold">
                                Single Pull<br><span class="text-sm">1,000 Gold</span>
                            </button>
                            <button @click="pullGacha('multi')" class="bg-purple-700 hover:bg-purple-800 px-6 py-3 rounded font-bold">
                                10x Pull<br><span class="text-sm">9,000 Gold</span>
                            </button>
                        </div>
                        <div class="text-sm text-gray-400">
                            <div>Legendary: 3% • Epic: 12% • Rare: 25% • Common: 60%</div>
                        </div>
                    </div>
                </div>
                
                <div class="card p-6 rounded-lg glow">
                    <h3 class="text-xl font-bold mb-4 text-blue-400">Recent Summons</h3>
                    <div x-show="gachaResults.length > 0" class="space-y-2">
                        <template x-for="result in gachaResults">
                            <div class="p-2 rounded" :class="getRarityClass(result.rarity)">
                                <span x-text="result.name"></span> - <span x-text="result.rarity"></span>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <!-- Inventory Tab -->
        <div x-show="currentTab === 'inventory'" class="space-y-6">
            <h2 class="text-3xl font-bold text-green-400 mb-6">🎒 Inventory</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                <template x-for="item in inventory">
                    <div class="card p-4 rounded-lg" :class="getRarityClass(item.rarity)">
                        <div class="font-bold" x-text="item.name"></div>
                        <div class="text-sm text-gray-400 mb-2" x-text="item.type + ' • ' + item.rarity"></div>
                        <div class="text-xs mb-3" x-text="item.description"></div>
                        <div class="flex justify-between items-center">
                            <span class="text-sm">Qty: <span x-text="item.quantity"></span></span>
                            <button @click="useItem(item)" class="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs">
                                <span x-text="item.type === 'consumable' ? 'Use' : 'Equip'"></span>
                            </button>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <!-- Skills Tab -->
        <div x-show="currentTab === 'skills'" class="space-y-6">
            <h2 class="text-3xl font-bold text-yellow-400 mb-6">🔮 Skills & Abilities</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <template x-for="skill in skills">
                    <div class="card p-6 rounded-lg glow-yellow">
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h3 class="text-xl font-bold text-yellow-400" x-text="skill.name"></h3>
                                <div class="text-sm text-gray-400" x-text="skill.type + ' • Level ' + skill.level + '/' + skill.max_level"></div>
                            </div>
                            <div class="text-right text-sm">
                                <div class="text-blue-400">MP: <span x-text="skill.mp_cost"></span></div>
                                <div class="text-red-400">CD: <span x-text="skill.cooldown"></span>s</div>
                            </div>
                        </div>
                        <p class="text-sm mb-4" x-text="skill.description"></p>
                        <div class="flex space-x-2">
                            <button @click="upgradeSkill(skill)" class="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded text-sm">
                                Upgrade
                            </button>
                            <button @click="useSkill(skill)" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-sm">
                                Use
                            </button>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <!-- Market Tab -->
        <div x-show="currentTab === 'market'" class="space-y-6">
            <h2 class="text-3xl font-bold text-cyan-400 mb-6">🏪 Market</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <template x-for="item in marketItems">
                    <div class="card p-6 rounded-lg glow-cyan">
                        <div class="font-bold text-cyan-400" x-text="item.name"></div>
                        <div class="text-sm text-gray-400 mb-2" x-text="item.type + ' • ' + item.rarity"></div>
                        <div class="text-xs mb-3" x-text="item.description"></div>
                        <div class="text-yellow-400 font-bold mb-3" x-text="item.price.toLocaleString() + ' Gold'"></div>
                        <div class="text-xs text-gray-500 mb-4">Seller: <span x-text="item.seller"></span></div>
                        <button @click="buyItem(item)" class="w-full bg-cyan-600 hover:bg-cyan-700 px-4 py-2 rounded">
                            Buy Item
                        </button>
                    </div>
                </template>
            </div>
        </div>

        <!-- Guild Tab -->
        <div x-show="currentTab === 'guild'" class="space-y-6">
            <h2 class="text-3xl font-bold text-indigo-400 mb-6">🏰 Guild</h2>
            
            <div class="card p-6 rounded-lg glow">
                <h3 class="text-xl font-bold mb-4 text-indigo-400">Shadow Legion</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-bold mb-2">Guild Info</h4>
                        <div class="space-y-1 text-sm">
                            <div>Level: 15</div>
                            <div>Members: 47/50</div>
                            <div>Guild Master: Shadow Monarch</div>
                            <div>Founded: 2024-01-15</div>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-bold mb-2">Guild Benefits</h4>
                        <div class="space-y-1 text-sm text-green-400">
                            <div>+15% XP Bonus</div>
                            <div>+10% Gold Bonus</div>
                            <div>Guild Shop Access</div>
                            <div>Raid Dungeons</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <script>
        function gameData() {
            return {
                currentTab: 'dashboard',
                player: {
                    level: 25,
                    hp: 2500,
                    max_hp: 2500,
                    mp: 1200,
                    max_mp: 1200,
                    attack: 850,
                    defense: 650,
                    agility: 720,
                    intelligence: 580,
                    gold: 125000,
                    rank: 'S-Rank'
                },
                monsters: [],
                skills: [],
                inventory: [],
                marketItems: [],
                dailyQuests: [],
                gachaResults: [],
                battleResult: '',

                async init() {
                    await this.loadAllData();
                },

                async loadAllData() {
                    try {
                        // Load monsters
                        const monstersRes = await fetch('/api/battle/monsters');
                        const monstersData = await monstersRes.json();
                        this.monsters = monstersData.monsters || [];

                        // Load skills
                        const skillsRes = await fetch('/api/skills/list');
                        const skillsData = await skillsRes.json();
                        this.skills = skillsData.skills || [];

                        // Load inventory
                        const invRes = await fetch('/api/inventory/items');
                        const invData = await invRes.json();
                        this.inventory = invData.inventory || [];

                        // Load market
                        const marketRes = await fetch('/api/market/items');
                        const marketData = await marketRes.json();
                        this.marketItems = marketData.items || [];

                        // Load daily quests
                        const dailyRes = await fetch('/api/daily/quests');
                        const dailyData = await dailyRes.json();
                        this.dailyQuests = dailyData.daily_quests || [];

                    } catch (error) {
                        console.error('Error loading data:', error);
                    }
                },

                async startBattle(monster) {
                    try {
                        const response = await fetch('/api/battle/start', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                battle_type: 'pve',
                                monster_id: monster.id,
                                difficulty: 'normal'
                            })
                        });
                        const result = await response.json();
                        this.battleResult = `Battle started against ${monster.name}! Battle ID: ${result.battle_id}`;
                    } catch (error) {
                        this.battleResult = 'Battle failed to start: ' + error.message;
                    }
                },

                async pullGacha(type) {
                    try {
                        const response = await fetch('/api/gacha/pull', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ pull_type: type })
                        });
                        const result = await response.json();
                        if (result.hunters) {
                            this.gachaResults = [...result.hunters, ...this.gachaResults].slice(0, 10);
                        }
                    } catch (error) {
                        console.error('Gacha pull failed:', error);
                    }
                },

                async useItem(item) {
                    try {
                        const endpoint = item.type === 'consumable' ? '/api/inventory/use' : '/api/inventory/equip';
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ item_id: item.id })
                        });
                        const result = await response.json();
                        if (result.success) {
                            await this.loadAllData(); // Refresh data
                        }
                    } catch (error) {
                        console.error('Item use failed:', error);
                    }
                },

                async upgradeSkill(skill) {
                    try {
                        const response = await fetch('/api/skills/upgrade', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ skill_id: skill.id })
                        });
                        const result = await response.json();
                        if (result.success) {
                            await this.loadAllData(); // Refresh data
                        }
                    } catch (error) {
                        console.error('Skill upgrade failed:', error);
                    }
                },

                async useSkill(skill) {
                    try {
                        const response = await fetch('/api/skills/use', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ skill_id: skill.id, target: 'enemy' })
                        });
                        const result = await response.json();
                        console.log('Skill used:', result);
                    } catch (error) {
                        console.error('Skill use failed:', error);
                    }
                },

                async buyItem(item) {
                    try {
                        const response = await fetch('/api/market/buy', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ item_id: item.id })
                        });
                        const result = await response.json();
                        if (result.success) {
                            this.player.gold = result.remaining_gold;
                            await this.loadAllData(); // Refresh data
                        }
                    } catch (error) {
                        console.error('Purchase failed:', error);
                    }
                },

                getRarityClass(rarity) {
                    const classes = {
                        'legendary': 'legendary',
                        'epic': 'epic', 
                        'rare': 'rare',
                        'common': 'common'
                    };
                    return classes[rarity] || 'common';
                }
            }
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_image(self):
        """Serve images from the images directory"""
        image_path = self.path[1:]  # Remove leading /
        full_path = f"/workspace/arise-fixed/web-game/frontend/public/{image_path}"
        
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                self.send_response(200)
                if full_path.endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                elif full_path.endswith('.jpg') or full_path.endswith('.jpeg'):
                    self.send_header('Content-type', 'image/jpeg')
                elif full_path.endswith('.webp'):
                    self.send_header('Content-type', 'image/webp')
                self.end_headers()
                self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def proxy_to_backend(self):
        """Proxy API calls to the backend server"""
        try:
            backend_url = f"http://localhost:56092{self.path}"
            
            if self.command == 'GET':
                with urllib.request.urlopen(backend_url) as response:
                    data = response.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(data)
            
            elif self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                req = urllib.request.Request(backend_url, data=post_data, method='POST')
                req.add_header('Content-Type', 'application/json')
                
                with urllib.request.urlopen(req) as response:
                    data = response.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(data)
                    
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({"error": str(e)})
            self.wfile.write(error_response.encode())

if __name__ == "__main__":
    PORT = 54156
    
    print(f"🎮 Solo Leveling - Complete Web Game")
    print(f"🌐 Game: http://localhost:{PORT}")
    print(f"🔧 Backend: http://localhost:56092")
    print("=" * 50)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), EnhancedGameHandler) as httpd:
        print(f"✅ Complete game running on port {PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Game stopped")
