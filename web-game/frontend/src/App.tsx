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

  return (
    <>
      {user && <Navbar />}
      <main className={user ? 'pt-16' : ''}>
        <Routes>
          {/* Public routes */}
          <Route 
            path="/login" 
            element={!user ? <LoginPage /> : <Navigate to="/dashboard" />} 
          />
          <Route 
            path="/register" 
            element={!user ? <RegisterPage /> : <Navigate to="/dashboard" />} 
          />
          
          {/* Protected routes */}
          <Route 
            path="/dashboard" 
            element={user ? (
              <SocketProvider>
                <DashboardPage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          <Route 
            path="/profile" 
            element={user ? (
              <SocketProvider>
                <ProfilePage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          <Route 
            path="/battle" 
            element={user ? (
              <SocketProvider>
                <BattlePage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          <Route 
            path="/gacha" 
            element={user ? (
              <SocketProvider>
                <GachaPage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          <Route 
            path="/guild" 
            element={user ? (
              <SocketProvider>
                <GuildPage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          <Route 
            path="/story" 
            element={user ? (
              <SocketProvider>
                <StoryPage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          <Route 
            path="/inventory" 
            element={user ? (
              <SocketProvider>
                <InventoryPage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          <Route 
            path="/leaderboard" 
            element={user ? (
              <SocketProvider>
                <LeaderboardPage />
              </SocketProvider>
            ) : <Navigate to="/login" />} 
          />
          
          {/* Default redirect */}
          <Route 
            path="/" 
            element={<Navigate to={user ? "/dashboard" : "/login"} />} 
          />
          <Route 
            path="*" 
            element={<Navigate to={user ? "/dashboard" : "/login"} />} 
          />
        </Routes>
      </main>
    </>
  );
}

export default App;