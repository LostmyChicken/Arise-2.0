import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:56092';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('arise_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          console.warn('🔐 Authentication failed:', error.response?.data?.detail || 'Token may be expired');

          // Only clear auth and redirect if we're not already on auth pages
          const currentPath = window.location.pathname;
          const isAuthPage = currentPath.includes('/login') || currentPath.includes('/register');

          if (!isAuthPage) {
            console.log('🔄 Clearing authentication and redirecting to login...');
            localStorage.removeItem('arise_token');
            localStorage.removeItem('arise_user');

            // Show a brief message before redirecting
            const message = document.createElement('div');
            message.style.cssText = `
              position: fixed; top: 20px; right: 20px; z-index: 9999;
              background: #ef4444; color: white; padding: 12px 20px;
              border-radius: 8px; font-family: system-ui;
            `;
            message.textContent = 'Session expired. Redirecting to login...';
            document.body.appendChild(message);

            setTimeout(() => {
              document.body.removeChild(message);
              window.location.href = '/login';
            }, 2000);
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setAuthToken(token: string | null) {
    if (token) {
      this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete this.api.defaults.headers.common['Authorization'];
    }
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const response = await this.api.post('/auth/login', { username, password });
    return response.data;
  }

  async register(username: string, email: string, password: string) {
    const response = await this.api.post('/auth/register', { username, email, password });
    return response.data;
  }

  async logout() {
    const response = await this.api.post('/auth/logout');
    return response.data;
  }

  // Player endpoints
  async getPlayerProfile(playerId: string) {
    const response = await this.api.get(`/player/profile/${playerId}`);
    return response.data;
  }

  async getPlayerStats(playerId: string) {
    const response = await this.api.get(`/player/stats/${playerId}`);
    return response.data;
  }

  async getPlayerInventory(playerId: string) {
    const response = await this.api.get(`/player/inventory/${playerId}`);
    return response.data;
  }

  async upgradeStat(playerId: string, stat: string, points: number) {
    const response = await this.api.post(`/player/upgrade-stat/${playerId}`, { stat, points });
    return response.data;
  }

  async equipItem(playerId: string, slot: string, itemId: string | null) {
    const response = await this.api.post(`/player/equip/${playerId}`, { slot, item_id: itemId });
    return response.data;
  }

  async getLeaderboard(limit: number = 10) {
    const response = await this.api.get(`/player/leaderboard?limit=${limit}`);
    return response.data;
  }

  // Battle endpoints
  async startBattle(playerId: string, battleType: string, opponentId?: string, difficulty?: string) {
    const response = await this.api.post(`/battle/start?player_id=${playerId}`, {
      battle_type: battleType,
      opponent_id: opponentId,
      difficulty: difficulty
    });
    return response.data;
  }

  async battleAction(playerId: string, battleId: string, actionType: string, skillId?: string) {
    const response = await this.api.post(`/battle/action?player_id=${playerId}`, {
      battle_id: battleId,
      action_type: actionType,
      skill_id: skillId
    });
    return response.data;
  }

  async getBattleState(battleId: string) {
    const response = await this.api.get(`/battle/state/${battleId}`);
    return response.data;
  }

  async getBattleHistory(playerId: string, limit: number = 10) {
    const response = await this.api.get(`/battle/history/${playerId}?limit=${limit}`);
    return response.data;
  }

  // Gacha endpoints
  async gachaPull(playerId: string, pullType: string, gachaType: string) {
    const response = await this.api.post(`/gacha/pull/${playerId}`, {
      pull_type: pullType,
      gacha_type: gachaType
    });
    return response.data;
  }

  async getGachaRates() {
    const response = await this.api.get('/gacha/rates');
    return response.data;
  }

  async getGachaHistory(playerId: string, limit: number = 20) {
    const response = await this.api.get(`/gacha/history/${playerId}?limit=${limit}`);
    return response.data;
  }

  // Guild endpoints
  async createGuild(playerId: string, name: string, description?: string) {
    const response = await this.api.post(`/guild/create/${playerId}`, { name, description });
    return response.data;
  }

  async getGuildInfo(guildId: string) {
    const response = await this.api.get(`/guild/info/${guildId}`);
    return response.data;
  }

  async joinGuild(playerId: string, guildId: string) {
    const response = await this.api.post(`/guild/join/${playerId}`, { guild_id: guildId });
    return response.data;
  }

  async leaveGuild(playerId: string) {
    const response = await this.api.post(`/guild/leave/${playerId}`);
    return response.data;
  }

  async listGuilds(limit: number = 20, offset: number = 0) {
    const response = await this.api.get(`/guild/list?limit=${limit}&offset=${offset}`);
    return response.data;
  }

  async getMyGuild(playerId: string) {
    const response = await this.api.get(`/guild/my-guild/${playerId}`);
    return response.data;
  }

  // Story endpoints
  async getStoryProgress(playerId: string) {
    const response = await this.api.get(`/story/progress/${playerId}`);
    return response.data;
  }

  async getStoryArcs() {
    const response = await this.api.get('/story/arcs');
    return response.data;
  }

  async startStoryMission(playerId: string, arc: number, mission: number) {
    const response = await this.api.post(`/story/start-mission/${playerId}`, { arc, mission });
    return response.data;
  }

  async completeStoryMission(playerId: string, arc: number, mission: number) {
    const response = await this.api.post(`/story/complete-mission/${playerId}`, { arc, mission });
    return response.data;
  }

  async getCurrentMission(playerId: string) {
    const response = await this.api.get(`/story/current-mission/${playerId}`);
    return response.data;
  }

  // Game data endpoints
  async getItems() {
    const response = await this.api.get('/game/items');
    return response.data;
  }

  async getHunters() {
    const response = await this.api.get('/game/hunters');
    return response.data;
  }

  async getEnemies() {
    const response = await this.api.get('/game/enemies');
    return response.data;
  }

  async getSkills() {
    const response = await this.api.get('/game/skills');
    return response.data;
  }

  async getEmojis() {
    const response = await this.api.get('/game/emojis');
    return response.data;
  }

  async getGameConfig() {
    const response = await this.api.get('/game/config');
    return response.data;
  }

  // Health check
  async healthCheck() {
    const response = await this.api.get('/health');
    return response.data;
  }

  // Direct HTTP methods for backward compatibility
  async get(url: string) {
    const response = await this.api.get(url);
    return response;
  }

  async post(url: string, data?: any) {
    const response = await this.api.post(url, data);
    return response;
  }

  async put(url: string, data?: any) {
    const response = await this.api.put(url, data);
    return response;
  }

  async delete(url: string) {
    const response = await this.api.delete(url);
    return response;
  }
}

export const apiService = new ApiService();
export default apiService;