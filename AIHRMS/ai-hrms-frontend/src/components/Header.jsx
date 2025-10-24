import { Moon, Sun, Bell, LogOut, BarChart3, Search, X, Clock, TrendingUp, Grid3X3, Home, FileUp } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import useStore from '../store/useStore';
import { motion, AnimatePresence } from 'framer-motion';
import ThemeSelector from './ThemeSelector';
import useThemeColors from '../hooks/useThemeColors';

const Header = ({ onNavigate, currentPage }) => {
  const { theme, toggleTheme, user, logout, searchAndShowTable, isGenerating, showDynamicUI, hideDynamicUI } = useStore();
  const colors = useThemeColors();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [recentSearches, setRecentSearches] = useState(['Active employees', 'Department wise count', 'Employee details']);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target) &&
          suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
        setIsSearchFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async (e, query = searchQuery) => {
    e?.preventDefault();
    const searchTerm = query.trim();
    if (!searchTerm) return;
    
    try {
      await searchAndShowTable(searchTerm);
      
      // Add to recent searches if not already present
      if (!recentSearches.includes(searchTerm)) {
        setRecentSearches(prev => [searchTerm, ...prev.slice(0, 4)]);
      }
      
      setSearchQuery('');
      setShowSuggestions(false);
      setIsSearchFocused(false);
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  const handleInputFocus = () => {
    setIsSearchFocused(true);
    setShowSuggestions(true);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    searchRef.current?.querySelector('input')?.focus();
  };

  const searchSuggestions = [
    { text: 'Show all active employees', icon: TrendingUp },
    { text: 'Department wise employee count', icon: BarChart3 },
    { text: 'Employee performance metrics', icon: TrendingUp },
    { text: 'Recent joiners this month', icon: Clock }
  ];

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
      <div className="flex items-center justify-between px-6 py-2.5">
        {/* Logo and Title */}
        <div className="flex items-center gap-4">
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
          
          {/* Navigation Tabs */}
          <nav className="flex items-center">
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 shadow-inner">
              <button
                onClick={() => {
                  hideDynamicUI();
                  onNavigate('dashboard');
                }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 relative overflow-hidden ${
                  currentPage === 'dashboard' 
                    ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-md transform scale-105'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-white/50 dark:hover:bg-slate-700/50'
                }`}
              >
                <motion.div
                  animate={{
                    rotate: currentPage === 'dashboard' ? 360 : 0,
                    scale: currentPage === 'dashboard' ? 1.1 : 1
                  }}
                  transition={{ duration: 0.3 }}
                >
                  <Home className="w-4 h-4" />
                </motion.div>
                <span className="relative">
                  Dashboard
                  {currentPage === 'dashboard' && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute -bottom-1 left-0 right-0 h-0.5 bg-blue-500 rounded-full"
                      initial={false}
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </span>
              </button>
              
              <button
                onClick={() => {
                  hideDynamicUI();
                  onNavigate('upload');
                }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 relative overflow-hidden ${
                  currentPage === 'upload' 
                    ? 'bg-white dark:bg-slate-700 text-blue-500 dark:text-blue-500 shadow-md transform scale-105'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-white/50 dark:hover:bg-slate-700/50'
                }`}
              >
                <motion.div
                  animate={{
                    y: currentPage === 'upload' ? [-2, 0, -2] : 0,
                    scale: currentPage === 'upload' ? 1.1 : 1
                  }}
                  transition={{ 
                    y: { repeat: currentPage === 'upload' ? Infinity : 0, duration: 1.5 },
                    scale: { duration: 0.3 }
                  }}
                >
                  <FileUp className="w-4 h-4" />
                </motion.div>
                <span className="relative">
                  Upload
                  {currentPage === 'upload' && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute -bottom-1 left-0 right-0 h-0.5 bg-blue-500 rounded-full"
                      initial={false}
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </span>
              </button>
            </div>
          </nav>
        </div>

        {/* Enhanced Global Search */}
        <div className="flex-1 max-w-lg mx-8 relative" ref={searchRef}>
          <form onSubmit={handleSearch} className="relative">
            <motion.div 
              className={`relative transition-all duration-300 ${
                isSearchFocused ? 'transform scale-[1.02]' : ''
              }`}
              animate={{
                boxShadow: isSearchFocused 
                  ? '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
                  : '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
              }}
              transition={{ duration: 0.2 }}
            >
              <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 transition-colors duration-200 ${
                isSearchFocused ? 'text-blue-500' : 'text-slate-400'
              }`} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={handleInputFocus}
                placeholder="Search employees, departments, or ask AI anything..."
                disabled={isGenerating}
                className={`w-full pl-12 pr-12 py-3 bg-white dark:bg-slate-800 border-2 transition-all duration-200 rounded-xl text-sm placeholder-slate-400 ${
                  isSearchFocused 
                    ? 'border-blue-500 dark:border-blue-400 bg-white dark:bg-slate-800' 
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                } ${
                  isGenerating ? 'opacity-50 cursor-not-allowed' : ''
                } focus:outline-none focus:ring-0`}
              />
              
              {/* Clear button */}
              {searchQuery && !isGenerating && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  type="button"
                  onClick={handleClearSearch}
                  className="absolute right-10 top-1/2 transform -translate-y-1/2 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <X className="w-4 h-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300" />
                </motion.button>
              )}
              
              {/* Loading spinner */}
              {isGenerating && (
                <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full"
                  />
                </div>
              )}
            </motion.div>
          </form>

          {/* Search Suggestions Dropdown */}
          <AnimatePresence>
            {showSuggestions && !isGenerating && (
              <motion.div
                ref={suggestionsRef}
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden"
              >
                {/* Recent Searches */}
                {recentSearches.length > 0 && (
                  <div className="p-3 border-b border-slate-100 dark:border-slate-700">
                    <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                      <Clock className="w-3 h-3" />
                      Recent Searches
                    </h4>
                    <div className="space-y-1">
                      {recentSearches.map((search, index) => (
                        <button
                          key={index}
                          onClick={(e) => handleSearch(e, search)}
                          className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg transition-colors flex items-center gap-2"
                        >
                          <Search className="w-3 h-3 text-slate-400" />
                          {search}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Quick Suggestions */}
                <div className="p-3">
                  <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                    Quick Actions
                  </h4>
                  <div className="space-y-1">
                    {searchSuggestions.map((suggestion, index) => {
                      const IconComponent = suggestion.icon;
                      return (
                        <button
                          key={index}
                          onClick={(e) => handleSearch(e, suggestion.text)}
                          className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors flex items-center gap-3 group"
                        >
                          <IconComponent className="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-colors" />
                          <span className="group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                            {suggestion.text}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
                
                {/* Dashboard Link in Suggestions */}
                <div className="p-3 border-t border-slate-100 dark:border-slate-700">
                  <button
                    onClick={() => {
                      hideDynamicUI();
                      onNavigate('dashboard');
                      setShowSuggestions(false);
                      setIsSearchFocused(false);
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors flex items-center gap-3 group"
                  >
                    <Home className="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-colors" />
                    <span className="group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      Go to Dashboard
                    </span>
                  </button>
                </div>
                
                {/* Search Tips */}
                <div className="px-3 py-2 bg-slate-50 dark:bg-slate-700/50 border-t border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    💡 Try asking: "Show me employees in Freepool" or "Show me employees in VVDN_ICEE"
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
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
