import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  ArrowsRightLeftIcon,
  PlusIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  UserIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';

interface Trade {
  id: string;
  creator_id: string;
  creator_username: string;
  target_player_id?: string;
  target_username?: string;
  offered_items: { [key: string]: number };
  offered_hunters: string[];
  offered_gold: number;
  requested_items: { [key: string]: number };
  requested_hunters: string[];
  requested_gold: number;
  status: string;
  created_at: number;
  expires_at: number;
}

const TradingPage: React.FC = () => {
  const { user } = useAuth();
  const [availableTrades, setAvailableTrades] = useState<Trade[]>([]);
  const [myTrades, setMyTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'browse' | 'my-trades' | 'create'>('browse');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (user) {
      loadTrades();
    }
  }, [user]);

  const loadTrades = async () => {
    try {
      const [availableResponse, myTradesResponse] = await Promise.all([
        apiService.get('/trading/offers'),
        apiService.get('/trading/my-trades')
      ]);
      
      setAvailableTrades(availableResponse.data.trades);
      setMyTrades(myTradesResponse.data.trades);
    } catch (error) {
      console.error('Failed to load trades:', error);
      toast.error('Failed to load trading data');
    } finally {
      setLoading(false);
    }
  };

  const respondToTrade = async (tradeId: string, accept: boolean) => {
    try {
      setActionLoading(true);
      const response = await apiService.post('/trading/respond', {
        trade_id: tradeId,
        accept
      });
      
      toast.success(response.data.message);
      loadTrades();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to respond to trade');
    } finally {
      setActionLoading(false);
    }
  };

  const cancelTrade = async (tradeId: string) => {
    try {
      setActionLoading(true);
      const response = await apiService.post(`/trading/cancel/${tradeId}`);
      toast.success(response.data.message);
      loadTrades();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to cancel trade');
    } finally {
      setActionLoading(false);
    }
  };

  const formatTimeRemaining = (expiresAt: number) => {
    const now = Math.floor(Date.now() / 1000);
    const remaining = expiresAt - now;
    
    if (remaining <= 0) return 'Expired';
    
    const hours = Math.floor(remaining / 3600);
    const minutes = Math.floor((remaining % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-400';
      case 'accepted': return 'text-green-400';
      case 'rejected': return 'text-red-400';
      case 'cancelled': return 'text-gray-400';
      case 'expired': return 'text-gray-500';
      default: return 'text-gray-400';
    }
  };

  const renderTradeCard = (trade: Trade, isMyTrade: boolean = false) => (
    <div key={trade.id} className="card hover:border-arise-purple/50 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center">
            <UserIcon className="w-5 h-5 mr-2 text-arise-purple" />
            {trade.creator_username}
          </h3>
          {trade.target_username && (
            <p className="text-sm text-gray-400">→ {trade.target_username}</p>
          )}
        </div>
        <div className="text-right">
          <span className={`text-sm font-semibold ${getStatusColor(trade.status)}`}>
            {trade.status.toUpperCase()}
          </span>
          <div className="text-xs text-gray-400 flex items-center mt-1">
            <ClockIcon className="w-3 h-3 mr-1" />
            {formatTimeRemaining(trade.expires_at)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Offering */}
        <div className="bg-green-600/20 rounded-lg p-3">
          <h4 className="text-green-400 font-semibold text-sm mb-2">💰 Offering</h4>
          <div className="space-y-1 text-sm">
            {trade.offered_gold > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-300">Gold:</span>
                <span className="text-arise-gold">{trade.offered_gold.toLocaleString()}</span>
              </div>
            )}
            {Object.entries(trade.offered_items).map(([item, quantity]) => (
              <div key={item} className="flex justify-between">
                <span className="text-gray-300">{item}:</span>
                <span className="text-white">{quantity}</span>
              </div>
            ))}
            {trade.offered_hunters.map((hunter) => (
              <div key={hunter} className="flex justify-between">
                <span className="text-gray-300">Hunter:</span>
                <span className="text-blue-400">{hunter}</span>
              </div>
            ))}
            {trade.offered_gold === 0 && Object.keys(trade.offered_items).length === 0 && trade.offered_hunters.length === 0 && (
              <span className="text-gray-500 text-xs">Nothing offered</span>
            )}
          </div>
        </div>

        {/* Requesting */}
        <div className="bg-red-600/20 rounded-lg p-3">
          <h4 className="text-red-400 font-semibold text-sm mb-2">🎯 Requesting</h4>
          <div className="space-y-1 text-sm">
            {trade.requested_gold > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-300">Gold:</span>
                <span className="text-arise-gold">{trade.requested_gold.toLocaleString()}</span>
              </div>
            )}
            {Object.entries(trade.requested_items).map(([item, quantity]) => (
              <div key={item} className="flex justify-between">
                <span className="text-gray-300">{item}:</span>
                <span className="text-white">{quantity}</span>
              </div>
            ))}
            {trade.requested_hunters.map((hunter) => (
              <div key={hunter} className="flex justify-between">
                <span className="text-gray-300">Hunter:</span>
                <span className="text-blue-400">{hunter}</span>
              </div>
            ))}
            {trade.requested_gold === 0 && Object.keys(trade.requested_items).length === 0 && trade.requested_hunters.length === 0 && (
              <span className="text-gray-500 text-xs">Nothing requested</span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        {!isMyTrade && trade.status === 'pending' && (
          <>
            <button
              onClick={() => respondToTrade(trade.id, true)}
              disabled={actionLoading}
              className="flex-1 btn-primary disabled:opacity-50"
            >
              <CheckCircleIcon className="w-4 h-4 mr-2" />
              Accept
            </button>
            <button
              onClick={() => respondToTrade(trade.id, false)}
              disabled={actionLoading}
              className="flex-1 btn-secondary bg-red-600 hover:bg-red-700 disabled:opacity-50"
            >
              <XCircleIcon className="w-4 h-4 mr-2" />
              Reject
            </button>
          </>
        )}
        
        {isMyTrade && trade.status === 'pending' && (
          <button
            onClick={() => cancelTrade(trade.id)}
            disabled={actionLoading}
            className="w-full btn-secondary bg-gray-600 hover:bg-gray-700 disabled:opacity-50"
          >
            <XCircleIcon className="w-4 h-4 mr-2" />
            Cancel Trade
          </button>
        )}

        {trade.status !== 'pending' && (
          <div className="w-full text-center py-2">
            <span className={`font-semibold ${getStatusColor(trade.status)}`}>
              Trade {trade.status}
            </span>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading trades...</p>
          </div>
        </div>
      </GameBackground>
    );
  }

  return (
    <GameBackground>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 text-white">🔄 Trading Hub</h1>
            <p className="text-gray-400">Trade items, hunters, and gold with other players</p>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8 space-x-2">
            <button
              onClick={() => setActiveTab('browse')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'browse'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🛒 Browse Trades ({availableTrades.length})
            </button>
            <button
              onClick={() => setActiveTab('my-trades')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'my-trades'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              📋 My Trades ({myTrades.length})
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'create'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              ➕ Create Trade
            </button>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'browse' && (
              <div className="space-y-6">
                {availableTrades.length === 0 ? (
                  <div className="text-center py-12">
                    <ArrowsRightLeftIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No Trades Available</h3>
                    <p className="text-gray-400">Be the first to create a trade offer!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {availableTrades.map((trade) => renderTradeCard(trade, false))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'my-trades' && (
              <div className="space-y-6">
                {myTrades.length === 0 ? (
                  <div className="text-center py-12">
                    <ArrowsRightLeftIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No Active Trades</h3>
                    <p className="text-gray-400">Create your first trade to get started!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {myTrades.map((trade) => renderTradeCard(trade, true))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'create' && (
              <div className="max-w-2xl mx-auto">
                <div className="card">
                  <h2 className="text-2xl font-bold text-white mb-6 text-center">Create New Trade</h2>
                  <div className="text-center py-8">
                    <PlusIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">Trade Creation Coming Soon</h3>
                    <p className="text-gray-400">
                      Advanced trade creation interface will be available soon!
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default TradingPage;
