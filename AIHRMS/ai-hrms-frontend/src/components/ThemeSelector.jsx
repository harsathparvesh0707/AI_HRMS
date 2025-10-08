import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Palette, Check } from 'lucide-react';
import useStore from '../store/useStore';

const colorThemes = [
  {
    id: 'blue',
    name: 'Corporate Blue',
    description: 'Professional and trustworthy',
    colors: ['#3b82f6', '#06b6d4', '#0ea5e9'],
    gradient: 'from-blue-600 to-cyan-600',
  },
  {
    id: 'indigo',
    name: 'Executive Indigo',
    description: 'Modern and sophisticated',
    colors: ['#6366f1', '#8b5cf6', '#a855f7'],
    gradient: 'from-indigo-600 to-purple-600',
  },
  {
    id: 'green',
    name: 'Growth Green',
    description: 'Fresh and innovative',
    colors: ['#10b981', '#14b8a6', '#22c55e'],
    gradient: 'from-emerald-600 to-teal-600',
  },
  {
    id: 'red',
    name: 'Dynamic Red',
    description: 'Bold and energetic',
    colors: ['#ef4444', '#f97316', '#dc2626'],
    gradient: 'from-red-600 to-orange-600',
  },
  {
    id: 'slate',
    name: 'Professional Slate',
    description: 'Clean and minimal',
    colors: ['#64748b', '#475569', '#334155'],
    gradient: 'from-slate-600 to-slate-700',
  },
  {
    id: 'orange',
    name: 'Creative Orange',
    description: 'Vibrant and inspiring',
    colors: ['#f97316', '#fb923c', '#f59e0b'],
    gradient: 'from-orange-600 to-amber-600',
  },
];

const ThemeSelector = () => {
  const { colorTheme, setColorTheme } = useStore();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        aria-label="Theme selector"
      >
        <Palette className="w-4 h-4 text-slate-600 dark:text-slate-400" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 z-50 overflow-hidden"
            >
              <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">
                  Theme Colors
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Choose your preferred color scheme
                </p>
              </div>

              <div className="p-3 max-h-96 overflow-y-auto">
                <div className="space-y-2">
                  {colorThemes.map((theme) => (
                    <motion.button
                      key={theme.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        setColorTheme(theme.id);
                        setIsOpen(false);
                      }}
                      className={`w-full p-3 rounded-lg border-2 transition-all text-left ${
                        colorTheme === theme.id
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-slate-900 dark:text-white">
                              {theme.name}
                            </span>
                            {colorTheme === theme.id && (
                              <Check className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            )}
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                            {theme.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-1.5">
                        {theme.colors.map((color, idx) => (
                          <div
                            key={idx}
                            className="w-8 h-8 rounded-md shadow-sm"
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ThemeSelector;
