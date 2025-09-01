import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '../services/api';

interface User {
  player_id: string;
  username: string;
  access_token: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth token on app start
    const token = localStorage.getItem('arise_token');
    const userData = localStorage.getItem('arise_user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser({ ...parsedUser, access_token: token });
        apiService.setAuthToken(token);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('arise_token');
        localStorage.removeItem('arise_user');
      }
    }
    
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await apiService.login(username, password);
      const userData = {
        player_id: response.player_id,
        username: response.username,
        access_token: response.access_token
      };
      
      setUser(userData);
      localStorage.setItem('arise_token', response.access_token);
      localStorage.setItem('arise_user', JSON.stringify({
        player_id: response.player_id,
        username: response.username
      }));
      
      apiService.setAuthToken(response.access_token);
    } catch (error) {
      throw error;
    }
  };

  const register = async (username: string, email: string, password: string) => {
    try {
      await apiService.register(username, email, password);
      // After successful registration, automatically log in
      await login(username, password);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('arise_token');
    localStorage.removeItem('arise_user');
    apiService.setAuthToken(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}