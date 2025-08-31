import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './useAuth';

interface SocketContextType {
  socket: Socket | null;
  connected: boolean;
  joinRoom: (room: string) => void;
  leaveRoom: (room: string) => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export function SocketProvider({ children }: { children: ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      // Connect to Socket.IO server
      const newSocket = io(process.env.REACT_APP_API_URL || 'http://localhost:56092', {
        auth: {
          token: user.access_token,
          player_id: user.player_id
        }
      });

      newSocket.on('connect', () => {
        console.log('🔌 Connected to game server');
        setConnected(true);
      });

      newSocket.on('disconnect', () => {
        console.log('🔌 Disconnected from game server');
        setConnected(false);
      });

      newSocket.on('connected', (data) => {
        console.log('Welcome message:', data.message);
      });

      // Battle events
      newSocket.on('battle_update', (data) => {
        console.log('Battle update:', data);
        // Handle battle updates
        window.dispatchEvent(new CustomEvent('battle_update', { detail: data }));
      });

      // World boss events
      newSocket.on('world_boss_update', (data) => {
        console.log('World boss update:', data);
        // Handle world boss updates
        window.dispatchEvent(new CustomEvent('world_boss_update', { detail: data }));
      });

      // Guild events
      newSocket.on('guild_update', (data) => {
        console.log('Guild update:', data);
        // Handle guild updates
        window.dispatchEvent(new CustomEvent('guild_update', { detail: data }));
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
      };
    }
  }, [user]);

  const joinRoom = (room: string) => {
    if (socket) {
      socket.emit('join_room', { room });
    }
  };

  const leaveRoom = (room: string) => {
    if (socket) {
      socket.emit('leave_room', { room });
    }
  };

  const value = {
    socket,
    connected,
    joinRoom,
    leaveRoom
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  const context = useContext(SocketContext);
  if (context === undefined) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
}