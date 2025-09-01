import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { SocketProvider } from './hooks/useSocket';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import BattlePage from './pages/BattlePage';
import GachaPage from './pages/GachaPage';
import GuildPage from './pages/GuildPage';
import StoryPage from './pages/StoryPage';
import InventoryPage from './pages/InventoryPage';
import LeaderboardPage from './pages/LeaderboardPage';
import SkillsPage from './pages/SkillsPage';
import WorldBossPage from './pages/WorldBossPage';
import GatesPage from './pages/GatesPage';
import UpgradePage from './pages/UpgradePage';
import TradingPage from './pages/TradingPage';
import ArenaPage from './pages/ArenaPage';
import DailyPage from './pages/DailyPage';
import MarketPage from './pages/MarketPage';

// Components
import Navbar from './components/Navbar';
import LoadingScreen from './components/LoadingScreen';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-game-bg bg-pattern">
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1F2937',
                color: '#F9FAFB',
                border: '1px solid #374151',
              },
            }}
          />
          <AppContent />
        </div>
      </Router>
    </AuthProvider>
  );
}

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return (
      <main>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<Navigate to="/login" />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </main>
    );
  }

  return (
    <SocketProvider>
      <Navbar />
      <main className="pt-16">
        <Routes>
          {/* Protected routes */}
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/battle" element={<BattlePage />} />
          <Route path="/gacha" element={<GachaPage />} />
          <Route path="/guild" element={<GuildPage />} />
          <Route path="/story" element={<StoryPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/worldboss" element={<WorldBossPage />} />
          <Route path="/gates" element={<GatesPage />} />
          <Route path="/upgrade" element={<UpgradePage />} />
          <Route path="/trading" element={<TradingPage />} />
          <Route path="/arena" element={<ArenaPage />} />
          <Route path="/daily" element={<DailyPage />} />
          <Route path="/market" element={<MarketPage />} />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </main>
    </SocketProvider>
  );
}

export default App;