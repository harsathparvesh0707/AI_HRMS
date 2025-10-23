import { Moon, Sun, Bell, LogOut, BarChart3, Search } from 'lucide-react';
import { useState } from 'react';
import useStore from '../store/useStore';
import { motion } from 'framer-motion';
import ThemeSelector from './ThemeSelector';
import useThemeColors from '../hooks/useThemeColors';

const Header = () => {
  const { theme, toggleTheme, user, logout, searchAndShowTable, isGenerating } = useStore();
  const colors = useThemeColors();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    try {
      await searchAndShowTable(searchQuery);
      setSearchQuery('');
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
      <div className="flex items-center justify-between px-6 py-2.5">
        {/* Logo and Title */}
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 bg-gradient-to-br ${colors.gradient} rounded-lg flex items-center justify-center`}>
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 dark:text-white">
              AI HRMS
            </h1>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">
              Enterprise Edition
            </p>
          </div>
        </div>

        {/* Global Search */}
        <div className="flex-1 max-w-md mx-8">
          <form onSubmit={handleSearch} className="relative">
            <div className={`relative transition-all duration-200 ${
              isSearchFocused ? 'transform scale-105' : ''
            }`}>
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                placeholder="Search employees, departments, or ask AI..."
                disabled={isGenerating}
                className={`w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm placeholder-slate-400 transition-all ${
                  isGenerating ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              />
              {isGenerating && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                </div>
              )}
            </div>
          </form>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'light' ? (
              <Moon className="w-4 h-4 text-slate-600 dark:text-slate-400" />
            ) : (
              <Sun className="w-4 h-4 text-slate-600 dark:text-slate-400" />
            )}
          </button>

          {/* Theme Color Selector */}
          <ThemeSelector />

          {/* Notifications */}
          <button
            className="relative p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4 text-slate-600 dark:text-slate-400" />
            <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 bg-red-500 rounded-full"></span>
          </button>

          {/* User Profile */}
          <div className="flex items-center gap-2 pl-2 ml-2 border-l border-slate-200 dark:border-slate-700">
            <div className="text-right">
              <p className="text-xs font-medium text-slate-900 dark:text-white">
                {user?.name || 'User'}
              </p>
              <p className="text-[10px] text-slate-500 dark:text-slate-400">
                {user?.role || 'Role'}
              </p>
            </div>
            <img
              src={user?.avatar}
              alt={user?.name}
              className="w-7 h-7 rounded-full border border-slate-200 dark:border-slate-700"
            />
          </div>

          {/* Logout */}
          <button
            onClick={logout}
            className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors ml-1"
            aria-label="Logout"
          >
            <LogOut className="w-4 h-4 text-red-600 dark:text-red-400" />
          </button>
        </div>
      </div>
    </header>
  );
};   

export default Header;
