import { Moon, Sun, Bell, LogOut, BarChart3 } from 'lucide-react';
import useStore from '../store/useStore';
import { motion } from 'framer-motion';
import ThemeSelector from './ThemeSelector';
import useThemeColors from '../hooks/useThemeColors';

const Header = () => {
  const { theme, toggleTheme, user, logout } = useStore();
  const colors = useThemeColors();

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

        {/* Right Section */}
        <div className="flex items-center gap-2">
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
