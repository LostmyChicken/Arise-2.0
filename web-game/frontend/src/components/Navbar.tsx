import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useSocket } from '../hooks/useSocket';
import {
  HomeIcon,
  UserIcon,
  GiftIcon,
  BuildingOfficeIcon,
  BookOpenIcon,
  ArchiveBoxIcon,
  TrophyIcon,
  Bars3Icon,
  XMarkIcon,
  SignalIcon,
  SignalSlashIcon,
  SparklesIcon,
  FireIcon,
  MapIcon,
  ArrowUpIcon,
  ArrowsRightLeftIcon,
  CalendarDaysIcon,
  ShoppingBagIcon
} from '@heroicons/react/24/outline';

// SwordIcon doesn't exist in heroicons, using a different icon
const SwordIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuth();
  const { connected } = useSocket();
  const location = useLocation();

  const navigation = [
    // Core
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, category: 'core' },
    { name: 'Profile', href: '/profile', icon: UserIcon, category: 'core' },

    // Combat
    { name: 'Battle', href: '/battle', icon: SwordIcon, category: 'combat' },
    { name: 'World Boss', href: '/worldboss', icon: FireIcon, category: 'combat' },
    { name: 'Arena', href: '/arena', icon: TrophyIcon, category: 'combat' },
    { name: 'Gates', href: '/gates', icon: MapIcon, category: 'combat' },

    // Progression
    { name: 'Story', href: '/story', icon: BookOpenIcon, category: 'progression' },
    { name: 'Skills', href: '/skills', icon: SparklesIcon, category: 'progression' },
    { name: 'Upgrade', href: '/upgrade', icon: ArrowUpIcon, category: 'progression' },
    { name: 'Daily', href: '/daily', icon: CalendarDaysIcon, category: 'progression' },

    // Social & Economy
    { name: 'Guild', href: '/guild', icon: BuildingOfficeIcon, category: 'social' },
    { name: 'Trading', href: '/trading', icon: ArrowsRightLeftIcon, category: 'social' },
    { name: 'Market', href: '/market', icon: ShoppingBagIcon, category: 'social' },

    // Collection
    { name: 'Gacha', href: '/gacha', icon: GiftIcon, category: 'collection' },
    { name: 'Inventory', href: '/inventory', icon: ArchiveBoxIcon, category: 'collection' },
    { name: 'Leaderboard', href: '/leaderboard', icon: TrophyIcon, category: 'collection' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-gray-900 bg-opacity-95 backdrop-blur-sm border-b border-gray-700 fixed w-full top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="text-2xl font-game font-black text-transparent bg-clip-text bg-gradient-to-r from-arise-purple to-arise-gold">
                ARISE
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden lg:block">
            <div className="ml-10 flex items-baseline space-x-2 overflow-x-auto scrollbar-thin max-w-4xl">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`px-2 py-2 rounded-md text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap ${
                      isActive(item.href)
                        ? 'bg-arise-purple text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    <Icon className="h-3 w-3" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* User Info & Connection Status */}
          <div className="hidden md:flex items-center space-x-4">
            {/* Connection Status */}
            <div className="flex items-center space-x-1">
              {connected ? (
                <SignalIcon className="h-4 w-4 text-green-400" />
              ) : (
                <SignalSlashIcon className="h-4 w-4 text-red-400" />
              )}
              <span className={`text-xs ${connected ? 'text-green-400' : 'text-red-400'}`}>
                {connected ? 'Online' : 'Offline'}
              </span>
            </div>

            {/* User Info */}
            <div className="text-sm text-gray-300">
              Welcome, <span className="text-arise-gold font-semibold">{user?.username}</span>
            </div>

            {/* Logout Button */}
            <button
              onClick={logout}
              className="btn-secondary text-xs px-3 py-1"
            >
              Logout
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="lg:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
            >
              {isOpen ? (
                <XMarkIcon className="block h-6 w-6" />
              ) : (
                <Bars3Icon className="block h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isOpen && (
        <div className="lg:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-800 bg-opacity-95 max-h-96 overflow-y-auto scrollbar-thin">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsOpen(false)}
                  className={`block px-3 py-2 rounded-md text-base font-medium transition-all duration-200 flex items-center space-x-2 ${
                    isActive(item.href)
                      ? 'bg-arise-purple text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
            
            {/* Mobile User Info */}
            <div className="border-t border-gray-700 pt-4 pb-3">
              <div className="flex items-center px-3 space-x-2">
                {connected ? (
                  <SignalIcon className="h-4 w-4 text-green-400" />
                ) : (
                  <SignalSlashIcon className="h-4 w-4 text-red-400" />
                )}
                <span className={`text-xs ${connected ? 'text-green-400' : 'text-red-400'}`}>
                  {connected ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="px-3 py-2 text-sm text-gray-300">
                Welcome, <span className="text-arise-gold font-semibold">{user?.username}</span>
              </div>
              <button
                onClick={logout}
                className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white rounded-md transition-all duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;