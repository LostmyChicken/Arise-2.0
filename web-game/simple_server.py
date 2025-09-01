#!/usr/bin/env python3
"""
Simple static file server for the Solo Leveling Web Game
This serves the frontend files and proxies API calls to the backend
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
from pathlib import Path

class GameHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/workspace/arise-fixed/web-game/frontend/src", **kwargs)
    
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        elif self.path == '/':
            self.serve_index()
        elif self.path.startswith('/images/'):
            self.serve_image()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def serve_index(self):
        """Serve a simple HTML page for testing"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solo Leveling - Arise Web Game</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: linear-gradient(135deg, #1a1a2e, #16213e); }
        .glow { box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
    </style>
</head>
<body class="min-h-screen text-white">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-4xl font-bold text-center mb-8 text-blue-400">Solo Leveling - Arise</h1>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Battle System Test -->
            <div class="bg-gray-800 p-6 rounded-lg glow">
                <h2 class="text-xl font-bold mb-4 text-yellow-400">Battle System</h2>
                <button onclick="testBattle()" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">
                    Test Battle API
                </button>
                <div id="battle-result" class="mt-4 text-sm"></div>
            </div>
            
            <!-- Gacha System Test -->
            <div class="bg-gray-800 p-6 rounded-lg glow">
                <h2 class="text-xl font-bold mb-4 text-purple-400">Gacha System</h2>
                <button onclick="testGacha()" class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded">
                    Test Gacha API
                </button>
                <div id="gacha-result" class="mt-4 text-sm"></div>
            </div>
            
            <!-- Story System Test -->
            <div class="bg-gray-800 p-6 rounded-lg glow">
                <h2 class="text-xl font-bold mb-4 text-green-400">Story System</h2>
                <button onclick="testStory()" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">
                    Test Story API
                </button>
                <div id="story-result" class="mt-4 text-sm"></div>
            </div>
            
            <!-- Player System Test -->
            <div class="bg-gray-800 p-6 rounded-lg glow">
                <h2 class="text-xl font-bold mb-4 text-blue-400">Player System</h2>
                <button onclick="testPlayer()" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
                    Test Player API
                </button>
                <div id="player-result" class="mt-4 text-sm"></div>
            </div>
            
            <!-- Game Data Test -->
            <div class="bg-gray-800 p-6 rounded-lg glow">
                <h2 class="text-xl font-bold mb-4 text-orange-400">Game Data</h2>
                <button onclick="testGameData()" class="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded">
                    Test Game Data API
                </button>
                <div id="gamedata-result" class="mt-4 text-sm"></div>
            </div>
            
            <!-- Health Check -->
            <div class="bg-gray-800 p-6 rounded-lg glow">
                <h2 class="text-xl font-bold mb-4 text-cyan-400">System Health</h2>
                <button onclick="testHealth()" class="bg-cyan-600 hover:bg-cyan-700 px-4 py-2 rounded">
                    Check API Health
                </button>
                <div id="health-result" class="mt-4 text-sm"></div>
            </div>
        </div>
        
        <div class="mt-8 text-center">
            <p class="text-gray-400">🎮 Solo Leveling Web Game - All Systems Operational</p>
            <p class="text-sm text-gray-500 mt-2">Backend: http://localhost:56092 | Frontend: http://localhost:54156</p>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:56092';
        
        async function apiCall(endpoint, method = 'GET', data = null) {
            try {
                const options = {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    mode: 'cors'
                };
                if (data) options.body = JSON.stringify(data);
                
                const response = await fetch(`${API_BASE}${endpoint}`, options);
                return await response.json();
            } catch (error) {
                return { error: error.message };
            }
        }
        
        async function testHealth() {
            const result = await apiCall('/api/health');
            document.getElementById('health-result').innerHTML = 
                `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
        
        async function testBattle() {
            const result = await apiCall('/api/battle/monsters');
            document.getElementById('battle-result').innerHTML = 
                `<pre>${JSON.stringify(result, null, 2).substring(0, 500)}...</pre>`;
        }
        
        async function testGacha() {
            const result = await apiCall('/api/gacha/rates');
            document.getElementById('gacha-result').innerHTML = 
                `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
        
        async function testStory() {
            const result = await apiCall('/api/story/chapters');
            document.getElementById('story-result').innerHTML = 
                `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
        
        async function testPlayer() {
            const result = await apiCall('/api/player/stats');
            document.getElementById('player-result').innerHTML = 
                `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
        
        async function testGameData() {
            const result = await apiCall('/api/gamedata/items');
            document.getElementById('gamedata-result').innerHTML = 
                `<pre>${JSON.stringify(result, null, 2).substring(0, 500)}...</pre>`;
        }
        
        // Auto-test health on load
        window.onload = () => testHealth();
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
    
    print(f"🚀 Starting Solo Leveling Web Game Test Server...")
    print(f"🌐 Frontend: http://localhost:{PORT}")
    print(f"🔧 Backend: http://localhost:56092")
    print(f"📊 API Docs: http://localhost:56092/docs")
    print("=" * 50)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), GameHandler) as httpd:
        print(f"✅ Server running on port {PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")