import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  ShoppingBagIcon,
  CurrencyDollarIcon,
  SparklesIcon,
  TagIcon,
  ClockIcon,
  StarIcon,
  FireIcon,
  ShoppingCartIcon
} from '@heroicons/react/24/outline';
import GameBackground from '../components/GameBackground';

interface ShopItem {
  id: string;
  name: string;
  description: string;
  type: string;
  rarity: string;
  price: { [key: string]: number };
  stock: number;
  daily_limit: number;
  can_purchase: boolean;
  remaining_daily: number;
  purchased_today: number;
  requirements: { [key: string]: any };
}

interface DailyDeal {
  id: string;
  name: string;
  description: string;
  type: string;
  rarity: string;
  original_price: { [key: string]: number };
  discounted_price: { [key: string]: number };
  discount_percent: number;
  stock: number;
  daily_limit: number;
}

const MarketPage: React.FC = () => {
  const { user } = useAuth();
  const [shopItems, setShopItems] = useState<ShopItem[]>([]);
  const [dailyDeals, setDailyDeals] = useState<DailyDeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [activeTab, setActiveTab] = useState<'shop' | 'deals' | 'sell'>('shop');

  useEffect(() => {
    if (user) {
      loadMarketData();
    }
  }, [user]);

  const loadMarketData = async () => {
    try {
      const [shopResponse, dealsResponse] = await Promise.all([
        apiService.get('/market/shop'),
        apiService.get('/market/daily-deals')
      ]);
      
      setShopItems(shopResponse.data.items);
      setDailyDeals(dealsResponse.data.deals);
    } catch (error) {
      console.error('Failed to load market data:', error);
      toast.error('Failed to load market data');
    } finally {
      setLoading(false);
    }
  };

  const purchaseItem = async (itemId: string, quantity: number = 1) => {
    try {
      setPurchasing(true);
      const response = await apiService.post('/market/purchase', {
        item_id: itemId,
        quantity
      });
      
      toast.success(response.data.message);
      loadMarketData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Purchase failed');
    } finally {
      setPurchasing(false);
    }
  };

  const getRarityColor = (rarity: string) => {
    switch (rarity.toLowerCase()) {
      case 'legendary': return 'text-red-500 bg-red-500/20 border-red-500/50';
      case 'epic': return 'text-purple-500 bg-purple-500/20 border-purple-500/50';
      case 'rare': return 'text-blue-500 bg-blue-500/20 border-blue-500/50';
      case 'common': return 'text-green-500 bg-green-500/20 border-green-500/50';
      default: return 'text-gray-500 bg-gray-500/20 border-gray-500/50';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'weapon': return <SparklesIcon className="w-5 h-5 text-red-500" />;
      case 'consumable': return <FireIcon className="w-5 h-5 text-green-500" />;
      case 'material': return <StarIcon className="w-5 h-5 text-blue-500" />;
      default: return <ShoppingBagIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const renderPrice = (price: { [key: string]: number }) => {
    const currencyIcons: { [key: string]: string } = {
      gold: '🪙',
      diamonds: '💎',
      crystals: '💠',
      stones: '🪨'
    };

    return (
      <div className="flex flex-wrap gap-2">
        {Object.entries(price).map(([currency, amount]) => (
          <span key={currency} className="bg-arise-gold/20 text-arise-gold px-2 py-1 rounded text-sm font-semibold">
            {currencyIcons[currency] || '💰'} {amount.toLocaleString()}
          </span>
        ))}
      </div>
    );
  };

  const renderShopItem = (item: ShopItem, isDeal: boolean = false) => {
    const dealItem = isDeal ? item as any as DailyDeal : null;
    
    return (
      <div key={item.id} className={`card hover:border-arise-purple/50 transition-colors ${isDeal ? 'border-arise-gold/50' : ''}`}>
        {isDeal && (
          <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">
            -{dealItem?.discount_percent}%
          </div>
        )}
        
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center">
            {getTypeIcon(item.type)}
            <h3 className="text-lg font-bold text-white ml-2">{item.name}</h3>
          </div>
          <span className={`px-2 py-1 rounded text-sm font-bold border ${getRarityColor(item.rarity)}`}>
            {item.rarity}
          </span>
        </div>

        <p className="text-gray-300 text-sm mb-4">{item.description}</p>

        {/* Stock and Limits */}
        <div className="space-y-2 mb-4 text-sm">
          {item.stock > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-400">Stock:</span>
              <span className="text-white">{item.stock}</span>
            </div>
          )}
          {item.daily_limit > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-400">Daily Limit:</span>
              <span className="text-white">{item.remaining_daily}/{item.daily_limit}</span>
            </div>
          )}
          {item.purchased_today > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-400">Purchased Today:</span>
              <span className="text-arise-purple">{item.purchased_today}</span>
            </div>
          )}
        </div>

        {/* Price */}
        <div className="mb-4">
          <span className="text-gray-400 text-sm">Price:</span>
          <div className="mt-2">
            {isDeal && dealItem ? (
              <div>
                <div className="line-through text-gray-500 text-sm mb-1">
                  {renderPrice(dealItem.original_price)}
                </div>
                {renderPrice(dealItem.discounted_price)}
              </div>
            ) : (
              renderPrice(item.price)
            )}
          </div>
        </div>

        {/* Requirements */}
        {Object.keys(item.requirements).length > 0 && (
          <div className="mb-4">
            <span className="text-gray-400 text-sm">Requirements:</span>
            <div className="mt-1">
              {Object.entries(item.requirements).map(([req, value]) => (
                <span key={req} className="bg-gray-600 text-white px-2 py-1 rounded text-xs mr-2">
                  {req}: {value}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Purchase Button */}
        <button
          onClick={() => purchaseItem(item.id)}
          disabled={purchasing || !item.can_purchase}
          className={`w-full py-2 px-4 rounded-lg font-semibold transition-colors ${
            item.can_purchase
              ? 'bg-arise-purple hover:bg-arise-purple/80 text-white'
              : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          } disabled:opacity-50`}
        >
          {purchasing ? (
            'Purchasing...'
          ) : !item.can_purchase ? (
            item.remaining_daily <= 0 ? 'Daily Limit Reached' : 'Cannot Purchase'
          ) : (
            <div className="flex items-center justify-center">
              <ShoppingCartIcon className="w-4 h-4 mr-2" />
              Purchase
            </div>
          )}
        </button>
      </div>
    );
  };

  if (loading) {
    return (
      <GameBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-white">Loading market...</p>
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
            <h1 className="text-4xl font-bold mb-4 text-white">🛒 Market & Shop</h1>
            <p className="text-gray-400">Purchase items, weapons, and consumables</p>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8 space-x-2">
            <button
              onClick={() => setActiveTab('shop')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'shop'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🏪 Shop ({shopItems.length})
            </button>
            <button
              onClick={() => setActiveTab('deals')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'deals'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🔥 Daily Deals ({dailyDeals.length})
            </button>
            <button
              onClick={() => setActiveTab('sell')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'sell'
                  ? 'bg-arise-purple text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              💰 Sell Items
            </button>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'shop' && (
              <div className="space-y-6">
                {shopItems.length === 0 ? (
                  <div className="text-center py-12">
                    <ShoppingBagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">Shop Unavailable</h3>
                    <p className="text-gray-400">The shop is currently being restocked!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {shopItems.map((item) => renderShopItem(item, false))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'deals' && (
              <div className="space-y-6">
                <div className="card bg-gradient-to-r from-arise-gold/20 to-red-500/20 border-arise-gold/50">
                  <h2 className="text-2xl font-bold text-white mb-4 flex items-center">
                    <TagIcon className="w-6 h-6 mr-2 text-arise-gold" />
                    Daily Deals
                    <ClockIcon className="w-5 h-5 ml-2 text-gray-400" />
                  </h2>
                  <p className="text-gray-300 mb-4">
                    Special discounted items that rotate daily! Don't miss out on these limited-time offers.
                  </p>
                </div>

                {dailyDeals.length === 0 ? (
                  <div className="text-center py-12">
                    <TagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No Deals Today</h3>
                    <p className="text-gray-400">Check back tomorrow for new daily deals!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {dailyDeals.map((deal) => renderShopItem(deal as any, true))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'sell' && (
              <div className="card">
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                  <CurrencyDollarIcon className="w-6 h-6 mr-2 text-arise-gold" />
                  Sell Items
                </h2>
                
                <div className="text-center py-12">
                  <CurrencyDollarIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">Item Selling Coming Soon</h3>
                  <p className="text-gray-400">
                    Sell your unwanted items for gold and resources!
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </GameBackground>
  );
};

export default MarketPage;
